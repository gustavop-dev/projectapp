"""Small per-account preferences used by Django-session panel views."""

from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import UserProfile


class DocumentPanelPreferenceSerializer(serializers.Serializer):
    navigation_mode = serializers.ChoiceField(
        choices=UserProfile.DOCUMENT_NAVIGATION_CHOICES,
    )


def _profile_for(user):
    profile, _created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': UserProfile.ROLE_ADMIN},
    )
    return profile


@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def document_panel_preferences(request):
    """Read or persist the document navigation mode for the current account."""
    profile = _profile_for(request.user)

    if request.method == 'PATCH':
        serializer = DocumentPanelPreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.document_navigation_mode = serializer.validated_data['navigation_mode']
        profile.save(update_fields=['document_navigation_mode', 'updated_at'])

    return Response({'navigation_mode': profile.document_navigation_mode})
