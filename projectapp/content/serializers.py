from rest_framework import serializers
from .models import Contact, Models3D, Designs, CategoriesDevelopment, Section, Components, Example

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['email', 'subject', 'message']

class Models3DSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Models3D
        fields = ['id', 'title_en', 'title_es', 'image_url', 'file_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

class DesignsSerializer(serializers.ModelSerializer):
    presentation_image_url = serializers.SerializerMethodField()
    detail_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Designs
        fields = ['id', 'title_en', 'title_es', 'presentation_image_url', 'detail_image_url']

    def get_presentation_image_url(self, obj):
        request = self.context.get('request')
        if obj.presentation_image and request:
            return request.build_absolute_uri(obj.presentation_image.url)
        return None

    def get_detail_image_url(self, obj):
        request = self.context.get('request')
        if obj.detail_image and request:
            return request.build_absolute_uri(obj.detail_image.url)
        return None
    
class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Example
        fields = ['id', 'title_en', 'title_es', 'image']

class ComponentsSerializer(serializers.ModelSerializer):
    examples = ExampleSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Components
        fields = ['id', 'title_en', 'title_es', 'image_url', 'examples']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class SectionSerializer(serializers.ModelSerializer):
    components = ComponentsSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ['id', 'title_en', 'title_es', 'components']

class CategoriesDevelopmentSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriesDevelopment
        fields = ['id', 'title_en', 'title_es', 'description_en', 'description_es', 'sections']