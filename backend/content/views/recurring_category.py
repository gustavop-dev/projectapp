"""API views for the recurring-payment categories (panel, superuser-only).

Kept out of `views/accounting.py` — that module is the generic registry-driven
CRUD engine for the accounting records themselves, and this is a small
side catalog with its own delete guard and reorder endpoint. Mirrors
`views/document_folder.py`, the other user-editable catalog in the panel.
"""
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from content.api_errors import error_response
from content.models import RecurringCategory
from content.permissions import IsSuperUser
from content.serializers.accounting import RecurringCategorySerializer


@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_recurring_categories(request):
    categories = RecurringCategory.objects.annotate(
        payment_count_annotated=Count('payments'),
    )
    serializer = RecurringCategorySerializer(categories, many=True)
    # Same {'results': [...], 'meta': {...}} envelope as every other
    # accounting list, so the frontend store consumes it without a special case.
    return Response({'results': serializer.data, 'meta': {}})


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_recurring_category(request):
    serializer = RecurringCategorySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_recurring_category(request, category_id):
    category = get_object_or_404(RecurringCategory, pk=category_id)
    serializer = RecurringCategorySerializer(
        category, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def delete_recurring_category(request, category_id):
    category = get_object_or_404(RecurringCategory, pk=category_id)
    payment_count = category.payments.count()
    if payment_count:
        # The FK is PROTECT; answer with the reason instead of a 500.
        return Response(
            {
                'detail': (
                    f'La categoría tiene {payment_count} pago(s) recurrente(s). '
                    'Muévelos a otra categoría antes de borrarla.'
                ),
                'payment_count': payment_count,
            },
            status=status.HTTP_409_CONFLICT,
        )
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def reorder_recurring_categories(request):
    """Body: {"ids": [3, 1, 2]} — array position becomes the new order."""
    ids = request.data.get('ids', [])
    if not isinstance(ids, list):
        return error_response(
            'Debe ser una lista.',
            code='invalid_reorder_payload',
            status=status.HTTP_400_BAD_REQUEST,
        )
    categories_by_id = {c.id: c for c in RecurringCategory.objects.filter(pk__in=ids)}
    for order, category_id in enumerate(ids):
        category = categories_by_id.get(category_id)
        if category is not None:
            category.order = order
    RecurringCategory.objects.bulk_update(categories_by_id.values(), ['order'])
    return Response({'reordered': len(categories_by_id)})
