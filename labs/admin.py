from django.contrib import admin

from .models import Lab


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ["title", "updated_at"]
    search_fields = ["title", "instructions"]
