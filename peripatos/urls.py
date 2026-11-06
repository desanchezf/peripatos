"""
URL configuration for Peripatos.
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path
from django.views.static import serve

from .auth_api import CsrfView, LoginView, LogoutView, MeView


@staff_member_required
def private_file(request, path):
    """Enlaces a ficheros privados en el admin. Siempre como descarga: pueden ser subidas de usuarios."""
    response = serve(request, path, document_root=settings.PRIVATE_ROOT)
    response["Content-Disposition"] = "attachment"
    return response


urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("admin/", admin.site.urls),
    path("private/<path:path>", private_file),
    path("api/auth/csrf/", CsrfView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/theory/", include("theory.urls")),
    path("api/quizzes/", include("quizzes.urls")),
    path("api/labs/", include("labs.urls")),
    path("api/roadmap/", include("roadmap.urls")),
    path("api/assistant/", include("assistant.urls")),
]
