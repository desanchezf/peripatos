from rest_framework import serializers

from .models import Conversation, LLMModel, Message


class LLMModelSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = LLMModel
        fields = ["id", "provider", "name", "label"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "model", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    model = serializers.PrimaryKeyRelatedField(queryset=LLMModel.objects.available(), allow_null=True, required=False)

    class Meta:
        model = Conversation
        fields = ["id", "title", "model", "created_at", "updated_at"]
        read_only_fields = ["title"]


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = [*ConversationSerializer.Meta.fields, "messages"]


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=50000)
    model = serializers.PrimaryKeyRelatedField(queryset=LLMModel.objects.available(), required=False)
