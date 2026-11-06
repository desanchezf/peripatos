from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ["title", "level", "active", "created_at"]
    list_filter = ["level", "active"]
