"""Serializers for the panel (accounting) view of collection accounts."""
from rest_framework import serializers

from content.models import Document, DocumentItem, DocumentPaymentMethod
from content.services.collection_account_service import commercial_is_overdue

STATUS_LABELS = {
    'draft': 'Borrador',
    'issued': 'Emitida',
    'paid': 'Pagada',
    'cancelled': 'Anulada',
}


class CollectionAccountPanelListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source='collection_account.customer_name', read_only=True, default='',
    )
    customer_email = serializers.CharField(
        source='collection_account.customer_email', read_only=True, default='',
    )
    billing_concept = serializers.CharField(
        source='collection_account.billing_concept', read_only=True, default='',
    )
    commercial_status_label = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    origin_label = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'public_number', 'title',
            'billing_concept', 'customer_name', 'customer_email',
            'origin', 'origin_label', 'hosting_record_id', 'project_id',
            'subtotal', 'tax_total', 'total', 'currency',
            'issue_date', 'due_date',
            'commercial_status', 'commercial_status_label', 'is_overdue',
            'created_at', 'updated_at',
        )

    def get_commercial_status_label(self, obj):
        return STATUS_LABELS.get(obj.commercial_status, obj.commercial_status)

    def get_is_overdue(self, obj):
        return commercial_is_overdue(obj)

    def get_origin(self, obj):
        if obj.hosting_record_id:
            return 'hosting'
        if obj.project_id:
            return 'project'
        return 'other'

    def get_origin_label(self, obj):
        if obj.hosting_record_id and obj.hosting_record:
            return f'Hosting · {obj.hosting_record.client_name}'
        if obj.project_id and obj.project:
            return f'Proyecto · {obj.project}'
        return 'Otro'


class _PanelItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentItem
        fields = (
            'id', 'position', 'item_type', 'description', 'quantity',
            'unit_price', 'discount_amount', 'tax_amount', 'line_total',
            'period_start', 'period_end',
        )


class _PanelPaymentMethodSerializer(serializers.ModelSerializer):
    payment_method_type_label = serializers.CharField(
        source='get_payment_method_type_display', read_only=True,
    )

    class Meta:
        model = DocumentPaymentMethod
        fields = (
            'id', 'payment_method_type', 'payment_method_type_label',
            'bank_name', 'account_type', 'account_number',
            'account_holder_name', 'payment_instructions', 'is_primary',
        )


class CollectionAccountPanelDetailSerializer(CollectionAccountPanelListSerializer):
    items = _PanelItemSerializer(many=True, read_only=True)
    payment_methods = _PanelPaymentMethodSerializer(many=True, read_only=True)

    class Meta(CollectionAccountPanelListSerializer.Meta):
        fields = CollectionAccountPanelListSerializer.Meta.fields + (
            'items', 'payment_methods', 'notes',
        )
