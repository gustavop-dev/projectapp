from rest_framework import serializers

from content.models import ViewMapSettings

ALLOWED_FILTER_KEYS = {'categories', 'audiences', 'viewTypes'}


class ViewMapSettingsSerializer(serializers.ModelSerializer):
    """Singleton settings for the view-map panel."""

    class Meta:
        model = ViewMapSettings
        fields = ('default_view_mode', 'default_filters', 'updated_at')

    def validate_default_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('Los filtros por defecto deben ser un objeto.')
        unknown = set(value) - ALLOWED_FILTER_KEYS
        if unknown:
            raise serializers.ValidationError(
                f'Claves de filtro desconocidas: {", ".join(sorted(unknown))}.'
            )
        for key, items in value.items():
            if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                raise serializers.ValidationError(
                    f'El filtro "{key}" debe ser una lista de textos.'
                )
        return value
