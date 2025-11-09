from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer
)

from psycopg2.errors import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, AuthUser


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer - using user's email for auth
    """
    username_field = "tab-number"


class CustomTokenObtainPairSerializer(EmailTokenObtainPairSerializer):

    def validate(self, attrs):
        tab_number = attrs.get("tab-number")
        password = attrs.get("password")

        if not tab_number or not password:
            raise AuthenticationFailed(detail="Email and password are required")

        try:
            user = AuthUser.objects.get(tab_number=tab_number)
        except AuthUser.DoesNotExist:
            raise AuthenticationFailed(detail="User not found")

        if not user.check_password(password):
            raise AuthenticationFailed(detail="Incorrect password")

        data = super().get_token(user)
        return {
            "refresh": str(data),
            "access": str(data.access_token),
        }


class RegisterSerializer(serializers.ModelSerializer):
    """Register serializer"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=AuthUser.objects.all())]
    )
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

    class Meta:
        model = AuthUser
        fields = (
            "id", "tab_number", "email", "password", "password2", "first_name", "last_name"
        )

    def validate(self, attrs):
        """Checking password and password2"""
        if attrs["password"] != attrs["password2"]:
            raise ValidationError(detail="The passwords dont't match")
        elif len(attrs["first_name"]) < 3:
            raise ValidationError(detail="The first name is too short")
        elif len(attrs["last_name"]) < 3:
            raise ValidationError(detail="The last name is too short")       
        return attrs

    def create(self, validated_data):
        try:
            user = AuthUser.objects.create_user(
                tab_number=validated_data["tab_number"],
                email=validated_data.get("email"),
                password=validated_data["password"],
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                username=validated_data["tab_number"],
            )
        except IntegrityError as e:
            # if email already exists
            raise ValidationError(detail="User with email already exists")
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
        fields = ("id", "user", "about_me", "avatar")