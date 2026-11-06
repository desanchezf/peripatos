import json
from unittest.mock import patch

import httpx
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from .models import Conversation, LLMModel, Message
from .providers import ProviderError, stream_ollama
from .views import ConversationViewSet

LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


def events(response):
    body = b"".join(response.streaming_content).decode()
    return [json.loads(chunk[6:]) for chunk in body.split("\n\n") if chunk]


@override_settings(ANTHROPIC_API_KEY="", CACHES=LOCMEM)
class AssistantTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="clave-segura-1")
        self.other = get_user_model().objects.create_user("luis", password="clave-segura-2")
        LLMModel.objects.all().delete()
        self.local = LLMModel.objects.create(provider=LLMModel.Provider.OLLAMA, name="local:1b")
        self.claude = LLMModel.objects.create(provider=LLMModel.Provider.ANTHROPIC, name="claude-opus-5-5")
        self.conversation = Conversation.objects.create(user=self.user)
        self.url = f"/api/assistant/conversations/{self.conversation.pk}/chat/"
        self.client.force_login(self.user)

    def post(self, **data):
        return self.client.post(self.url, {"message": "Hola", "model": self.local.pk, **data}, format="json")

    def test_requires_session(self):
        self.client.logout()
        self.assertIn(self.client.get("/api/assistant/models/").status_code, (401, 403))
        self.assertIn(self.post().status_code, (401, 403))

    def test_claude_is_hidden_without_api_key(self):
        names = [m["name"] for m in self.client.get("/api/assistant/models/").data]
        self.assertEqual(names, ["local:1b"])
        with override_settings(ANTHROPIC_API_KEY="clave"):
            names = [m["name"] for m in self.client.get("/api/assistant/models/").data]
        self.assertEqual(names, ["claude-opus-5-5", "local:1b"])

    def test_inactive_model_is_rejected(self):
        self.local.is_active = False
        self.local.save()
        with patch("assistant.views.stream_chat") as stream:
            self.assertEqual(self.post().status_code, 400)
        stream.assert_not_called()

    def test_conversation_model_no_longer_available_is_rejected(self):
        self.conversation.model = self.claude
        self.conversation.save()
        self.assertEqual(self.client.post(self.url, {"message": "Hola"}, format="json").status_code, 400)

    def test_chat_streams_and_saves_both_messages(self):
        chunks = [
            {"type": "text", "text": "Buenos "},
            {"type": "text", "text": "días"},
            {"type": "usage", "input_tokens": 3, "output_tokens": 2},
        ]
        with patch("assistant.views.stream_chat", return_value=iter(chunks)) as stream:
            response = self.post()
            self.assertEqual(response["Content-Type"], "text/event-stream")
            received = events(response)
        self.assertEqual(received, [{"type": "text", "text": "Buenos "}, {"type": "text", "text": "días"}, {"type": "done"}])
        stream.assert_called_once_with(self.local, [{"role": "user", "content": "Hola"}])

        user, assistant = self.conversation.messages.all()
        self.assertEqual((user.role, user.content), ("user", "Hola"))
        self.assertEqual((assistant.role, assistant.content, assistant.model), ("assistant", "Buenos días", self.local))
        self.assertEqual(assistant.usage, {"input_tokens": 3, "output_tokens": 2})
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.title, "Hola")

    def test_history_is_sent_in_order(self):
        Message.objects.create(conversation=self.conversation, role="user", content="Uno")
        Message.objects.create(conversation=self.conversation, role="assistant", content="Dos")
        with patch("assistant.views.stream_chat", return_value=iter([])) as stream:
            events(self.post(message="Tres"))
        self.assertEqual([m["content"] for m in stream.call_args.args[1]], ["Uno", "Dos", "Tres"])

    def test_provider_error_reaches_the_client_and_keeps_partial_text(self):
        def failing(*args):
            yield {"type": "text", "text": "Parcial"}
            raise ProviderError("Sin conexión")

        with patch("assistant.views.stream_chat", side_effect=failing):
            received = events(self.post())
        self.assertEqual(received[1], {"type": "error", "message": "Sin conexión"})
        self.assertEqual(self.conversation.messages.last().content, "Parcial")

    def test_stopping_the_response_keeps_partial_text(self):
        def chunks(*args):
            yield {"type": "text", "text": "Parcial"}
            yield {"type": "text", "text": " y más"}

        with patch("assistant.views.stream_chat", side_effect=chunks):
            stream = ConversationViewSet().event_stream(self.conversation, self.local, [])
            next(stream)
            stream.close()
        self.assertEqual(self.conversation.messages.last().content, "Parcial")

    def test_ollama_down_is_a_provider_error(self):
        with patch("assistant.providers.ollama.Client") as client:
            client.return_value.chat.side_effect = httpx.ConnectError("sin red")
            with self.assertRaisesMessage(ProviderError, "perfil ollama"):
                list(stream_ollama("local:1b", []))

    def test_empty_message_is_rejected(self):
        self.assertEqual(self.post(message="").status_code, 400)

    def test_other_users_cannot_use_a_conversation(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f"/api/assistant/conversations/{self.conversation.pk}/").status_code, 404)
        self.assertEqual(self.post().status_code, 404)
        self.assertEqual(self.client.delete(f"/api/assistant/conversations/{self.conversation.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/api/assistant/conversations/").data["count"], 0)

    def test_create_and_delete_conversation(self):
        created = self.client.post("/api/assistant/conversations/", {"model": self.local.pk}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(Conversation.objects.get(pk=created.data["id"]).user, self.user)
        self.assertEqual(self.client.delete(f"/api/assistant/conversations/{created.data['id']}/").status_code, 204)

    def test_chat_is_throttled(self):
        rates = {"assistant": "1/min", "login": "10/min"}
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", rates), patch("assistant.views.stream_chat", return_value=iter([])):
            events(self.post())
            self.assertEqual(self.post().status_code, 429)
