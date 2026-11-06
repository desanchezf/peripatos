from django.contrib import admin

from .models import LLMModel


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ["__str__", "provider", "name", "position", "is_active"]
    list_editable = ["position", "is_active"]
    list_filter = ["provider", "is_active"]
    search_fields = ["name", "display_name"]
