from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CareerPath, NodeProgress, PathEnrollment, PathNode

DONE = NodeProgress.Status.DONE
SKIPPED = NodeProgress.Status.SKIPPED


def node_links(node):
    links = []
    if node.material_id:
        links.append({"type": "reading", "title": node.material.title, "to": f"/readings/{node.material_id}"})
    if node.quiz_id:
        links.append({"type": "quiz", "title": node.quiz.title, "to": f"/quizzes/{node.quiz_id}"})
    if node.lab_id:
        links.append({"type": "lab", "title": node.lab.title, "to": f"/labs/{node.lab_id}"})
    if node.training_id:
        links.append({"type": "training", "title": node.training.title, "to": f"/roadmap/{node.training_id}"})
    return links


def path_summary(path, statuses, enrolled):
    nodes = [node for stage in path.stages.all() for node in stage.nodes.all()]
    done = sum(statuses.get(node.id) == DONE for node in nodes)
    # Lo omitido no cuenta: elegir una alternativa no deja la trayectoria incompleta
    counted = sum(statuses.get(node.id) != SKIPPED for node in nodes)
    return {
        "id": path.id,
        "title": path.title,
        "summary": path.summary,
        "stage_count": len(path.stages.all()),
        "node_count": len(nodes),
        "done_nodes": done,
        "percent": round(100 * done / counted) if counted else 0,
        "enrolled": enrolled,
    }


class CareerPathViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = CareerPath.objects.filter(published=True).prefetch_related(
        "stages__nodes__material", "stages__nodes__quiz", "stages__nodes__lab", "stages__nodes__training"
    )

    def _statuses(self):
        return dict(NodeProgress.objects.filter(user=self.request.user).values_list("node_id", "status"))

    def _enrolled(self):
        return set(PathEnrollment.objects.filter(user=self.request.user).values_list("path_id", flat=True))

    def list(self, request):
        statuses, enrolled = self._statuses(), self._enrolled()
        return Response([path_summary(path, statuses, path.id in enrolled) for path in self.get_queryset()])

    def _detail(self, path):
        statuses = self._statuses()
        return {
            **path_summary(path, statuses, path.id in self._enrolled()),
            "description": path.description,
            "stages": [
                {
                    "id": stage.id,
                    "title": stage.title,
                    "description": stage.description,
                    "nodes": [
                        {
                            "id": node.id,
                            "title": node.title,
                            "description": node.description,
                            "kind": node.kind,
                            "kind_label": node.get_kind_display(),
                            "status": statuses.get(node.id, NodeProgress.Status.PENDING),
                            "links": node_links(node),
                            "resource_url": node.resource_url,
                        }
                        for node in stage.nodes.all()
                    ],
                }
                for stage in path.stages.all()
            ],
        }

    def retrieve(self, request, pk=None):
        return Response(self._detail(self.get_object()))

    @action(detail=True, methods=["post", "delete"])
    def enrollment(self, request, pk=None):
        path = self.get_object()
        if request.method == "POST":
            PathEnrollment.objects.get_or_create(user=request.user, path=path)
        else:
            # El progreso se conserva por si vuelve a elegirla
            PathEnrollment.objects.filter(user=request.user, path=path).delete()
        return Response(self._detail(path))


class NodeProgressView(APIView):
    def put(self, request, pk):
        node = get_object_or_404(PathNode.objects.select_related("stage"), pk=pk, stage__path__published=True)
        if not PathEnrollment.objects.filter(user=request.user, path_id=node.stage.path_id).exists():
            raise ValidationError({"detail": "Elige esta trayectoria para registrar tu avance."})
        value = request.data.get("status")
        if value not in NodeProgress.Status.values:
            raise ValidationError({"status": ["Estado no válido."]})
        NodeProgress.objects.update_or_create(user=request.user, node=node, defaults={"status": value})
        return Response({"id": node.id, "status": value}, status=status.HTTP_200_OK)
