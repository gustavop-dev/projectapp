"""
JWT API views for the client-facing document portal (platform).

A client sees the documents linked to them (main contract flagged with
``requires_signature`` plus its annexes), can view/download each PDF, validate
their email via OTP, and sign the main document once their email is verified.
Every milestone (first login, email validated, signed) notifies the team.
"""
import logging

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import VerificationCode
from accounts.serializers import DocumentSignSerializer, EmailVerifyConfirmSerializer
from accounts.serializers_documents import ClientDocumentSerializer
from accounts.services.verification import create_and_send_otp, validate_otp
from content.models import Document
from content.services.document_pdf_service import DocumentPdfService
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.utils import get_client_ip

logger = logging.getLogger(__name__)


def _is_platform_admin(request):
    profile = getattr(request.user, 'profile', None)
    return profile is not None and profile.is_admin


def _visible_docs_qs(request):
    """Published portal documents visible to the requesting user.

    Excludes commercial collection accounts (those have their own portal).
    Admins see every published portal document; clients only their own.
    """
    qs = (
        Document.objects
        .filter(status=Document.Status.PUBLISHED)
        .exclude(document_type__code=COLLECTION_ACCOUNT)
        .select_related('document_type', 'project', 'client_user', 'signed_by')
    )
    if _is_platform_admin(request):
        return qs
    return qs.filter(
        Q(client_user=request.user) | Q(project__client=request.user),
    )


def _ordered_docs(qs):
    """Main signable document(s) first, then annexes by creation order."""
    return qs.order_by('-requires_signature', 'created_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_document_list_view(request):
    """List the client's portal documents plus their email-verification state."""
    docs = _ordered_docs(_visible_docs_qs(request))
    profile = getattr(request.user, 'profile', None)
    return Response({
        'email': request.user.email or '',
        'email_verified': bool(profile and profile.email_verified),
        'documents': ClientDocumentSerializer(docs, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_document_detail_view(request, doc_uuid):
    doc = _visible_docs_qs(request).filter(uuid=doc_uuid).first()
    if not doc:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(ClientDocumentSerializer(doc).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_document_pdf_view(request, doc_uuid):
    doc = _visible_docs_qs(request).filter(uuid=doc_uuid).first()
    if not doc:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    pdf_bytes = DocumentPdfService.generate(doc)
    if not pdf_bytes:
        return Response(
            {'detail': 'Failed to generate PDF.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    filename = slugify(doc.title) or 'document'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_document_sign_view(request, doc_uuid):
    """Client accepts/signs a document (click-to-accept). Requires a verified email."""
    doc = _visible_docs_qs(request).filter(uuid=doc_uuid).first()
    if not doc:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not doc.requires_signature:
        return Response(
            {'detail': 'Este documento no requiere firma.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile = getattr(request.user, 'profile', None)
    if not (profile and profile.email_verified):
        return Response(
            {'detail': 'Debes validar tu correo electrónico antes de firmar.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if doc.signed_at is not None:
        # Idempotent: already signed.
        return Response(ClientDocumentSerializer(doc).data)

    serializer = DocumentSignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    default_name = f'{request.user.first_name} {request.user.last_name}'.strip()
    doc.signed_at = timezone.now()
    doc.signed_by = request.user
    doc.signature_name = serializer.validated_data.get('signature_name') or default_name or request.user.email
    doc.signature_ip = get_client_ip(request)
    doc.signature_user_agent = request.META.get('HTTP_USER_AGENT', '')
    doc.save(update_fields=[
        'signed_at', 'signed_by', 'signature_name',
        'signature_ip', 'signature_user_agent', 'updated_at',
    ])

    from accounts.tasks import notify_team_document_signed_task

    notify_team_document_signed_task(doc.id)

    return Response(ClientDocumentSerializer(doc).data)


# ==========================================================================
# Email validation (OTP) — confirm ownership of the account email
# ==========================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def email_verify_request_view(request):
    """Send an OTP code to the authenticated client's current email."""
    profile = getattr(request.user, 'profile', None)
    if profile and profile.email_verified:
        return Response({'detail': 'Tu correo ya está validado.', 'email_verified': True})
    if not request.user.email:
        return Response(
            {'detail': 'No tienes un correo configurado. Contacta al administrador.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    create_and_send_otp(request.user, purpose=VerificationCode.PURPOSE_EMAIL_VALIDATION)
    return Response({'detail': 'Código enviado a tu correo.', 'email': request.user.email})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def email_verify_confirm_view(request):
    """Validate the OTP and mark the client's email as verified."""
    profile = getattr(request.user, 'profile', None)
    if profile and profile.email_verified:
        return Response({'detail': 'Tu correo ya está validado.', 'email_verified': True})

    serializer = EmailVerifyConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    success, error_msg = validate_otp(
        request.user,
        serializer.validated_data['code'],
        purpose=VerificationCode.PURPOSE_EMAIL_VALIDATION,
    )
    if not success:
        return Response({'detail': error_msg}, status=status.HTTP_400_BAD_REQUEST)

    profile.email_verified = True
    profile.email_verified_at = timezone.now()
    profile.save(update_fields=['email_verified', 'email_verified_at'])

    from accounts.tasks import notify_team_email_validated_task

    notify_team_email_validated_task(request.user.id)

    return Response({'detail': 'Correo validado correctamente.', 'email_verified': True})
