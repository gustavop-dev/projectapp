from rest_framework import serializers

from content.models import Linktree, LinktreeButton
from content.models.linktree import HANDLE_VALIDATOR, RESERVED_HANDLES


def normalize_handle(value):
    """Public handles are stored lowercase and without the decorative '@'."""
    return (value or '').strip().lstrip('@').lower()


class LinktreeButtonSerializer(serializers.ModelSerializer):
    """Read serializer for one button — includes the derived render hints."""

    resolved_icon = serializers.ReadOnlyField()
    kind = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()

    class Meta:
        model = LinktreeButton
        fields = (
            'id', 'tier', 'action', 'label', 'href', 'icon',
            'resolved_icon', 'kind', 'is_pending', 'order', 'is_active',
        )


class LinktreeButtonWriteSerializer(serializers.ModelSerializer):
    """Write serializer for the nested `buttons` array."""

    class Meta:
        model = LinktreeButton
        fields = ('tier', 'action', 'label', 'href', 'icon', 'order', 'is_active')
        extra_kwargs = {
            'href': {'required': False, 'allow_blank': True},
            'icon': {'required': False, 'allow_blank': True},
            'order': {'required': False},
            'is_active': {'required': False},
        }


class LinktreeListSerializer(serializers.ModelSerializer):
    """Admin listing row."""

    public_path = serializers.ReadOnlyField()
    buttons_count = serializers.IntegerField(source='buttons.count', read_only=True)

    class Meta:
        model = Linktree
        fields = (
            'id', 'handle', 'name', 'kind', 'display_name',
            'is_active', 'public_path', 'buttons_count', 'created_at',
        )


class LinktreeDetailSerializer(serializers.ModelSerializer):
    """Full admin detail with nested buttons."""

    public_path = serializers.ReadOnlyField()
    buttons = LinktreeButtonSerializer(many=True, read_only=True)

    class Meta:
        model = Linktree
        fields = (
            'id', 'handle', 'name', 'kind',
            'display_name', 'role', 'bio', 'monogram',
            'claim_line_1', 'claim_line_2', 'badge_text',
            'footer_tagline', 'show_brand_header',
            'pwa_enabled', 'pwa_title', 'pwa_description',
            'vcard_first_name', 'vcard_last_name', 'vcard_org',
            'vcard_email', 'vcard_tel', 'vcard_url',
            'is_active', 'public_path', 'buttons',
            'created_at', 'updated_at',
        )


class PublicLinktreeSerializer(serializers.ModelSerializer):
    """Whitelist of fields the public /lk/@handle page needs."""

    buttons = serializers.SerializerMethodField()

    class Meta:
        model = Linktree
        fields = (
            'handle', 'kind',
            'display_name', 'role', 'bio', 'monogram',
            'claim_line_1', 'claim_line_2', 'badge_text',
            'footer_tagline', 'show_brand_header',
            'pwa_enabled', 'pwa_title', 'pwa_description',
            'vcard_first_name', 'vcard_last_name', 'vcard_org',
            'vcard_email', 'vcard_tel', 'vcard_url',
            'buttons',
        )

    def get_buttons(self, obj):
        active = [b for b in obj.buttons.all() if b.is_active]
        return LinktreeButtonSerializer(active, many=True).data


class LinktreeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Create/update from the panel. Accepts the full nested `buttons` array
    (replace semantics) and enforces the design system's hard rules.
    """

    buttons = LinktreeButtonWriteSerializer(many=True, required=False)
    # Declared explicitly so the raw input (which may carry the decorative
    # '@' and uppercase) is normalized in validate_handle BEFORE the model's
    # regex validator would reject it.
    handle = serializers.CharField(max_length=32)

    class Meta:
        model = Linktree
        fields = (
            'handle', 'name', 'kind',
            'display_name', 'role', 'bio', 'monogram',
            'claim_line_1', 'claim_line_2', 'badge_text',
            'footer_tagline', 'show_brand_header',
            'pwa_enabled', 'pwa_title', 'pwa_description',
            'vcard_first_name', 'vcard_last_name', 'vcard_org',
            'vcard_email', 'vcard_tel', 'vcard_url',
            'is_active', 'buttons',
        )

    def validate_handle(self, value):
        handle = normalize_handle(value)
        HANDLE_VALIDATOR(handle)
        if handle in RESERVED_HANDLES:
            raise serializers.ValidationError('Este handle está reservado por el sistema.')
        qs = Linktree.objects.filter(handle=handle)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Este handle ya está en uso.')
        return handle

    def validate_buttons(self, value):
        active = [b for b in value if b.get('is_active', True)]
        tiers = [b.get('tier', LinktreeButton.Tier.ROW) for b in active]

        primary_count = tiers.count(LinktreeButton.Tier.PRIMARY)
        if active and primary_count != 1:
            raise serializers.ValidationError(
                'Debe haber exactamente 1 botón principal (tier primary).'
            )
        if tiers.count(LinktreeButton.Tier.FEATURED) > 1:
            raise serializers.ValidationError(
                'Máximo 1 botón destacado (tier featured).'
            )
        pair_count = tiers.count(LinktreeButton.Tier.PAIR)
        if pair_count not in (0, 2):
            raise serializers.ValidationError(
                'Los botones de tier pair van exactamente de a 2 (o ninguno).'
            )
        if tiers.count(LinktreeButton.Tier.ROW) > 6:
            raise serializers.ValidationError(
                'Máximo 6 botones de tier row.'
            )
        return value

    def _replace_buttons(self, linktree, buttons_data):
        linktree.buttons.all().delete()
        LinktreeButton.objects.bulk_create([
            LinktreeButton(linktree=linktree, order=item.get('order', idx), **{
                key: val for key, val in item.items() if key != 'order'
            })
            for idx, item in enumerate(buttons_data)
        ])

    def create(self, validated_data):
        buttons_data = validated_data.pop('buttons', [])
        linktree = Linktree.objects.create(**validated_data)
        if buttons_data:
            self._replace_buttons(linktree, buttons_data)
        return linktree

    def update(self, instance, validated_data):
        buttons_data = validated_data.pop('buttons', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if buttons_data is not None:
            self._replace_buttons(instance, buttons_data)
        return instance
