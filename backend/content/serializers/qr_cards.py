from rest_framework import serializers

from content.models import QRCard


class QRCardListSerializer(serializers.ModelSerializer):
    """Admin listing serializer — every field a listing row or edit form needs."""

    class Meta:
        model = QRCard
        fields = ('id', 'name', 'destination_url', 'is_active', 'created_at')


class QRCardCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a QR card from the admin panel."""

    class Meta:
        model = QRCard
        fields = ('name', 'destination_url', 'is_active')
        extra_kwargs = {
            'destination_url': {'required': False, 'allow_blank': True},
            'is_active': {'required': False},
        }
