from django.db.models import Prefetch
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Bookmark, Material, Note, ReadingProgress
from .serializers import BookmarkSerializer, MaterialSerializer, NoteSerializer, ProgressUpdateSerializer

CONTENT_TYPES = {"pdf": "application/pdf", "epub": "application/epub+zip"}


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaterialSerializer
    pagination_class = None

    def get_queryset(self):
        mine = ReadingProgress.objects.filter(user=self.request.user)
        return Material.objects.prefetch_related(Prefetch("progress", queryset=mine, to_attr="user_progress"))

    @action(detail=True)
    def file(self, request, pk=None):
        material = self.get_object()
        if not material.file:
            return Response({"detail": "Este material no tiene fichero."}, status=404)
        return FileResponse(material.file.open("rb"), content_type=CONTENT_TYPES.get(material.format))

    @action(detail=True, methods=["patch"])
    def progress(self, request, pk=None):
        material = self.get_object()
        update = ProgressUpdateSerializer(data=request.data)
        update.is_valid(raise_exception=True)
        data = update.validated_data

        progress, _ = ReadingProgress.objects.get_or_create(user=request.user, material=material)
        progress.location = data.get("location", progress.location)
        progress.percent = data.get("percent", progress.percent)
        # Llegar al final la marca como leída; desmarcarla es una decisión explícita
        finished = data.get("finished", progress.finished_at is not None or progress.percent >= 100)
        if not finished:
            progress.finished_at = None
        elif progress.finished_at is None:
            progress.finished_at = timezone.now()
        progress.save()

        material.user_progress = [progress]
        return Response(self.get_serializer(material).data)


class OwnedByUserViewSet(viewsets.ModelViewSet):
    """CRUD de los registros del usuario, filtrables con ?material=<id>."""

    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        material = self.request.query_params.get("material")
        return queryset.filter(material_id=material) if material and material.isdigit() else queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkViewSet(OwnedByUserViewSet):
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer


class NoteViewSet(OwnedByUserViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
