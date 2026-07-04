"""Serializer for freeform LinkedIn posts."""
from django.utils import timezone
from rest_framework import serializers

from content.models import LinkedInPost


class LinkedInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedInPost
        fields = [
            'id', 'commentary', 'image', 'status', 'scheduled_at',
            'published_at', 'linkedin_post_id', 'error_message',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'status', 'published_at', 'linkedin_post_id',
            'error_message', 'created_at', 'updated_at',
        ]

    def validate_scheduled_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                'La fecha programada debe estar en el futuro.'
            )
        return value
