from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from peripatos.storage import private_storage

MAX_SOLUTION_SIZE = 25 * 1024 * 1024


def validate_solution_size(file):
    if file.size > MAX_SOLUTION_SIZE:
        raise ValidationError("La solución no puede superar los 25 MB.")


def solution_path(submission, filename):
    return f"labs/{submission.lab_id}/{submission.user_id}/{filename}"


class Lab(models.Model):
    title = models.CharField("título", max_length=200)
    statement = models.TextField("enunciado", blank=True, help_text="Markdown.")
    theory = models.TextField("teoría", blank=True, help_text="Markdown.")
    due_date = models.DateField("fecha límite", null=True, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "laboratorio"
        verbose_name_plural = "laboratorios"

    def __str__(self):
        return self.title


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Entregada"
        REVIEWED = "reviewed", "Revisada"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lab_submissions", verbose_name="usuario")
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="submissions", verbose_name="laboratorio")
    file = models.FileField("solución", storage=private_storage, upload_to=solution_path, max_length=255, validators=[validate_solution_size])
    comment = models.TextField("comentario", blank=True)
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    feedback = models.TextField("revisión", blank=True)
    submitted_at = models.DateTimeField("entregada", auto_now_add=True)
    reviewed_at = models.DateTimeField("revisada", null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "entrega"
        verbose_name_plural = "entregas"

    def __str__(self):
        return f"{self.lab} · {self.user}"
