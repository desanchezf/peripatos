from rest_framework import serializers

from .models import Choice, Question, Quiz


class QuizListSerializer(serializers.ModelSerializer):
    topic = serializers.SerializerMethodField()
    question_count = serializers.IntegerField(read_only=True)
    attempt_count = serializers.SerializerMethodField()
    best_percent = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "topic", "question_count", "attempt_count", "best_percent"]

    def get_topic(self, obj):
        return {"id": obj.topic_id, "name": obj.topic.name, "description": obj.topic.description} if obj.topic else None

    def get_attempt_count(self, obj):
        return len(obj.user_attempts)

    def get_best_percent(self, obj):
        return max((attempt.percent for attempt in obj.user_attempts), default=None)


class ChoiceSerializer(serializers.ModelSerializer):
    """Sin `is_correct`: la solución no sale del servidor hasta corregir."""

    class Meta:
        model = Choice
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "choices"]


class QuizDetailSerializer(QuizListSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + ["questions"]


class SubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.IntegerField(), allow_empty=True)
