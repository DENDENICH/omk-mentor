from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API's
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import (
    EmailTokenObtainPairLoginView,
    UserViewSet,
    ProfileViewSet,
    ### For testing
    # RegisterView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    # Auth api's
    path('login', EmailTokenObtainPairLoginView.as_view(), name='login'),
    path('logout', TokenBlacklistView.as_view(), name='logout'),
    ### For testing
    # path('register', RegisterView.as_view(), name='register'),

    # users and profiles api's
    path('', include(router.urls)),
]