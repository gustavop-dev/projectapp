"""Validation contracts for project access-detail mutations."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from accounts.models import ProjectAdminAccess


_http_url_validator = URLValidator(schemes=['http', 'https'])


def _validate_http_url(value):
    if not value:
        return ''
    try:
        _http_url_validator(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(
            'Ingresa una URL absoluta que comience por http:// o https://.'
        ) from exc
    return value


class ProjectAccessUpdateSerializer(serializers.Serializer):
    """One explicit field save in the project access editor."""

    environment = serializers.ChoiceField(
        choices=ProjectAdminAccess.Environment.choices,
        required=False,
    )
    repository_url = serializers.URLField(
        required=False,
        allow_blank=True,
        max_length=500,
        validators=[_validate_http_url],
    )
    site_url = serializers.URLField(
        required=False,
        allow_blank=True,
        max_length=500,
        validators=[_validate_http_url],
    )
    admin_url = serializers.URLField(
        required=False,
        allow_blank=True,
        max_length=500,
        validators=[_validate_http_url],
    )
    admin_username = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )
    admin_password = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=500,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        mutable_fields = {
            'repository_url', 'site_url', 'admin_url',
            'admin_username', 'admin_password',
        }
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({
                'non_field_errors': ['La solicitud contiene campos no permitidos.'],
            })

        supplied = mutable_fields.intersection(self.initial_data)
        if len(supplied) != 1:
            raise serializers.ValidationError({
                'non_field_errors': ['Guarda exactamente un campo por solicitud.'],
            })

        field = next(iter(supplied))
        environment = attrs.get('environment')
        if field == 'repository_url' and environment:
            raise serializers.ValidationError({
                'environment': ['El repositorio no pertenece a un ambiente.'],
            })
        if field != 'repository_url' and not environment:
            raise serializers.ValidationError({
                'environment': ['Selecciona producción o staging.'],
            })
        attrs['field'] = field
        return attrs


class ProjectAccessNoteCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField(max_length=10_000, trim_whitespace=False)
    is_sensitive = serializers.BooleanField(default=False)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El título es obligatorio.')
        return value

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('El contenido es obligatorio.')
        return value

    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({
                'non_field_errors': ['La solicitud contiene campos no permitidos.'],
            })
        return attrs


class ProjectAccessNoteUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    content = serializers.CharField(
        max_length=10_000,
        required=False,
        trim_whitespace=False,
    )
    is_sensitive = serializers.BooleanField(required=False)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El título es obligatorio.')
        return value

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('El contenido es obligatorio.')
        return value

    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({
                'non_field_errors': ['La solicitud contiene campos no permitidos.'],
            })
        if not attrs:
            raise serializers.ValidationError({
                'non_field_errors': ['Envía al menos un campo para guardar.'],
            })
        return attrs


class ProjectLegacyAccessClassifySerializer(serializers.Serializer):
    environment = serializers.ChoiceField(
        choices=ProjectAdminAccess.Environment.choices,
    )
