from rest_framework import serializers

from content.models import Linktree, QRCard


class QRCardListSerializer(serializers.ModelSerializer):
    """Admin listing serializer — every field a listing row or edit form needs."""

    linktree_handle = serializers.CharField(source='linktree.handle', read_only=True, default=None)
    linktree_name = serializers.CharField(source='linktree.name', read_only=True, default=None)

    class Meta:
        model = QRCard
        fields = (
            'id', 'name', 'destination_url', 'destination_type',
            'linktree', 'linktree_handle', 'linktree_name',
            'is_active', 'created_at',
        )


class QRCardCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a QR card from the admin panel."""

    linktree = serializers.PrimaryKeyRelatedField(
        queryset=Linktree.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = QRCard
        fields = ('name', 'destination_url', 'destination_type', 'linktree', 'is_active')
        extra_kwargs = {
            'destination_url': {'required': False, 'allow_blank': True},
            'destination_type': {'required': False},
            'is_active': {'required': False},
        }
