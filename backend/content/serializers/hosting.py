from rest_framework import serializers
from content.models import Hosting

class HostingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Hosting model.
    """
    class Meta:
        model = Hosting
        fields = '__all__'
