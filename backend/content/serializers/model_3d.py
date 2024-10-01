from rest_framework import serializers
from content.models import Model3D

class Model3DSerializer(serializers.ModelSerializer):
    """
    Serializer for the Model3D model, including the URLs for the image and file fields.
    """
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Model3D
        fields = '__all__'

    def get_image_url(self, obj):
        """
        Returns the full URL of the image.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_file_url(self, obj):
        """
        Returns the full URL of the 3D model file.
        """
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
