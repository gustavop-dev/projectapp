from rest_framework import serializers
from content.models import Design

class DesignSerializer(serializers.ModelSerializer):
    """
    Serializer for the Design model, including the URLs for the cover and detail images.
    """

    class Meta:
        model = Design
        fields = '__all__'
