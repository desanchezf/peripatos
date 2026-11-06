from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_roadmaps


class RoadmapListView(APIView):
    def get(self, request):
        return Response(build_roadmaps(request.user))


class RoadmapDetailView(APIView):
    def get(self, request, pk):
        for roadmap in build_roadmaps(request.user):
            if roadmap["id"] == pk:
                return Response(roadmap)
        raise NotFound()
