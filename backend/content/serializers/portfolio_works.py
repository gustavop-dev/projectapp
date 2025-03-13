from rest_framework import serializers
from content.models import PortfolioWork

class PortfolioWorkSerializer(serializers.ModelSerializer):
    """
    Serializer for the PortfolioWork model, providing all model fields including the URL for the cover image
    and the project URL for external redirection.
    """

    class Meta:
        model = PortfolioWork
        fields = '__all__'