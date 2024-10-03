from rest_framework import serializers
from content.models import Contact

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contact model.
    """
    class Meta:
        model = Contact
        fields = '__all__'
