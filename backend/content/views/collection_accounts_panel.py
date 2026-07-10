"""Panel (accounting) endpoints for collection accounts — superuser only.

The platform (JWT) side has its own per-project views in
accounts/collection_account_views.py; these serve the accounting "Cobros"
monitor and the hosting "Enviar cuenta de cobro" action (session + CSRF).
"""
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from content.api_errors import error_response
from content.models import Document, HostingRecord
from content.permissions import IsSuperUser
from content.serializers.collection_accounts_panel import (
    CollectionAccountPanelDetailSerializer,
    CollectionAccountPanelListSerializer,
)
from content.services import hosting_billing_service
from content.services.collection_account_pdf_service import (
    CollectionAccountPdfService,
)
from content.services.collection_account_service import (
    CollectionAccountError,
    mark_collection_account_cancelled,
    mark_collection_account_paid,
)
from content.services.document_type_codes import COLLECTION_ACCOUNT


def _base_qs():
    return (
        Document.objects.filter(document_type__code=COLLECTION_ACCOUNT)
        .select_related('collection_account', 'hosting_record', 'project')
        .prefetch_related('items', 'payment_methods')
    )


def _get_document(doc_id):
    return get_object_or_404(_base_qs(), pk=doc_id)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def send_hosting_collection_account(request, record_id):
    hosting = get_object_or_404(HostingRecord, pk=record_id)
    try:
        result = hosting_billing_service.send_hosting_collection_account(
            hosting, acting_user=request.user,
        )
    except hosting_billing_service.HostingBillingError as exc:
        return error_response(str(exc))
    document = _get_document(result['document'].pk)
    return Response(
        {
            'document': CollectionAccountPanelDetailSerializer(document).data,
            'email_sent': result['email_sent'],
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_collection_accounts(request):
    qs = _base_qs().order_by('-created_at')
    params = request.query_params

    commercial_status = params.get('commercial_status')
    if commercial_status:
        qs = qs.filter(commercial_status=commercial_status)
    origin = params.get('origin')
    if origin == 'hosting':
        qs = qs.filter(hosting_record__isnull=False)
    elif origin == 'project':
        qs = qs.filter(project__isnull=False)
    elif origin == 'other':
        qs = qs.filter(hosting_record__isnull=True, project__isnull=True)
    for param, lookup in (
        ('date_from', 'issue_date__gte'),
        ('date_to', 'issue_date__lte'),
    ):
        value = params.get(param)
        if value:
            try:
                qs = qs.filter(**{lookup: date.fromisoformat(value)})
            except ValueError:
                return error_response(
                    f"El parámetro '{param}' debe ser una fecha AAAA-MM-DD.",
                )
    search = (params.get('q') or '').strip()
    if search:
        qs = qs.filter(
            Q(public_number__icontains=search)
            | Q(title__icontains=search)
            | Q(collection_account__customer_name__icontains=search),
        )

    totals = qs.aggregate(
        draft_count=Count('id', filter=Q(commercial_status='draft')),
        issued_count=Count('id', filter=Q(commercial_status='issued')),
        paid_count=Count('id', filter=Q(commercial_status='paid')),
        cancelled_count=Count('id', filter=Q(commercial_status='cancelled')),
        issued_total=Sum('total', filter=Q(commercial_status='issued')),
        paid_total=Sum('total', filter=Q(commercial_status='paid')),
    )
    two_places = Decimal('0.01')
    meta = {
        key: (
            str((value or Decimal('0')).quantize(two_places))
            if key.endswith('_total')
            else value or 0
        )
        for key, value in totals.items()
    }
    serializer = CollectionAccountPanelListSerializer(qs, many=True)
    return Response({'results': serializer.data, 'meta': meta})


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_collection_account(request, doc_id):
    document = _get_document(doc_id)
    return Response(CollectionAccountPanelDetailSerializer(document).data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def collection_account_pdf(request, doc_id):
    document = _get_document(doc_id)
    pdf_bytes = CollectionAccountPdfService.generate(document)
    if not pdf_bytes:
        return error_response('No se pudo generar el PDF.', status=500)
    filename = f'{document.public_number or document.pk}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view(['POST'])
@permission_classes([IsSuperUser])
def resend_collection_account(request, doc_id):
    document = _get_document(doc_id)
    try:
        sent = hosting_billing_service.resend_collection_account_email(
            document, acting_user=request.user,
        )
    except hosting_billing_service.HostingBillingError as exc:
        return error_response(str(exc))
    if not sent:
        return error_response(
            'No se pudo enviar el correo; revisa los logs e inténtalo de nuevo.',
            status=502,
        )
    return Response({'email_sent': True})


@api_view(['POST'])
@permission_classes([IsSuperUser])
def mark_collection_account_paid_view(request, doc_id):
    document = _get_document(doc_id)
    try:
        mark_collection_account_paid(document, acting_user=request.user)
    except CollectionAccountError as exc:
        return error_response(str(exc))
    return Response(CollectionAccountPanelDetailSerializer(document).data)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def cancel_collection_account_view(request, doc_id):
    document = _get_document(doc_id)
    try:
        mark_collection_account_cancelled(document, acting_user=request.user)
    except CollectionAccountError as exc:
        return error_response(str(exc))
    # Cancelling the current period's cuenta de cobro resumes the expiry
    # notice cadence for the linked hosting.
    hosting = document.hosting_record
    if hosting is not None and hosting.billing_requested_at is not None:
        HostingRecord.objects.filter(pk=hosting.pk).update(
            billing_requested_at=None,
        )
    return Response(CollectionAccountPanelDetailSerializer(document).data)
