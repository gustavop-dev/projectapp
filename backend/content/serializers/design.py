from rest_framework import serializers
from content.models import Design

class DesignSerializer(serializers.ModelSerializer):
    """
    Serializer for the Design model, including the URLs for the cover and detail images.
    """
    cover_image_url = serializers.SerializerMethodField()
    detail_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Design
        fields = '__all__'

    def get_cover_image_url(self, obj):
        """
        Returns the full URL of the cover image.
        """
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_detail_image_url(self, obj):
        """
        Returns the full URL of the detail image.
        """
        request = self.context.get('request')
        if obj.detail_image and request:
            return request.build_absolute_uri(obj.detail_image.url)
        return None
