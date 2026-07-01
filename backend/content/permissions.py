from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Allows access only to authenticated superusers.

    Used by the accounting module (módulo contable): financial data is
    restricted to the company owners, not regular panel staff.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
