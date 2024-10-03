from rest_framework import serializers
from content.models import Model3D

class Model3DSerializer(serializers.ModelSerializer):
    """
    Serializer for the Model3D model, including the URLs for the image and file fields.
    """

    class Meta:
        model = Model3D
        fields = '__all__'
