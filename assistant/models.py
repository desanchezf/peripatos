from django.conf import settings
from django.db import models


class LLMModelQuerySet(models.QuerySet):
    def available(self):
        """Lo que se puede usar ahora. Sin API key, los modelos de Claude solo darían error."""
        models = self.filter(is_active=True)
        if not settings.ANTHROPIC_API_KEY:
            models = models.exclude(provider=LLMModel.Provider.ANTHROPIC)
        return models


class LLMModel(models.Model):
    """Catálogo de modelos, gestionado desde el admin. El primero disponible es el predeterminado."""

    class Provider(models.TextChoices):
        ANTHROPIC = "anthropic", "Anthropic (Claude)"
        OLLAMA = "ollama", "Ollama (local)"

    provider = models.CharField("proveedor", max_length=20, choices=Provider)
    name = models.CharField("identificador", max_length=200, help_text="ID en el proveedor, p. ej. claude-opus-5-5 o qwen3:4b.")
    display_name = models.CharField("nombre visible", max_length=200, blank=True)
    position = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activo", default=True)

    objects = LLMModelQuerySet.as_manager()

    class Meta:
        ordering = ["position", "name"]
        verbose_name = "modelo"
        verbose_name_plural = "modelos"
        constraints = [models.UniqueConstraint(fields=["provider", "name"], name="unique_llm_model")]

    def __str__(self):
        return self.display_name or self.name


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations", verbose_name="usuario")
    model = models.ForeignKey(LLMModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations", verbose_name="modelo")
    title = models.CharField("título", max_length=200, blank=True)
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "conversación"
        verbose_name_plural = "conversaciones"

    def __str__(self):
        return self.title or f"Conversación {self.pk}"


class Message(models.Model):
    """Se guarda solo el texto, sin formato de proveedor: así se puede cambiar de modelo a mitad de conversación."""

    class Role(models.TextChoices):
        USER = "user", "Usuario"
        ASSISTANT = "assistant", "Asistente"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages", verbose_name="conversación")
    role = models.CharField("rol", max_length=20, choices=Role)
    content = models.TextField("contenido")
    model = models.ForeignKey(LLMModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="modelo")
    usage = models.JSONField("tokens", default=dict, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "mensaje"
        verbose_name_plural = "mensajes"

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"
