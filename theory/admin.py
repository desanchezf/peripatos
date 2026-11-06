from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "format", "updated_at"]
    list_filter = ["kind"]
    search_fields = ["title", "content"]

    @admin.display(description="formato")
    def format(self, obj):
        return obj.format
