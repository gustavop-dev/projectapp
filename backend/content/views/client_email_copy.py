"""Admin configuration for BCC copies of outbound client email."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.email_copy_families import CLIENT_EMAIL_FAMILY_CHOICES
from content.models import ClientEmailCopyRecipient
from content.serializers.client_email_copy import (
    ClientEmailCopyRecipientSerializer,
)


def _family_options():
    return [
        {'value': value, 'label': label}
        for value, label in CLIENT_EMAIL_FAMILY_CHOICES
    ]


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def client_email_copy_recipients(request):
    if request.method == 'GET':
        recipients = ClientEmailCopyRecipient.objects.all()
        return Response({
            'results': ClientEmailCopyRecipientSerializer(
                recipients, many=True,
            ).data,
            'families': _family_options(),
            'copy_mode': 'bcc',
        })

    serializer = ClientEmailCopyRecipientSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def client_email_copy_recipient_detail(request, recipient_id):
    recipient = get_object_or_404(ClientEmailCopyRecipient, pk=recipient_id)
    if request.method == 'DELETE':
        recipient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ClientEmailCopyRecipientSerializer(
        recipient, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)

