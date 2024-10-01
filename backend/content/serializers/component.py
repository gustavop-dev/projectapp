from rest_framework import serializers
from content.models import Example, Component, Section, UISectionCategory

class ExampleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Example model, including the image URL.
    """

    class Meta:
        model = Example
        fields = '__all__'

class ComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Component model, including the related examples and image URL.
    """
    examples = ExampleSerializer(many=True, read_only=True)

    class Meta:
        model = Component
        fields = '__all__'

class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Section model, including the related components.
    """
    components = ComponentSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = '__all__'


class UISectionCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the UISectionCategory model, including the related sections.
    """
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = UISectionCategory
        fields = '__all__'
