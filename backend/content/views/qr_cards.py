from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from content.models import QRCard
from content.serializers.qr_cards import QRCardListSerializer, QRCardCreateUpdateSerializer


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_qr_cards(request):
    """List all QR cards for admin management."""
    qs = QRCard.objects.all()
    serializer = QRCardListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_qr_card(request):
    """Create a new QR card."""
    serializer = QRCardCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    card = serializer.save()
    detail = QRCardListSerializer(card)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_qr_card(request, card_id):
    """Update a QR card's name, destination_url and/or is_active."""
    card = get_object_or_404(QRCard, pk=card_id)
    serializer = QRCardCreateUpdateSerializer(card, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    detail = QRCardListSerializer(card)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_qr_card(request, card_id):
    """Delete a QR card."""
    card = get_object_or_404(QRCard, pk=card_id)
    card.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Public redirect endpoint (registered as a top-level route — see
# projectapp/urls.py — so the short link reads as /t/<uuid>/, not /api/t/<uuid>/)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def qr_card_redirect(request, card_id):
    """Resolve a QR card's UUID to its configured destination and redirect."""
    card = get_object_or_404(QRCard, pk=card_id)
    if not card.is_active:
        return HttpResponse(
            'Este enlace no está disponible.', content_type='text/plain; charset=utf-8'
        )
    if not card.destination_url:
        return HttpResponse(
            'Este enlace aún no ha sido configurado.', content_type='text/plain; charset=utf-8'
        )
    return HttpResponseRedirect(card.destination_url)
