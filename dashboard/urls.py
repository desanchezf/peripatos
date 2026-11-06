from django.urls import path

from .views import DashboardView, DismissNoticeView

urlpatterns = [
    path("", DashboardView.as_view()),
    path("notices/<int:pk>/dismiss/", DismissNoticeView.as_view()),
]
