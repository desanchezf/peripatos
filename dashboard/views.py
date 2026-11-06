from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notice
from .services import build_dashboard


class DashboardView(APIView):
    def get(self, request):
        return Response(build_dashboard(request.user))


class DismissNoticeView(APIView):
    def post(self, request, pk):
        get_object_or_404(Notice, pk=pk, active=True).dismissed_by.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
