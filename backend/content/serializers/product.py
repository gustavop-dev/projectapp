from rest_framework import serializers
from content.models import Product, Category, Item

class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the Item model.
    """
    class Meta:
        model = Item
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model, including related items.
    """
    items = ItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model, including related categories.
    """
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
