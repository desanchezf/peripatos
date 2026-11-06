from rest_framework.routers import SimpleRouter

from .views import LabViewSet, SubmissionViewSet

router = SimpleRouter()
router.register("labs", LabViewSet, basename="lab")
router.register("submissions", SubmissionViewSet, basename="submission")

urlpatterns = router.urls
