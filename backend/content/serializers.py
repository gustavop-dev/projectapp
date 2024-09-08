from rest_framework import serializers
from .models import Contact, Models3D, Designs, CategoriesDevelopment, Section, Components, Example

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contact model, used to handle data validation and serialization
    for contact messages sent through the contact form.

    Fields:
        - email: The email address of the contact.
        - subject: The subject of the message.
        - message: The message content.
    """
    class Meta:
        model = Contact
        fields = '__all__'


class Models3DSerializer(serializers.ModelSerializer):
    """
    Serializer for the Models3D model, responsible for serializing the 3D model data,
    including generating absolute URLs for the image and file fields.

    Fields:
        - id: The ID of the 3D model.
        - title_en: The English title of the 3D model.
        - title_es: The Spanish title of the 3D model.
        - image_url: The absolute URL of the 3D model's image.
        - file_url: The absolute URL of the 3D model's file.
    """
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Models3D
        fields = '__all__'

    def get_image_url(self, obj):
        """
        Get the absolute URL for the 3D model's image.
        """
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_file_url(self, obj):
        """
        Get the absolute URL for the 3D model's file.
        """
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class DesignsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Designs model, responsible for serializing the design data,
    including generating absolute URLs for presentation and detail images.

    Fields:
        - id: The ID of the design.
        - title_en: The English title of the design.
        - title_es: The Spanish title of the design.
        - presentation_image_url: The absolute URL of the presentation image.
        - detail_image_url: The absolute URL of the detail image.
    """
    presentation_image_url = serializers.SerializerMethodField()
    detail_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Designs
        fields = '__all__'

    def get_presentation_image_url(self, obj):
        """
        Get the absolute URL for the presentation image.
        """
        request = self.context.get('request')
        if obj.presentation_image and request:
            return request.build_absolute_uri(obj.presentation_image.url)
        return None

    def get_detail_image_url(self, obj):
        """
        Get the absolute URL for the detail image.
        """
        request = self.context.get('request')
        if obj.detail_image and request:
            return request.build_absolute_uri(obj.detail_image.url)
        return None


class ExampleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Example model, used to handle data for example objects.

    Fields:
        - id: The ID of the example.
        - title_en: The English title of the example.
        - title_es: The Spanish title of the example.
        - image: The image associated with the example.
    """
    class Meta:
        model = Example
        fields = '__all__'


class ComponentsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Components model, handling the serialization of component data,
    including its examples and image URL.

    Fields:
        - id: The ID of the component.
        - title_en: The English title of the component.
        - title_es: The Spanish title of the component.
        - image_url: The absolute URL of the component's image.
        - examples: The related examples for the component.
    """
    examples = ExampleSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Components
        fields = '__all__'

    def get_image_url(self, obj):
        """
        Get the absolute URL for the component's image.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Section model, handling the serialization of sections,
    including their related components.

    Fields:
        - id: The ID of the section.
        - title_en: The English title of the section.
        - title_es: The Spanish title of the section.
        - components: The related components in the section.
    """
    components = ComponentsSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = '__all__'


class CategoriesDevelopmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the CategoriesDevelopment model, handling the serialization
    of development categories, including their related sections.

    Fields:
        - id: The ID of the development category.
        - title_en: The English title of the category.
        - title_es: The Spanish title of the category.
        - description_en: The English description of the category.
        - description_es: The Spanish description of the category.
        - sections: The related sections within the category.
    """
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriesDevelopment
        fields = '__all__'
