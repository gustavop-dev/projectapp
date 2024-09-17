from rest_framework.response import Response
from rest_framework import status
from content.models import Contact
from content.serializers.contact import ContactSerializer
from rest_framework.decorators import api_view

@api_view(['GET'])
def contact_list(request):
    """
    API view to retrieve a list of Contact messages.
    """
    contacts = Contact.objects.all()
    serializer = ContactSerializer(contacts, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
