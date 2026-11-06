from django.contrib import admin
from django.utils import timezone

from .models import Lab, Submission


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ["title", "due_date", "updated_at"]
    search_fields = ["title", "statement", "theory"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["lab", "user", "status", "submitted_at", "reviewed_at"]
    list_filter = ["status", "lab"]
    readonly_fields = ["user", "lab", "file", "comment", "submitted_at", "reviewed_at"]

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if obj.status == Submission.Status.REVIEWED and obj.reviewed_at is None:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
