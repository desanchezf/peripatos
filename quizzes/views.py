from django.db import transaction
from django.db.models import Count, Prefetch
from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Attempt, AttemptAnswer, Choice, Question, Quiz
from .serializers import QuizDetailSerializer, QuizListSerializer, SubmitSerializer


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None

    def get_queryset(self):
        mine = Attempt.objects.filter(user=self.request.user)
        queryset = (
            Quiz.objects.select_related("topic")
            .annotate(question_count=Count("questions", distinct=True))
            .prefetch_related(Prefetch("attempts", queryset=mine, to_attr="user_attempts"))
        )
        if self.action != "list":
            questions = Question.objects.prefetch_related("choices")
            queryset = queryset.prefetch_related(Prefetch("questions", queryset=questions))
        return queryset

    def get_serializer_class(self):
        return QuizListSerializer if self.action == "list" else QuizDetailSerializer

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        payload = SubmitSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        questions = list(quiz.questions.all())
        if not questions:
            raise drf_serializers.ValidationError({"detail": "Este cuestionario no tiene preguntas."})
        answers = payload.validated_data["answers"]
        choices = Choice.objects.filter(question__quiz=quiz).in_bulk()

        results = []
        rows = []
        score = 0
        for question in questions:
            selected = answers.get(str(question.id))
            choice = choices.get(selected)
            if selected is not None and (choice is None or choice.question_id != question.id):
                raise drf_serializers.ValidationError({"detail": "Respuesta no válida."})
            correct = choice is not None and choice.is_correct
            score += correct
            rows.append(AttemptAnswer(question=question, choice=choice))
            results.append(
                {
                    "question": question.id,
                    "selected": selected,
                    "correct": correct,
                    "correct_choices": [c.id for c in question.choices.all() if c.is_correct],
                    "explanation": question.explanation,
                }
            )

        with transaction.atomic():
            attempt = Attempt.objects.create(user=request.user, quiz=quiz, score=score, total=len(questions))
            for row in rows:
                row.attempt = attempt
            AttemptAnswer.objects.bulk_create(rows)

        return Response({"score": score, "total": attempt.total, "percent": attempt.percent, "results": results})
