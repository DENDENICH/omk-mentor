from rest_framework import permissions

from typing import Optional

from .models import Enrollment


class RolePermission(permissions.BasePermission):
    """
    Universal class for checking permission by role
    Example using:
        permission_classes = [RolePermission.allow('teacher', 'student')]
    """

    def __init__(self, *args):
        """
        param: *args: roles for permission
        """
        self.allowed_roles = args

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        active_membership_id = request.headers.get('X-Active-Membership')  # либо request.data, либо session
        if not active_membership_id:
            return False
        try:
            membership = Enrollment.objects.get(id=active_membership_id, user=user)
        except Enrollment.DoesNotExist:
            return False
        return membership.role in self.allowed_roles

        
    
    @classmethod
    def allow(cls, *roles):
        class _RolePermission(cls):
            def __init__(self):
                super().__init__(*roles)
        return _RolePermission