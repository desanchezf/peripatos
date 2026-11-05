from django.contrib import admin

from .models import Choice, Question, Quiz


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "updated_at"]
    search_fields = ["title", "description"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "quiz", "order"]
    list_filter = ["quiz"]
    search_fields = ["text"]
    inlines = [ChoiceInline]
