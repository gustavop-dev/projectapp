from rest_framework.response import Response
from rest_framework import status
from content.models import Contact
from content.serializers.contact import ContactSerializer
from rest_framework.decorators import api_view
from content.utils import send_whatsapp_notification

@api_view(['GET'])
def contact_list(request):
    """
    API view to retrieve a list of Contact messages.
    """
    contacts = Contact.objects.all()
    serializer = ContactSerializer(contacts, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def new_contact(request):
    """
    API view to create a new Contact message.
    """
    serializer = ContactSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        contact = serializer.save()
        
        # Create a message for WhatsApp notification
        email = contact.email
        subject = contact.subject
        message = contact.message
        
        whatsapp_message = f"New contact message:\nEmail: {email}\nSubject: {subject}\nMessage: {message}"
        
        # Send WhatsApp notification
        send_whatsapp_notification(whatsapp_message)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
