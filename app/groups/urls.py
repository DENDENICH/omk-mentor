from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    GroupViewSet
)

app_name = "group"

router = DefaultRouter()
router.register("group", GroupViewSet)

urlpatterns = [
    path("", include(router.urls))
]
