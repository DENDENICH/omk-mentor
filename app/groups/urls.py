from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    GroupImportViewSet,
    GroupAPIView
)

router = DefaultRouter()
router.register(r'group-import', GroupImportViewSet, basename='group-import')
urlpatterns = [
    path("groups/create", GroupAPIView.as_view(), name="group-create"),
] + router.urls

