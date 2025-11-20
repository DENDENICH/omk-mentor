import os
from typing import Any, cast

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from drf_spectacular.utils import extend_schema, OpenApiResponse

from django.http import FileResponse, Http404
from django.conf import settings

from .serializers import GroupImportSchemaSerializer
from .exceptions import CustomException

from users.permissions import IsAdminPermission
from .bussines_logic.creating_group.importing_excel_data import ExcelGroupParser
from .bussines_logic.creating_group.creating_group import GroupCreatingService
from .bussines_logic.creating_group.items import ImportData


class GroupImportViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminPermission]

    excel_template_name = 'your_group_name.xlsx'

    @action(detail=False, methods=['get'], url_path="download-template")
    def download_template(self, request):
        file_path = os.path.join(settings.BASE_DIR, 'templates_files', self.excel_template_name)
        if not os.path.exists(file_path):
            raise Http404("Template file not found")
        response = FileResponse(open(file_path, 'rb'),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="users_template.xlsx"'
        return response

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Excel with users'
                    }
                },
                'required': ['file']
            }
        },
        responses={
        200: OpenApiResponse(
            response=GroupImportSchemaSerializer,
            description="JSON черновик группы"
        ),
        400: OpenApiResponse(description="Ошибка валидации файла"),
        500: OpenApiResponse(description="Ошибка обработки файла"),
    },
    tags=["groups"],
        summary="Загрузка Excel файла",
        description="Загружает Excel-файл и возвращает JSON схему"
    )
    @action(
        detail=False,
        methods=['post'],
        url_path="upload-excel",
        parser_classes=[MultiPartParser]
    )
    def upload_excel(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Файл обязателен"}, status=400)

        parser = ExcelGroupParser()

        try:
            draft = parser.parse(file, file.name)
        except CustomException as e:
            return Response({"detail": str(e)}, status=e.code)

        return Response(draft, status=200)


class GroupAPIView(APIView):

    @extend_schema(
        request=GroupImportSchemaSerializer,
        responses={200: dict},
        summary="Подтвердить импорт (создание групп, подгрупп и связей)",
        tags=["groups"],
    )
    def post(self, request):
        serializer = GroupImportSchemaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = GroupCreatingService()
        try:
            data: ImportData = cast(ImportData, serializer.validated_data)
            result = service.import_json(data)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

        return Response(result, status=200)