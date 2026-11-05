from django.db import models


class Lab(models.Model):
    title = models.CharField("título", max_length=200)
    instructions = models.TextField("instrucciones", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "laboratorio"
        verbose_name_plural = "laboratorios"

    def __str__(self):
        return self.title
