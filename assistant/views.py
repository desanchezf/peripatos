import json

from django.http import StreamingHttpResponse
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from .models import Conversation, LLMModel, Message
from .providers import ProviderError, stream_chat
from .serializers import ChatSerializer, ConversationDetailSerializer, ConversationSerializer, LLMModelSerializer


def sse(event):
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


class LLMModelListView(generics.ListAPIView):
    serializer_class = LLMModelSerializer
    pagination_class = None

    def get_queryset(self):
        return LLMModel.objects.available()


class ConversationViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options"]
    # Solo limita las acciones que lo fijan: DRF exige que el atributo exista para aceptarlo en @action
    throttle_scope = None

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return ConversationDetailSerializer if self.action == "retrieve" else ConversationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # Cada mensaje cuesta dinero o CPU: límite por usuario (DEFAULT_THROTTLE_RATES)
    @action(detail=True, methods=["post"], throttle_scope="assistant")
    def chat(self, request, pk=None):
        """Envía un mensaje y devuelve la respuesta como Server-Sent Events."""
        conversation = self.get_object()
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        model = serializer.validated_data.get("model") or conversation.model
        # El de la conversación puede haberse desactivado desde que se usó
        if model is None or not LLMModel.objects.available().filter(pk=model.pk).exists():
            raise ValidationError({"model": "Elige un modelo disponible."})

        text = serializer.validated_data["message"]
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=text)
        conversation.model = model
        conversation.title = conversation.title or text[:60]
        conversation.save()

        history = [{"role": m.role, "content": m.content} for m in conversation.messages.all()]
        response = StreamingHttpResponse(self.event_stream(conversation, model, history), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # que nginx no acumule la respuesta
        return response

    def event_stream(self, conversation, model, history):
        text = []
        usage = {"input_tokens": 0, "output_tokens": 0}
        try:
            for event in stream_chat(model, history):
                if event["type"] == "usage":
                    for key in usage:
                        usage[key] += event[key]
                    continue
                text.append(event["text"])
                yield sse(event)
        except ProviderError as exc:
            yield sse({"type": "error", "message": str(exc)})
        finally:
            # Se guarda lo recibido aunque el usuario pare la respuesta
            if text:
                Message.objects.create(
                    conversation=conversation, role=Message.Role.ASSISTANT, content="".join(text), model=model, usage=usage
                )
        yield sse({"type": "done"})
