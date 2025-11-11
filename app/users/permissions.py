from rest_framework import permissions

from typing import Optional

from .models import Profile


def _cheking_profile_role(request, view, role: str) -> bool:
    user = request.user
    if not user or not user.is_authenticated:
        return False
    profile: Optional[Profile] = getattr(user, "profile", None)
    if not profile:
        return False

    return profile.account_role == role


class IsAdminPermission(permissions.BasePermission):
    """
    Allows access only to users with role 'admin'.
    """

    def has_permission(self, request, view):
        return _cheking_profile_role(request, view, 'admin')

    

class IsOrganizerPermission(permissions.BasePermission):
    """
    Allows access only to users with role 'organizer'.
    """

    def has_permission(self, request, view):
        return _cheking_profile_role(request, view, 'organizer')
