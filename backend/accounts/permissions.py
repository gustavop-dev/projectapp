from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to users with the admin role."""

    message = 'Solo los administradores pueden acceder a este recurso.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.is_admin


class IsClientRole(BasePermission):
    """Allow access only to users with the client role."""

    message = 'Solo los clientes pueden acceder a este recurso.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.is_client


class IsOnboarded(BasePermission):
    """Allow access only to fully onboarded users."""

    message = 'Debes completar la configuración de tu cuenta primero.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.is_onboarded
