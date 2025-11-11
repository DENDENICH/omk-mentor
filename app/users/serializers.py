from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer
)
from .models import Profile, AuthUser


class TabNumberTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer - using user's tab_number for auth
    """
    username_field = 'tab_number'

    def validate(self, attrs):
        # Попытка аутентификации
        tab_number = attrs.get("tab_number")
        password = attrs.get("password")

        if not tab_number or not password:
            raise ValidationError(detail="tab number and password are required")

        try:
            user = AuthUser.objects.get(tab_number=tab_number)
        except AuthUser.DoesNotExist:
            raise AuthenticationFailed(detail="User not found")


        # Проверка флага is_auth
        if not user.is_auth:
            raise ValidationError({
                "detail": "Must be set password",
                "code": "password_not_set"
            })
        
        print(user.password)
        if not user.check_password(password):
            raise AuthenticationFailed(detail="Incorrect password")

        # Всё ок — вызываем родительскую валидацию, получаем токены
        data = super().get_token(user)
        return {
            "refresh": str(data),
            "access": str(data.access_token),
        }



class SetPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting password for not auth user
    """
    tab_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label="Подтверждение пароля",
        style={'input_type': 'password'}
    )


    def validate(self, attrs):
        try:
            user = AuthUser.objects.get(tab_number=attrs['tab_number'])
        except AuthUser.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")

        if user.is_auth:
            raise serializers.ValidationError("Пароль уже задан")

        if attrs["password"] != attrs["password2"]:
            raise ValidationError(detail="The passwords dont't match")

        attrs['user'] = user
        return attrs

    def save(self, **kwargs) -> AuthUser:
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.is_auth = True
        user.save()
        return user



class AdminCreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['first_name', 'last_name', 'email', 'tab_number']

    def create(self, validated_data):
        user = AuthUser.objects.create(**validated_data)
        user.set_unusable_password()  # пароль нельзя использовать
        user.is_auth = False
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """For view and updating info about user"""
    class Meta:
        model = AuthUser
        fields = ("id", "tab_number", "email", "first_name", "last_name", "is_active")


class ProfileSerializer(serializers.ModelSerializer):
    """The profile of user"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "user", "avatar")


class UserExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class UserTemplateDownloadSerializer(serializers.Serializer):
    pass
