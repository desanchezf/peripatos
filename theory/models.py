from django.db import models


class Material(models.Model):
    class Kind(models.TextChoices):
        THEORY = "theory", "Teoría"
        READING = "reading", "Lectura"

    title = models.CharField("título", max_length=200)
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices, default=Kind.THEORY)
    content = models.TextField("contenido", blank=True)
    source_url = models.URLField("enlace", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "material"
        verbose_name_plural = "materiales"

    def __str__(self):
        return self.title
