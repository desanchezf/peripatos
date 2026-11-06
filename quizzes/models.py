from django.conf import settings
from django.db import models


class Topic(models.Model):
    name = models.CharField("nombre", max_length=120, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "tema"
        verbose_name_plural = "temas"

    def __str__(self):
        return self.name


class Quiz(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="quizzes", verbose_name="tema")
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "cuestionario"
        verbose_name_plural = "cuestionarios"

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="cuestionario")
    text = models.TextField("enunciado")
    explanation = models.TextField("explicación", blank=True, help_text="Se muestra al corregir.")
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["quiz", "order", "id"]
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices", verbose_name="pregunta")
    text = models.CharField("respuesta", max_length=500)
    is_correct = models.BooleanField("correcta", default=False)

    class Meta:
        ordering = ["id"]
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"

    def __str__(self):
        return self.text[:80]


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="cuestionario")
    score = models.PositiveIntegerField("aciertos")
    total = models.PositiveIntegerField("preguntas")
    submitted_at = models.DateTimeField("enviado", auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "intento"
        verbose_name_plural = "intentos"

    @property
    def percent(self):
        return round(100 * self.score / self.total) if self.total else 0


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, related_name="+")
