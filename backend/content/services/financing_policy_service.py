"""Versioned commercial policy for the financing program."""

from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction

from content.models import AccountingSettings, FinancingPolicyRevision


DEFAULT_MINIMUM_PROJECT_VALUE_COP = Decimal('20000000.00')
DEFAULT_MAXIMUM_PROJECT_VALUE_COP = Decimal('140000000.00')
DEFAULT_FINANCING_MONTHS = 12
DEFAULT_MAXIMUM_FINANCED_PERCENT = Decimal('80.00')
DEFAULT_LATE_HOSTING_INCREASE_PERCENT = Decimal('2.00')
DEFAULT_INSTALLMENT_DUE_DAY_START = 1
DEFAULT_INSTALLMENT_DUE_DAY_END = 5


class FinancingPolicyValidationError(ValueError):
    def __init__(self, errors, *, code='invalid_financing_policy'):
        self.errors = errors
        self.code = code
        super().__init__(str(errors))


def current_policy():
    policy = FinancingPolicyRevision.get_current()
    if policy is None:
        raise FinancingPolicyValidationError({
            'policy_revision': [
                'No existe una política de financiación configurada.',
            ],
        }, code='financing_policy_missing')
    return policy


def minimum_initial_payment_percent(policy):
    return (Decimal('100.00') - policy.maximum_financed_percent).quantize(
        Decimal('0.01'),
    )


def validate_policy_values(values):
    errors = {}
    minimum = Decimal(str(values['minimum_project_value_cop']))
    maximum = Decimal(str(values['maximum_project_value_cop']))
    months = int(values['financing_months'])
    financed_percent = Decimal(str(values['maximum_financed_percent']))
    hosting_percent = Decimal(str(values['late_hosting_increase_percent']))
    due_start = int(values['installment_due_day_start'])
    due_end = int(values['installment_due_day_end'])

    if minimum <= 0:
        errors['minimum_project_value_cop'] = [
            'El valor mínimo debe ser mayor que cero.',
        ]
    if maximum <= minimum:
        errors['maximum_project_value_cop'] = [
            'El valor máximo debe ser mayor que el valor mínimo.',
        ]
    if not 1 <= months <= 36:
        errors['financing_months'] = [
            'El plazo debe estar entre 1 y 36 meses.',
        ]
    if not Decimal('1.00') <= financed_percent <= Decimal('99.00'):
        errors['maximum_financed_percent'] = [
            'El porcentaje financiable debe estar entre 1% y 99%.',
        ]
    if not Decimal('0.00') <= hosting_percent <= Decimal('100.00'):
        errors['late_hosting_increase_percent'] = [
            'El aumento del Hosting debe estar entre 0% y 100%.',
        ]
    if not 1 <= due_start <= 28:
        errors['installment_due_day_start'] = [
            'El primer día permitido debe estar entre 1 y 28.',
        ]
    if not due_start <= due_end <= 28:
        errors['installment_due_day_end'] = [
            'El último día debe estar entre el día inicial y el día 28.',
        ]
    if errors:
        raise FinancingPolicyValidationError(errors)


@transaction.atomic
def create_policy_revision(validated_data, *, actor):
    latest = FinancingPolicyRevision.objects.select_for_update().order_by(
        '-version',
    ).first()
    values = dict(validated_data)
    validate_policy_values(values)
    if latest and all(
        getattr(latest, field) == value
        for field, value in values.items()
    ):
        raise FinancingPolicyValidationError({
            'non_field_errors': [
                'Modifica al menos una condición antes de publicar una revisión.',
            ],
        }, code='financing_policy_unchanged')
    try:
        return FinancingPolicyRevision.objects.create(
            version=(latest.version + 1) if latest else 1,
            created_by=actor,
            **values,
        )
    except IntegrityError as exc:
        raise FinancingPolicyValidationError({
            'non_field_errors': [
                'Otra revisión fue publicada al mismo tiempo. Recarga e inténtalo de nuevo.',
            ],
        }, code='financing_policy_conflict') from exc


def eligibility_exchange_rate(currency):
    if currency == 'COP':
        return None
    rate = AccountingSettings.load().usd_exchange_rate
    if rate is None or rate <= 0:
        raise FinancingPolicyValidationError({
            'currency': [
                'Configura una tasa USD/COP válida en Contabilidad antes de usar USD.',
            ],
        }, code='financing_exchange_rate_missing')
    return Decimal(str(rate)).quantize(Decimal('0.01'))


def equivalent_total_cop(total_value, currency, exchange_rate):
    try:
        total = Decimal(str(total_value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FinancingPolicyValidationError({
            'total_value': ['El valor total no es válido.'],
        }) from exc
    if currency == 'COP':
        return total
    if exchange_rate is None or Decimal(str(exchange_rate)) <= 0:
        raise FinancingPolicyValidationError({
            'eligibility_exchange_rate': [
                'El acuerdo en USD necesita una tasa USD/COP congelada.',
            ],
        })
    return (total * Decimal(str(exchange_rate))).quantize(Decimal('0.01'))


def validate_agreement_financials(
    *,
    total_value,
    initial_payment,
    currency,
    exchange_rate,
    policy,
):
    total = Decimal(str(total_value)).quantize(Decimal('0.01'))
    initial = Decimal(str(initial_payment)).quantize(Decimal('0.01'))
    total_cop = equivalent_total_cop(total, currency, exchange_rate)
    errors = {}
    if total_cop < policy.minimum_project_value_cop:
        errors['total_value'] = [
            'El valor total del alcance está por debajo del mínimo de la política.',
        ]
    if total_cop > policy.maximum_project_value_cop:
        errors['total_value'] = [
            'El valor total del alcance supera el máximo de la política.',
        ]
    minimum_percent = minimum_initial_payment_percent(policy)
    if initial * Decimal('100.00') < total * minimum_percent:
        errors['initial_payment'] = [
            f'El aporte inicial debe ser como mínimo el {minimum_percent}% '
            'del valor total.',
        ]
    if errors:
        raise FinancingPolicyValidationError(errors)
    return total_cop


def policy_defaults():
    return {
        'minimum_project_value_cop': DEFAULT_MINIMUM_PROJECT_VALUE_COP,
        'maximum_project_value_cop': DEFAULT_MAXIMUM_PROJECT_VALUE_COP,
        'financing_months': DEFAULT_FINANCING_MONTHS,
        'maximum_financed_percent': DEFAULT_MAXIMUM_FINANCED_PERCENT,
        'late_hosting_increase_percent': DEFAULT_LATE_HOSTING_INCREASE_PERCENT,
        'installment_due_day_start': DEFAULT_INSTALLMENT_DUE_DAY_START,
        'installment_due_day_end': DEFAULT_INSTALLMENT_DUE_DAY_END,
    }
