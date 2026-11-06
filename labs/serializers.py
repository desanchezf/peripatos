from pathlib import Path

from rest_framework import serializers

from .models import Lab, Submission, validate_solution_size


class SubmissionSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, max_length=150, validators=[validate_solution_size])

    class Meta:
        model = Submission
        fields = ["id", "lab", "file", "file_name", "file_url", "comment", "status", "status_label", "feedback", "submitted_at", "reviewed_at"]
        read_only_fields = ["status", "feedback", "submitted_at", "reviewed_at"]

    def get_file_name(self, obj):
        return Path(obj.file.name).name

    def get_file_url(self, obj):
        return f"/api/labs/submissions/{obj.id}/file/"


class LabSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()

    class Meta:
        model = Lab
        fields = ["id", "title", "statement", "theory", "due_date", "submissions"]

    def get_submissions(self, obj):
        return SubmissionSerializer(obj.user_submissions, many=True).data
