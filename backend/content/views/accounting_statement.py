"""API views for credit-card statements (extractos) — panel, superuser-only.

Statement CRUD reuses the generic accounting handlers (audit + email);
transactions and merchant aliases route through accounting_statement_service
so their audit rows stay silent (no per-line emails).
"""
from pathlib import Path

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from content.api_errors import error_response, error_response_from_exc
from content.models import CreditCardStatement, CreditCardTransaction, MerchantAlias
from content.permissions import IsSuperUser
from content.serializers.accounting_statement import (
    CreditCardStatementDetailSerializer,
    CreditCardStatementWriteSerializer,
    CreditCardTransactionSerializer,
    CreditCardTransactionWriteSerializer,
    MerchantAliasSerializer,
    MerchantAliasWriteSerializer,
)
from content.services import accounting_statement_service
from content.utils import today_bogota
from content.views.accounting import (
    _delete_record,
    _list_records,
    _update_record,
)


# ── Statements ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_statements(request):
    return _list_records(request, 'statement')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_statement(request):
    """Create a DRAFT statement with its transactions in one atomic call."""
    transactions_data = request.data.get('transactions', [])
    if not isinstance(transactions_data, list):
        return error_response("El campo 'transactions' debe ser una lista.")
    header = {
        key: value for key, value in request.data.items()
        if key != 'transactions'
    }
    statement_serializer = CreditCardStatementWriteSerializer(data=header)
    transactions_serializer = CreditCardTransactionWriteSerializer(
        data=transactions_data, many=True,
    )
    errors = {}
    if not statement_serializer.is_valid():
        errors.update(statement_serializer.errors)
    if not transactions_serializer.is_valid():
        errors['transactions'] = transactions_serializer.errors
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        statement = accounting_statement_service.create_statement_with_transactions(
            statement_serializer, transactions_serializer, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(
        CreditCardStatementDetailSerializer(statement).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsSuperUser])
def statements_status(request):
    """12-month processed/draft/pending grid for one year."""
    year_param = request.query_params.get('year') or ''
    try:
        year = int(year_param) if year_param else today_bogota().year
    except (TypeError, ValueError):
        return error_response("El parámetro 'year' debe ser un año válido.")
    card_name = request.query_params.get('card_name') or None
    return Response(
        accounting_statement_service.statement_month_status(year, card_name),
    )


@api_view(['GET'])
@permission_classes([IsSuperUser])
def retrieve_statement(request, record_id):
    statement = get_object_or_404(CreditCardStatement, pk=record_id)
    return Response(CreditCardStatementDetailSerializer(statement).data)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_statement(request, record_id):
    return _update_record(request, 'statement', record_id)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_statement(request, record_id):
    return _delete_record(request, 'statement', record_id)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def finalize_statement(request, record_id):
    statement = get_object_or_404(CreditCardStatement, pk=record_id)
    force = bool(request.data.get('force'))
    try:
        statement = accounting_statement_service.finalize_statement(
            statement, request.user, force=force,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(CreditCardStatementDetailSerializer(statement).data)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def reopen_statement(request, record_id):
    statement = get_object_or_404(CreditCardStatement, pk=record_id)
    try:
        statement = accounting_statement_service.reopen_statement(
            statement, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(CreditCardStatementDetailSerializer(statement).data)


# ── Statement PDF (bank document kept as documentation) ──

_PDF_MAX_SIZE = 15 * 1024 * 1024  # 15 MB


@api_view(['POST'])
@permission_classes([IsSuperUser])
@parser_classes([MultiPartParser])
def upload_statement_pdf(request, record_id):
    statement = get_object_or_404(CreditCardStatement, pk=record_id)
    file = request.FILES.get('file')
    if not file:
        return error_response(
            'No se adjuntó ningún archivo.',
            code='statement_pdf_required',
        )
    if Path(file.name).suffix.lower() != '.pdf':
        return error_response(
            'El extracto debe adjuntarse en formato PDF.',
            code='statement_pdf_type_not_allowed',
        )
    if file.size > _PDF_MAX_SIZE:
        return error_response(
            'El archivo es demasiado grande. El tamaño máximo es 15 MB.',
            code='statement_pdf_too_large',
        )
    try:
        statement = accounting_statement_service.attach_statement_pdf(
            statement, file, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(CreditCardStatementDetailSerializer(statement).data)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_statement_pdf(request, record_id):
    statement = get_object_or_404(CreditCardStatement, pk=record_id)
    if not statement.pdf_file:
        return error_response(
            'El extracto no tiene un PDF adjunto.',
            code='statement_pdf_missing',
        )
    statement = accounting_statement_service.remove_statement_pdf(
        statement, request.user,
    )
    return Response(CreditCardStatementDetailSerializer(statement).data)


# ── Transactions ──

@api_view(['POST'])
@permission_classes([IsSuperUser])
def batch_create_transactions(request, record_id):
    """Append transactions to a DRAFT statement (all-or-nothing)."""
    statement = get_object_or_404(CreditCardStatement, pk=record_id)
    transactions_data = request.data.get('transactions', [])
    if not isinstance(transactions_data, list) or not transactions_data:
        return error_response(
            "El campo 'transactions' debe ser una lista con al menos una "
            'transacción.'
        )
    serializer = CreditCardTransactionWriteSerializer(
        data=transactions_data, many=True,
    )
    if not serializer.is_valid():
        return Response(
            {'transactions': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        transactions = accounting_statement_service.add_transactions(
            statement, serializer, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(
        CreditCardTransactionSerializer(transactions, many=True).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_statement_transaction(request, record_id, tx_id):
    tx = get_object_or_404(
        CreditCardTransaction, pk=tx_id, statement_id=record_id,
    )
    serializer = CreditCardTransactionWriteSerializer(
        tx, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        tx = accounting_statement_service.update_transaction(
            tx, serializer, request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(CreditCardTransactionSerializer(tx).data)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_statement_transaction(request, record_id, tx_id):
    tx = get_object_or_404(
        CreditCardTransaction, pk=tx_id, statement_id=record_id,
    )
    try:
        accounting_statement_service.delete_transaction(tx, request.user)
    except ValueError as exc:
        return error_response_from_exc(exc)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Merchant aliases ──

@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_merchant_aliases(request):
    return _list_records(request, 'merchant_alias')


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_merchant_alias(request):
    serializer = MerchantAliasWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = accounting_statement_service.save_merchant_aliases(
            [{
                'match_text': serializer.validated_data['match_text'],
                'merchant_name': serializer.validated_data['merchant_name'],
                'category': serializer.validated_data.get('default_category'),
                'is_gateway': serializer.validated_data.get(
                    'is_gateway', False,
                ),
            }],
            request.user,
        )
    except ValueError as exc:
        return error_response_from_exc(exc)
    alias = result['aliases'][0]
    return Response(
        MerchantAliasSerializer(alias).data, status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([IsSuperUser])
def resolve_merchant_aliases(request):
    raw_descriptions = request.data.get('raw_descriptions', [])
    if not isinstance(raw_descriptions, list):
        return error_response(
            "El campo 'raw_descriptions' debe ser una lista de textos."
        )
    return Response(
        accounting_statement_service.resolve_merchants(raw_descriptions),
    )


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_merchant_alias(request, record_id):
    alias = get_object_or_404(MerchantAlias, pk=record_id)
    serializer = MerchantAliasWriteSerializer(
        alias, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    alias = accounting_statement_service.update_merchant_alias(
        alias, serializer, request.user,
    )
    return Response(MerchantAliasSerializer(alias).data)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_merchant_alias(request, record_id):
    alias = get_object_or_404(MerchantAlias, pk=record_id)
    accounting_statement_service.delete_merchant_alias(alias, request.user)
    return Response(status=status.HTTP_204_NO_CONTENT)
