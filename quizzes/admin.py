from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from .models import Attempt, Choice, Question, Quiz, Topic


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["text", "order"]


class ChoiceFormSet(BaseInlineFormSet):
    """Una pregunta sin respuesta correcta sería imposible de acertar."""

    def clean(self):
        super().clean()
        kept = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get("DELETE")]
        if kept and not any(form.cleaned_data.get("is_correct") for form in kept):
            raise ValidationError("Marca al menos una respuesta como correcta.")


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceFormSet
    extra = 4


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "topic", "updated_at"]
    list_filter = ["topic"]
    search_fields = ["title", "description"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "quiz", "order"]
    list_filter = ["quiz"]
    search_fields = ["text"]
    inlines = [ChoiceInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ["quiz", "user", "score", "total", "submitted_at"]
    list_filter = ["quiz"]

    def has_add_permission(self, request):
        return False
