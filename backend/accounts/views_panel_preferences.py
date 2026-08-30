"""Small per-account preferences used by Django-session panel views."""

from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import CommunicationPanelPreference, UserProfile


class DocumentPanelPreferenceSerializer(serializers.Serializer):
    navigation_mode = serializers.ChoiceField(
        choices=UserProfile.DOCUMENT_NAVIGATION_CHOICES,
    )


class CommunicationPanelPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationPanelPreference
        fields = [
            'navigation_mode',
            'thread_order',
            'page_size',
            'default_channel',
            'show_manual_help',
            'navigation_width',
        ]

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=[*validated_data, 'updated_at'])
        return instance


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


def _communication_response(preference, *, legacy_import_allowed=False):
    data = CommunicationPanelPreferenceSerializer(preference).data
    data['legacy_import_allowed'] = legacy_import_allowed
    return Response(data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAdminUser])
def communication_panel_preferences(request):
    """Read or persist Communications defaults for the current account."""
    preference, created = CommunicationPanelPreference.objects.get_or_create(
        user=request.user,
    )

    if request.method == 'PATCH':
        serializer = CommunicationPanelPreferenceSerializer(
            preference,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        preference = serializer.save()
        created = False

    return _communication_response(
        preference,
        legacy_import_allowed=created,
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_communication_panel_preferences(request):
    """Restore every Communications preference without touching saved views."""
    preference, _created = CommunicationPanelPreference.objects.get_or_create(
        user=request.user,
    )
    preference.reset()
    return _communication_response(preference)
