from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets, generics, permissions, mixins
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Profile, AuthUser
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileSerializer,
    CustomTokenObtainPairSerializer,
)


class EmailTokenObtainPairLoginView(TokenObtainPairView):
    """For getting JWT token"""
    serializer_class = CustomTokenObtainPairSerializer


### FOR Testing
class RegisterView(generics.CreateAPIView):
    """Register new user"""
    queryset = AuthUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


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

