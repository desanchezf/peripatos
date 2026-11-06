from pathlib import Path

from django.db.models import Prefetch
from django.http import FileResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser

from .models import Lab, Submission
from .serializers import LabSerializer, SubmissionSerializer


class LabViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabSerializer
    pagination_class = None

    def get_queryset(self):
        mine = Submission.objects.filter(user=self.request.user)
        return Lab.objects.prefetch_related(Prefetch("submissions", queryset=mine, to_attr="user_submissions"))


class SubmissionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubmissionSerializer
    pagination_class = None
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True)
    def file(self, request, pk=None):
        submission = self.get_object()
        # Siempre como descarga: el contenido lo sube el usuario y no debe ejecutarse en este origen
        return FileResponse(submission.file.open("rb"), as_attachment=True, filename=Path(submission.file.name).name)
