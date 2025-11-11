from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API's
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import (
    TabNumberTokenObtainPairLoginView,
    UserViewSet,
    ProfileViewSet,
    SetPasswordView,
    AdminUserImportViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'admin/users-import', AdminUserImportViewSet, basename='admin-users-import')

urlpatterns = [
    # Auth api's
    path('login', TabNumberTokenObtainPairLoginView.as_view(), name='login'),
    path('logout', TokenBlacklistView.as_view(), name='logout'),
    path('login/set-password', SetPasswordView.as_view(), name='set_password'),

    # users and profiles api's
    path('', include(router.urls)),
]