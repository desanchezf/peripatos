from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models

from peripatos.storage import private_storage


class Material(models.Model):
    class Kind(models.TextChoices):
        THEORY = "theory", "Teoría"
        READING = "reading", "Lectura"

    title = models.CharField("título", max_length=200)
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices, default=Kind.THEORY)
    content = models.TextField("contenido", blank=True, help_text="Markdown. Se muestra si no hay fichero.")
    file = models.FileField(
        "fichero",
        storage=private_storage,
        upload_to="materials/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "epub"])],
    )
    source_url = models.URLField("enlace", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "material"
        verbose_name_plural = "materiales"

    def __str__(self):
        return self.title

    @property
    def format(self):
        """pdf, epub o text"""
        return Path(self.file.name).suffix.lstrip(".").lower() if self.file else "text"


class ReadingProgress(models.Model):
    """Dónde va cada usuario. `location` es el número de página (PDF) o el CFI (EPUB)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_progress")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="progress")
    location = models.CharField(max_length=500, blank=True)
    percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "material"], name="unique_progress_per_user")]
        verbose_name = "progreso de lectura"
        verbose_name_plural = "progresos de lectura"


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="bookmarks")
    location = models.CharField(max_length=500)
    label = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "material", "location"], name="unique_bookmark_location")]
        verbose_name = "marcador"
        verbose_name_plural = "marcadores"


class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_notes")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="notes")
    location = models.CharField(max_length=500, blank=True)
    label = models.CharField(max_length=200, blank=True)
    quote = models.TextField(blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "nota"
        verbose_name_plural = "notas"
