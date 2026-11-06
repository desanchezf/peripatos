from rest_framework import serializers

from .models import Bookmark, Material, Note


class MaterialSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    format = serializers.CharField(read_only=True)
    file_url = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = ["id", "title", "kind", "kind_label", "format", "file_url", "source_url", "content", "progress"]

    def get_file_url(self, obj):
        return f"/api/theory/materials/{obj.id}/file/" if obj.file else None

    def get_progress(self, obj):
        progress = obj.user_progress[0] if obj.user_progress else None
        if progress is None:
            return {"location": "", "percent": 0, "finished": False, "updated_at": None}
        return {
            "location": progress.location,
            "percent": progress.percent,
            "finished": progress.finished_at is not None,
            "updated_at": progress.updated_at,
        }


class ProgressUpdateSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=500, required=False, allow_blank=True)
    percent = serializers.FloatField(min_value=0, max_value=100, required=False)
    finished = serializers.BooleanField(required=False)


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["id", "material", "location", "label", "created_at"]
        read_only_fields = ["created_at"]


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "material", "location", "label", "quote", "text", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
