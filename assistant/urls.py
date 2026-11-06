from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet, LLMModelListView

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("models/", LLMModelListView.as_view(), name="llm-models"),
    path("", include(router.urls)),
]
