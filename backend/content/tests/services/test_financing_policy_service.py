from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from content.models import (
    AccountingSettings,
    FinancingAgreement,
    FinancingAgreementTemplate,
    FinancingPolicyRevision,
)
from content.services.financing_agreement_service import (
    FinancingAgreementTransitionError,
    FinancingAgreementValidationError,
    apply_current_policy,
    create_agreement,
    mark_ready,
)
from content.services.financing_policy_service import (
    FinancingPolicyValidationError,
    create_policy_revision,
    validate_agreement_financials,
)


pytestmark = pytest.mark.django_db


def _revision_data(**overrides):
    policy = FinancingPolicyRevision.get_current()
    values = {
        'minimum_project_value_cop': policy.minimum_project_value_cop,
        'maximum_project_value_cop': policy.maximum_project_value_cop,
        'financing_months': policy.financing_months,
        'maximum_financed_percent': policy.maximum_financed_percent,
        'late_hosting_increase_percent': policy.late_hosting_increase_percent,
        'installment_due_day_start': policy.installment_due_day_start,
        'installment_due_day_end': policy.installment_due_day_end,
    }
    values.update(overrides)
    return values


def _agreement_data(client, **overrides):
    values = {
        'client': client,
        'original_contract_reference': 'Contrato PA-020',
        'original_contract_date': date(2026, 1, 15),
        'project_name': 'Producto elegible',
        'financed_scope': 'Desarrollo e implementación de la primera fase.',
        'modality': FinancingAgreement.Modality.FIVE_YEAR,
        'partnership_start_date': date(2026, 2, 1),
        'currency': 'COP',
        'total_value': Decimal('25000000.00'),
        'initial_payment': Decimal('5000000.00'),
        'hosting_value': Decimal('500000.00'),
        'hosting_period': FinancingAgreement.HostingPeriod.MONTHLY,
        'first_installment_date': date(2026, 3, 5),
        'template': FinancingAgreementTemplate.get_default(),
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ('total', 'initial'),
    (
        (Decimal('20000000.00'), Decimal('4000000.00')),
        (Decimal('140000000.00'), Decimal('28000000.00')),
    ),
)
def test_policy_accepts_inclusive_value_boundary(total, initial):
    policy = FinancingPolicyRevision.get_current()

    equivalent = validate_agreement_financials(
        total_value=total,
        initial_payment=initial,
        currency='COP',
        exchange_rate=None,
        policy=policy,
    )

    assert equivalent == total


@pytest.mark.parametrize(
    'total',
    (Decimal('19999999.99'), Decimal('140000000.01')),
)
def test_policy_rejects_value_outside_range(total):
    policy = FinancingPolicyRevision.get_current()

    with pytest.raises(FinancingPolicyValidationError) as exc_info:
        validate_agreement_financials(
            total_value=total,
            initial_payment=total,
            currency='COP',
            exchange_rate=None,
            policy=policy,
        )

    assert 'total_value' in exc_info.value.errors


def test_policy_rejects_initial_contribution_below_minimum():
    policy = FinancingPolicyRevision.get_current()

    with pytest.raises(FinancingPolicyValidationError) as exc_info:
        validate_agreement_financials(
            total_value=Decimal('20000000.00'),
            initial_payment=Decimal('3999999.99'),
            currency='COP',
            exchange_rate=None,
            policy=policy,
        )

    assert 'initial_payment' in exc_info.value.errors


def test_publish_policy_creates_next_immutable_revision(admin_user):
    previous = FinancingPolicyRevision.get_current()

    published = create_policy_revision(
        _revision_data(financing_months=18),
        actor=admin_user,
    )

    previous.refresh_from_db()
    assert published.version == previous.version + 1
    assert previous.financing_months == 12


def test_publish_policy_rejects_unchanged_values(admin_user):
    with pytest.raises(FinancingPolicyValidationError) as exc_info:
        create_policy_revision(_revision_data(), actor=admin_user)

    assert exc_info.value.code == 'financing_policy_unchanged'


def test_usd_agreement_freezes_accounting_exchange_rate(
    make_client_profile,
    admin_user,
):
    settings = AccountingSettings.load()
    settings.usd_exchange_rate = Decimal('4000.00')
    settings.save(update_fields=['usd_exchange_rate', 'updated_at'])

    agreement = create_agreement(
        _agreement_data(
            make_client_profile(nit='900300200-1'),
            currency='USD',
            total_value=Decimal('5000.00'),
            initial_payment=Decimal('1000.00'),
        ),
        actor=admin_user,
    )

    assert agreement.eligibility_exchange_rate == Decimal('4000.00')
    assert agreement.equivalent_total_cop == Decimal('20000000.00')


@freeze_time('2026-02-01 12:00:00')
def test_draft_adopts_current_policy_schedule(
    make_client_profile,
    admin_user,
):
    agreement = create_agreement(
        _agreement_data(make_client_profile(nit='900300200-2')),
        actor=admin_user,
    )
    agreement.contract_markdown = 'Texto personalizado del borrador'
    agreement.save(update_fields=['contract_markdown', 'updated_at'])
    policy = create_policy_revision(
        _revision_data(
            financing_months=10,
            late_hosting_increase_percent=Decimal('3.00'),
            installment_due_day_start=2,
            installment_due_day_end=6,
        ),
        actor=admin_user,
    )

    adopted = apply_current_policy(agreement, actor=admin_user)

    assert adopted.policy_revision == policy
    assert len(adopted.installment_schedule) == 10
    assert adopted.contract_markdown == FinancingAgreementTemplate.get_default().content_markdown
    assert adopted.events.filter(event_type='policy_revision_applied').exists()


def test_locked_agreement_rejects_current_policy_adoption(
    make_client_profile,
    admin_user,
    company_settings,
):
    agreement = create_agreement(
        _agreement_data(make_client_profile(nit='900300200-3')),
        actor=admin_user,
    )
    ready = mark_ready(agreement, actor=admin_user)
    create_policy_revision(
        _revision_data(financing_months=18),
        actor=admin_user,
    )

    with pytest.raises(FinancingAgreementTransitionError):
        apply_current_policy(ready, actor=admin_user)

    ready.refresh_from_db()
    assert ready.policy_revision.version == 2


def test_policy_adoption_is_atomic_when_values_become_ineligible(
    make_client_profile,
    admin_user,
):
    agreement = create_agreement(
        _agreement_data(make_client_profile(nit='900300200-4')),
        actor=admin_user,
    )
    original_policy_id = agreement.policy_revision_id
    create_policy_revision(
        _revision_data(maximum_financed_percent=Decimal('70.00')),
        actor=admin_user,
    )

    with pytest.raises(FinancingAgreementValidationError):
        apply_current_policy(agreement, actor=admin_user)

    agreement.refresh_from_db()
    assert agreement.policy_revision_id == original_policy_id
