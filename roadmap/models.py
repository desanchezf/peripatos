from django.conf import settings
from django.db import models
from django.db.models import Q

from labs.models import Lab
from quizzes.models import Quiz
from theory.models import Material


class Training(models.Model):
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True)
    target_date = models.DateField("fecha objetivo", null=True, blank=True)
    order = models.PositiveIntegerField("orden", default=0)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "formación"
        verbose_name_plural = "formaciones"

    def __str__(self):
        return self.title


class TrainingStep(models.Model):
    """Un paso del roadmap: una lectura, un cuestionario o un laboratorio."""

    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name="steps", verbose_name="formación")
    order = models.PositiveIntegerField("orden", default=0)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True, related_name="+", verbose_name="lectura")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True, related_name="+", verbose_name="cuestionario")
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, null=True, blank=True, related_name="+", verbose_name="laboratorio")

    class Meta:
        ordering = ["training", "order", "id"]
        verbose_name = "paso"
        verbose_name_plural = "pasos"
        constraints = [
            models.CheckConstraint(
                name="step_links_exactly_one_item",
                condition=(
                    Q(material__isnull=False, quiz__isnull=True, lab__isnull=True)
                    | Q(material__isnull=True, quiz__isnull=False, lab__isnull=True)
                    | Q(material__isnull=True, quiz__isnull=True, lab__isnull=False)
                ),
                violation_error_message="Cada paso enlaza exactamente una lectura, un cuestionario o un laboratorio.",
            )
        ]

    def __str__(self):
        return str(self.material or self.quiz or self.lab)


class CareerPath(models.Model):
    """Trayectoria profesional que cada usuario puede elegir y seguir."""

    title = models.CharField("título", max_length=200)
    summary = models.CharField("resumen", max_length=300, blank=True)
    description = models.TextField("descripción", blank=True, help_text="Markdown.")
    published = models.BooleanField("publicada", default=True)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "trayectoria"
        verbose_name_plural = "trayectorias"

    def __str__(self):
        return self.title


class PathStage(models.Model):
    """Hito de la columna central del mapa."""

    path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name="stages", verbose_name="trayectoria")
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        ordering = ["path", "order", "id"]
        verbose_name = "etapa"
        verbose_name_plural = "etapas"

    def __str__(self):
        return f"{self.path} · {self.title}"


class PathNode(models.Model):
    """Tema de una etapa. Puede enlazar contenido de la plataforma o un recurso externo."""

    class Kind(models.TextChoices):
        CORE = "core", "Imprescindible"
        RECOMMENDED = "recommended", "Recomendado"
        ALTERNATIVE = "alternative", "Alternativa"
        OPTIONAL = "optional", "Opcional"

    stage = models.ForeignKey(PathStage, on_delete=models.CASCADE, related_name="nodes", verbose_name="etapa")
    title = models.CharField("título", max_length=200)
    description = models.TextField("descripción", blank=True, help_text="Markdown.")
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices, default=Kind.CORE)
    order = models.PositiveIntegerField("orden", default=0)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="lectura")
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="cuestionario")
    lab = models.ForeignKey(Lab, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="laboratorio")
    training = models.ForeignKey(Training, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="formación")
    resource_url = models.URLField("recurso externo", blank=True)

    class Meta:
        ordering = ["stage", "order", "id"]
        verbose_name = "nodo"
        verbose_name_plural = "nodos"

    def __str__(self):
        return self.title


class PathEnrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="path_enrollments")
    path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name="enrollments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "path"], name="unique_path_enrollment")]


class NodeProgress(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        IN_PROGRESS = "in_progress", "En curso"
        DONE = "done", "Hecho"
        SKIPPED = "skipped", "Omitido"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="path_progress")
    node = models.ForeignKey(PathNode, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "node"], name="unique_node_progress")]
