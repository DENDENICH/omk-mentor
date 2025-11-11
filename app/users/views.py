import io
import pandas as pd

from django.http import HttpResponse

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import viewsets, mixins

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, AuthUser
from .serializers import (
    UserSerializer,
    ProfileSerializer,
    TabNumberTokenObtainPairSerializer,
    SetPasswordSerializer,
    UserExcelUploadSerializer
)
from .permissions import RolePermission 


class TabNumberTokenObtainPairLoginView(TokenObtainPairView):
    """For getting JWT token"""
    serializer_class = TabNumberTokenObtainPairSerializer


class AdminUserImportViewSet(viewsets.ViewSet):
    """
    Creating users and importing users from Excel-file
    """
    permission_classes = [RolePermission.allow('admin')]

    @action(detail=False, methods=['get'], url_path='download-template')
    def download_template(self, request):
        df = pd.DataFrame(columns=['first_name', 'last_name', 'email', 'tab_number'])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')
        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="users_template.xlsx"'
        return response


    @action(detail=False, methods=['post'], url_path='upload-excel', parser_classes=[MultiPartParser, FormParser])
    def upload_excel(self, request):
        serializer = UserExcelUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data['file']

        try:
            df = pd.read_excel(file_obj, engine='openpyxl')
        except Exception as e:
            return Response({"detail": f"Не удалось прочитать Excel-файл: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # проверяем необходимые столбцы
        expected_cols = {'first_name', 'last_name', 'email', 'tab_number'}
        if not expected_cols.issubset(set(df.columns)):
            return Response({"detail": f"В файле отсутствуют столбцы: {expected_cols - set(df.columns)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []

        for idx, row in df.iterrows():
            first_name = row['first_name']
            last_name = row['last_name']
            email = row['email']
            tab_number = row['tab_number']

            # Бизнес-логика: например, если пользователь с tab_number уже существует — пропускаем или фиксируем ошибку
            if AuthUser.objects.filter(tab_number=tab_number).exists():
                errors.append({"row": idx + 2, "tab_number": tab_number, "detail": "Пользователь с таким tab_number уже существует"})
                continue

            user = AuthUser(
                first_name=first_name,
                last_name=last_name,
                email=email,
                tab_number=tab_number,
                is_auth=False   # по бизнес-логике: пароль ещё не задан
            )
            user.set_unusable_password()
            user.save()
            created.append({"tab_number": tab_number, "user_id": user.id})

        return Response({
            "created": created,
            "errors": errors
        }, status=status.HTTP_200_OK)


class SetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user: AuthUser = serializer.save()

        # выдаём токены после установки пароля
        refresh = RefreshToken.for_user(user)
        return Response({
            "detail": "Password is state",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)



class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """RUD for user"""
    queryset = AuthUser.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        # Admin viewing all user
        user = self.request.user
        if user.is_superuser:
            return AuthUser.objects.all()
        return AuthUser.objects.filter(id=user.id)


class ProfileViewSet(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """RUD for user's profile"""
    queryset = Profile.objects.select_related("user")
    serializer_class = ProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Profile.objects.all()
        return Profile.objects.filter(user=user)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Getting self profile"""
        profile = Profile.objects.get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

