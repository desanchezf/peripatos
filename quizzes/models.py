from django.db import models


class Quiz(models.Model):
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "test"
        verbose_name_plural = "tests"

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="test")
    text = models.TextField("enunciado")
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
