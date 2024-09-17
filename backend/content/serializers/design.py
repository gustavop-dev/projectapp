from rest_framework import serializers
from content.models import Design

class DesignSerializer(serializers.ModelSerializer):
    """
    Serializer for the Design model.
    """
    class Meta:
        model = Design
        fields = '__all__'
