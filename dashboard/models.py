from django.conf import settings
from django.db import models


class Notice(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "Información"
        WARNING = "warning", "Importante"

    title = models.CharField("título", max_length=200)
    body = models.TextField("texto", blank=True)
    level = models.CharField("nivel", max_length=20, choices=Level.choices, default=Level.INFO)
    active = models.BooleanField("activo", default=True)
    dismissed_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="+", editable=False)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "aviso"
        verbose_name_plural = "avisos"

    def __str__(self):
        return self.title
