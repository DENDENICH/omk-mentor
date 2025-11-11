from rest_framework import permissions


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

        # profile = getattr(user, "profile", None)
        # if not profile:
        #     return False

        # return profile.role in self.allowed_roles
    
    @classmethod
    def allow(cls, *roles):
        class _RolePermission(cls):
            def __init__(self):
                super().__init__(*roles)
        return _RolePermission


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff