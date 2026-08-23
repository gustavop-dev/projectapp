from rest_framework import serializers

from content.email_copy_families import (
    CLIENT_EMAIL_FAMILY_CHOICES,
    CLIENT_EMAIL_FAMILY_VALUES,
)
from content.models import ClientEmailCopyRecipient


class ClientEmailCopyRecipientSerializer(serializers.ModelSerializer):
    family_labels = serializers.SerializerMethodField()

    class Meta:
        model = ClientEmailCopyRecipient
        fields = (
            'id', 'email', 'is_active', 'families', 'family_labels',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'family_labels', 'created_at', 'updated_at')
        extra_kwargs = {'email': {'validators': []}}

    def validate_email(self, value):
        normalized = (value or '').strip().lower()
        queryset = ClientEmailCopyRecipient.objects.filter(
            email__iexact=normalized,
        )
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Ese correo ya está en la lista.')
        return normalized

    def validate_families(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Debe ser una lista.')
        unknown = set(value) - set(CLIENT_EMAIL_FAMILY_VALUES)
        if unknown:
            raise serializers.ValidationError(
                f'Familias no válidas: {", ".join(sorted(unknown))}.',
            )
        selected = set(value)
        return [family for family in CLIENT_EMAIL_FAMILY_VALUES if family in selected]

    def validate(self, attrs):
        instance = self.instance
        active = attrs.get(
            'is_active', instance.is_active if instance is not None else True,
        )
        families = attrs.get(
            'families',
            instance.families if instance is not None
            else list(CLIENT_EMAIL_FAMILY_VALUES),
        )
        if active and not families:
            raise serializers.ValidationError({
                'families': 'Un destinatario activo debe cubrir al menos una familia.',
            })
        return attrs

    def get_family_labels(self, obj):
        labels = dict(CLIENT_EMAIL_FAMILY_CHOICES)
        return [labels[family] for family in obj.families if family in labels]

