"""Serializers for the accounting module (panel, superuser-only).

Write serializers apply the default 50/50 partner split when neither
partner amount is supplied on create, and accept month periods as
"YYYY-MM" (normalized to the first day of the month).
"""
import re
from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers

from content.utils import SPANISH_MONTHS
from content.models import (
    AccountingChangeLog,
    AccountingSettings,
    AdsSpendRecord,
    CardBalanceSnapshot,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    Ledger,
    PocketMovement,
    RecurringPayment,
)

PERSONAL_LEDGER_OWNER = {
    Ledger.GUSTAVO: ('gustavo_amount', 'carlos_amount'),
    Ledger.CARLOS: ('carlos_amount', 'gustavo_amount'),
}

MONTH_PERIOD_RE = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')

TWO_PLACES = Decimal('0.01')


def month_period(date_value):
    """Return the 'YYYY-MM' representation of a date."""
    return date_value.strftime('%Y-%m') if date_value else None


def month_label(date_value):
    """Return the Spanish 'Mes YYYY' label of a date."""
    if not date_value:
        return ''
    return f'{SPANISH_MONTHS[date_value.month].capitalize()} {date_value.year}'


def split_half(total):
    """50/50 split; the odd cent goes deterministically to Carlos."""
    gustavo = (total / 2).quantize(TWO_PLACES, rounding=ROUND_DOWN)
    return gustavo, total - gustavo


class MonthPeriodField(serializers.DateField):
    """DateField accepting 'YYYY-MM' too; always normalized to day 1."""

    def to_internal_value(self, value):
        if isinstance(value, str) and MONTH_PERIOD_RE.match(value.strip()):
            value = f'{value.strip()}-01'
        date_value = super().to_internal_value(value)
        return date_value.replace(day=1)


class PeriodReadMixin(serializers.Serializer):
    period = serializers.SerializerMethodField()
    period_label = serializers.SerializerMethodField()

    def get_period(self, obj):
        return month_period(obj.period_date)

    def get_period_label(self, obj):
        return month_label(obj.period_date)


class PartnerSplitWriteMixin(serializers.Serializer):
    """Split fields + validation shared by income/expense write serializers.

    Company records keep the 50/50 default split. Personal-ledger records
    always belong 100% to their owner: any split sent by the client is
    normalized instead of rejected.
    """

    total_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
    )
    gustavo_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
        required=False,
    )
    carlos_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
        required=False,
    )
    ledger = serializers.ChoiceField(choices=Ledger.choices, required=False)

    def validate(self, data):
        data = super().validate(data)

        def effective(field, default=None):
            if field in data:
                return data[field]
            if self.instance is not None:
                return getattr(self.instance, field)
            return default

        total = effective('total_amount')
        ledger = effective('ledger', Ledger.COMPANY)

        if ledger in PERSONAL_LEDGER_OWNER:
            if total is not None:
                owner_field, other_field = PERSONAL_LEDGER_OWNER[ledger]
                data[owner_field] = total
                data[other_field] = Decimal('0')
            return data

        split_provided = 'gustavo_amount' in data or 'carlos_amount' in data
        if self.instance is None and not split_provided and total is not None:
            gustavo, carlos = split_half(total)
            data['gustavo_amount'] = gustavo
            data['carlos_amount'] = carlos

        gustavo = effective('gustavo_amount', Decimal('0')) or Decimal('0')
        carlos = effective('carlos_amount', Decimal('0')) or Decimal('0')
        if total is not None and gustavo + carlos > total:
            raise serializers.ValidationError(
                'La suma de los montos de los socios no puede superar el monto total.'
            )
        return data


# ── Income ──

class IncomeRecordSerializer(PeriodReadMixin, serializers.ModelSerializer):
    kind_label = serializers.CharField(source='get_kind_display', read_only=True)
    destination_label = serializers.CharField(
        source='get_destination_display', read_only=True,
    )
    ledger_label = serializers.CharField(
        source='get_ledger_display', read_only=True,
    )
    company_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True,
    )

    class Meta:
        model = IncomeRecord
        fields = (
            'id', 'concept', 'kind', 'kind_label',
            'period', 'period_label', 'period_date',
            'destination', 'destination_label', 'ledger', 'ledger_label',
            'total_amount', 'gustavo_amount', 'carlos_amount', 'company_amount',
            'expected_income', 'pocket_movement',
            'notes', 'created_at', 'updated_at',
        )


class IncomeRecordCreateUpdateSerializer(
    PartnerSplitWriteMixin, serializers.ModelSerializer,
):
    period_date = MonthPeriodField()
    expected_income = serializers.PrimaryKeyRelatedField(
        queryset=IncomeRecord.objects.filter(kind=IncomeRecord.Kind.EXPECTED),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = IncomeRecord
        fields = (
            'concept', 'kind', 'period_date', 'destination', 'ledger',
            'total_amount', 'gustavo_amount', 'carlos_amount',
            'expected_income', 'notes',
        )

    def validate(self, data):
        data = super().validate(data)

        def effective(field, default=None):
            if field in data:
                return data[field]
            if self.instance is not None:
                return getattr(self.instance, field)
            return default

        kind = effective('kind')
        destination = effective('destination')
        ledger = effective('ledger', Ledger.COMPANY)
        if (
            destination == IncomeRecord.Destination.POCKET
            and kind != IncomeRecord.Kind.LIQUID
        ):
            raise serializers.ValidationError(
                'El destino Bolsillo ProjectApp solo aplica a ingresos líquidos.'
            )
        if (
            ledger != Ledger.COMPANY
            and destination == IncomeRecord.Destination.POCKET
        ):
            raise serializers.ValidationError(
                'Los movimientos personales no pueden ir al Bolsillo ProjectApp.'
            )
        expected = effective('expected_income')
        if expected is not None and expected.ledger != ledger:
            raise serializers.ValidationError(
                'El ingreso esperado vinculado debe ser de la misma contabilidad.'
            )
        return data


# ── Expense ──

class ExpenseRecordSerializer(PeriodReadMixin, serializers.ModelSerializer):
    category_label = serializers.CharField(
        source='get_category_display', read_only=True,
    )
    ledger_label = serializers.CharField(
        source='get_ledger_display', read_only=True,
    )
    company_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True,
    )

    class Meta:
        model = ExpenseRecord
        fields = (
            'id', 'concept',
            'period', 'period_label', 'period_date',
            'category', 'category_label',
            'ledger', 'ledger_label',
            'total_amount', 'gustavo_amount', 'carlos_amount', 'company_amount',
            'notes', 'created_at', 'updated_at',
        )


class ExpenseRecordCreateUpdateSerializer(
    PartnerSplitWriteMixin, serializers.ModelSerializer,
):
    period_date = MonthPeriodField()

    class Meta:
        model = ExpenseRecord
        fields = (
            'concept', 'period_date', 'category', 'ledger',
            'total_amount', 'gustavo_amount', 'carlos_amount', 'notes',
        )


# ── Hosting ──

class HostingRecordSerializer(serializers.ModelSerializer):
    payment_modality_label = serializers.CharField(
        source='get_payment_modality_display', read_only=True,
    )

    class Meta:
        model = HostingRecord
        fields = (
            'id', 'client_name', 'domain_url', 'monthly_value',
            'payment_modality', 'payment_modality_label', 'benefit',
            'valid_from', 'valid_to', 'cycles_count',
            'payment_per_cycle', 'total_paid', 'is_active',
            'notes', 'created_at', 'updated_at',
        )


class HostingRecordCreateUpdateSerializer(serializers.ModelSerializer):
    monthly_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
    )

    class Meta:
        model = HostingRecord
        fields = (
            'client_name', 'domain_url', 'monthly_value',
            'payment_modality', 'benefit', 'valid_from', 'valid_to',
            'cycles_count', 'payment_per_cycle', 'total_paid',
            'is_active', 'notes',
        )

    def validate(self, data):
        data = super().validate(data)

        def effective(field):
            if field in data:
                return data[field]
            return getattr(self.instance, field, None)

        valid_from = effective('valid_from')
        valid_to = effective('valid_to')
        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError(
                'La fecha de fin de vigencia no puede ser anterior al inicio.'
            )

        # Default the per-cycle payment from the modality on create.
        if self.instance is None and 'payment_per_cycle' not in data:
            monthly = data.get('monthly_value')
            modality = data.get(
                'payment_modality', HostingRecord.Modality.MONTHLY,
            )
            if monthly is not None:
                months = HostingRecord.MODALITY_MONTHS.get(modality, 1)
                data['payment_per_cycle'] = (monthly * months).quantize(
                    TWO_PLACES,
                )
        return data


# ── Pocket ──

class PocketMovementSerializer(serializers.ModelSerializer):
    direction_label = serializers.CharField(
        source='get_direction_display', read_only=True,
    )
    is_auto_managed = serializers.ReadOnlyField()

    class Meta:
        model = PocketMovement
        fields = (
            'id', 'concept', 'movement_date',
            'direction', 'direction_label', 'amount', 'is_auto_managed',
            'notes', 'created_at', 'updated_at',
        )


class PocketMovementCreateUpdateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0.01'),
    )

    class Meta:
        model = PocketMovement
        fields = ('concept', 'movement_date', 'direction', 'amount', 'notes')


# ── Recurring payments ──

class RecurringPaymentSerializer(serializers.ModelSerializer):
    payment_method_label = serializers.CharField(
        source='get_payment_method_display', read_only=True,
    )
    frequency_label = serializers.CharField(
        source='get_frequency_display', read_only=True,
    )
    cost_type_label = serializers.CharField(
        source='get_cost_type_display', read_only=True,
    )
    monthly_cop_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True,
    )

    class Meta:
        model = RecurringPayment
        fields = (
            'id', 'name', 'price', 'currency', 'cop_equivalent',
            'payment_method', 'payment_method_label',
            'frequency', 'frequency_label', 'billing_day',
            'cost_type', 'cost_type_label', 'monthly_cop_cost',
            'is_active', 'notes', 'created_at', 'updated_at',
        )


class RecurringPaymentCreateUpdateSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
    )

    class Meta:
        model = RecurringPayment
        fields = (
            'name', 'price', 'currency', 'cop_equivalent',
            'payment_method', 'frequency', 'billing_day',
            'cost_type', 'is_active', 'notes',
        )

    def validate(self, data):
        data = super().validate(data)
        # COP payments default their COP equivalent to the price itself.
        if self.instance is None and 'cop_equivalent' not in data:
            currency = data.get('currency', RecurringPayment.Currency.COP)
            if currency == RecurringPayment.Currency.COP:
                data['cop_equivalent'] = data.get('price', Decimal('0'))
        return data


# ── Ads ──

class AdsSpendRecordSerializer(serializers.ModelSerializer):
    platform_label = serializers.CharField(
        source='get_platform_display', read_only=True,
    )
    accumulated = serializers.SerializerMethodField()

    class Meta:
        model = AdsSpendRecord
        fields = (
            'id', 'spend_date', 'platform', 'platform_label',
            'origin_card', 'amount', 'accumulated',
            'notes', 'created_at', 'updated_at',
        )

    def get_accumulated(self, obj):
        # Set by accounting_service.ads_with_accumulated; absent on writes.
        value = getattr(obj, 'accumulated', None)
        return str(value) if value is not None else None


class AdsSpendRecordCreateUpdateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
    )

    class Meta:
        model = AdsSpendRecord
        fields = ('spend_date', 'platform', 'origin_card', 'amount', 'notes')


# ── Card snapshots ──

class CardBalanceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardBalanceSnapshot
        fields = (
            'id', 'snapshot_date', 'card_name',
            'available_amount', 'debt_amount',
            'notes', 'created_at', 'updated_at',
        )


class CardBalanceSnapshotCreateUpdateSerializer(serializers.ModelSerializer):
    available_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
    )
    debt_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0'),
    )

    class Meta:
        model = CardBalanceSnapshot
        fields = (
            'snapshot_date', 'card_name',
            'available_amount', 'debt_amount', 'notes',
        )


# ── Change log & settings ──

class AccountingChangeLogSerializer(serializers.ModelSerializer):
    entity_type_label = serializers.CharField(
        source='get_entity_type_display', read_only=True,
    )
    action_label = serializers.CharField(
        source='get_action_display', read_only=True,
    )

    class Meta:
        model = AccountingChangeLog
        fields = (
            'id', 'entity_type', 'entity_type_label',
            'object_id', 'object_repr', 'action', 'action_label',
            'changes', 'actor', 'actor_username', 'created_at',
        )


class AccountingSettingsSerializer(serializers.ModelSerializer):
    notification_recipients = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=True,
        required=False,
    )
    usd_exchange_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal('1'),
        required=False,
    )

    class Meta:
        model = AccountingSettings
        fields = (
            'notification_recipients', 'notifications_enabled',
            'card_reminder_enabled', 'usd_exchange_rate', 'updated_at',
        )
