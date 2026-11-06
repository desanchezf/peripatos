from rest_framework.routers import SimpleRouter

from .views import BookmarkViewSet, MaterialViewSet, NoteViewSet

router = SimpleRouter()
router.register("materials", MaterialViewSet, basename="material")
router.register("bookmarks", BookmarkViewSet, basename="bookmark")
router.register("notes", NoteViewSet, basename="note")

urlpatterns = router.urls
