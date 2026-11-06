from django.urls import path
from rest_framework.routers import SimpleRouter

from .paths import CareerPathViewSet, NodeProgressView
from .views import RoadmapDetailView, RoadmapListView

router = SimpleRouter()
router.register("paths", CareerPathViewSet, basename="career-path")

urlpatterns = [
    path("trainings/", RoadmapListView.as_view()),
    path("trainings/<int:pk>/", RoadmapDetailView.as_view()),
    path("nodes/<int:pk>/progress/", NodeProgressView.as_view()),
    *router.urls,
]
