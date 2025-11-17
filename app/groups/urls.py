from rest_framework.routers import DefaultRouter
from .views import GroupImportViewSet

router = DefaultRouter()
router.register(r'group-import', GroupImportViewSet, basename='group-import')
urlpatterns = router.urls

