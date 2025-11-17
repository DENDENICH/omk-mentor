from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from django.http import HttpResponse
from .serializers import GroupTemplateSerializer, GroupUploadSerializer
from users.permissions import IsAdminPermission


class GroupImportViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminPermission]

    @action(detail=False, methods=['get'], url_path="download-template")
    def download_template(self, request):
        serializer = GroupTemplateSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        buffer, filename = serializer.build_template()
        resp = HttpResponse(
            buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    @action(detail=False, methods=['post'], url_path="upload-excel", parser_classes=[MultiPartParser])
    def upload_excel(self, request):
        serializer = GroupUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
