from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

from .models import Group
from .serializer import GroupSerializer


class GroupViewSet(ModelViewSet):
    """CRUD для групп"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # permission_classes = [IsAuthenticated]

    # фильтры и поиск
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter
    ]
    search_fields = ["name", "organizer__username"]
    filterset_fields = ["organizer__username", "name"]
    ordering_fields = ["name", "organizer__username"]


