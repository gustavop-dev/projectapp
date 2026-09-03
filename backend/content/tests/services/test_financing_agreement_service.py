import hashlib
from datetime import date
from decimal import Decimal

import pytest

from content.models import FinancingAgreement, FinancingAgreementTemplate
from content.services.financing_agreement_service import (
    FinancingAgreementTransitionError,
    FinancingAgreementValidationError,
    build_installment_schedule,
    create_agreement,
    create_second_cycle,
    mark_ready,
    normalize_installment_schedule,
    update_draft,
)


pytestmark = pytest.mark.django_db


def _template():
    return FinancingAgreementTemplate.objects.create(
        name='Prueba',
        version=1,
        is_default=True,
        content_markdown=(
            '{agreement_number} {client_full_name} {client_id_type} '
            '{client_id_number} {contractor_full_name} {contractor_id_type} '
            '{contractor_id_number} {original_contract_reference} '
            '{original_contract_date} {project_name} {financed_scope} '
            '{financed_balance} {installment_schedule} {hosting_value} '
            '{modality_label} {modality_terms} {partnership_end_date}'
        ),
    )


def _agreement_data(client, template, **overrides):
    data = {
        'client': client,
        'original_contract_reference': 'Contrato PA-001',
        'original_contract_date': date(2026, 1, 15),
        'project_name': 'Vástago',
        'financed_scope': 'Desarrollo e implementación de la fase 2.',
        'modality': FinancingAgreement.Modality.FIVE_YEAR,
        'partnership_start_date': date(2026, 2, 1),
        'currency': 'COP',
        'total_value': Decimal('12000000.00'),
        'initial_payment': Decimal('0.00'),
        'hosting_value': Decimal('500000.00'),
        'hosting_period': FinancingAgreement.HostingPeriod.MONTHLY,
        'first_installment_date': date(2026, 3, 5),
        'template': template,
    }
    data.update(overrides)
    return data


def test_schedule_rounding_preserves_exact_financed_balance():
    schedule = build_installment_schedule(Decimal('100.00'), date(2026, 3, 5))

    assert len(schedule) == 12
    assert schedule[0]['amount'] == '8.33'
    assert schedule[-1]['amount'] == '8.37'
    assert sum(Decimal(row['amount']) for row in schedule) == Decimal('100.00')


def test_schedule_rejects_due_date_after_fifth_day():
    schedule = build_installment_schedule(Decimal('1200.00'), date(2026, 3, 5))
    schedule[4]['due_date'] = '2026-07-06'

    with pytest.raises(FinancingAgreementValidationError) as exc_info:
        normalize_installment_schedule(schedule, Decimal('1200.00'))

    assert 'días 1 y 5' in str(exc_info.value.errors['installment_schedule'])


def test_mark_ready_freezes_numbered_legal_snapshot(
    make_client_profile,
    admin_user,
    company_settings,
):
    client = make_client_profile(nit='901234567-1')
    agreement = create_agreement(
        _agreement_data(client, _template()),
        actor=admin_user,
    )

    ready = mark_ready(agreement, actor=admin_user)

    assert ready.number.startswith('OFIN-')
    assert ready.status == FinancingAgreement.Status.READY
    assert 'Ana Cliente' in ready.resolved_contract_markdown
    assert '12.000.000,00 COP' in ready.resolved_contract_markdown
    assert ready.resolved_contract_sha256 == hashlib.sha256(
        ready.resolved_contract_markdown.encode('utf-8'),
    ).hexdigest()


def test_second_cycle_requires_completed_first_cycle(
    make_client_profile,
    admin_user,
    company_settings,
):
    agreement = create_agreement(
        _agreement_data(make_client_profile(nit='9001'), _template()),
        actor=admin_user,
    )

    with pytest.raises(FinancingAgreementTransitionError):
        create_second_cycle(agreement, actor=admin_user)


def test_second_cycle_update_preserves_original_partnership_end(
    make_client_profile,
    admin_user,
    company_settings,
):
    first = create_agreement(
        _agreement_data(make_client_profile(nit='9002'), _template()),
        actor=admin_user,
    )
    FinancingAgreement.objects.filter(pk=first.pk).update(
        status=FinancingAgreement.Status.COMPLETED,
    )
    first.refresh_from_db()
    second = create_second_cycle(first, actor=admin_user)

    updated = update_draft(
        second,
        {
            'partnership_start_date': first.partnership_start_date,
            'total_value': Decimal('6000000.00'),
            'initial_payment': Decimal('0.00'),
            'first_installment_date': date(2028, 3, 5),
            'financed_scope': 'Segunda fase del producto.',
        },
        actor=admin_user,
    )

    assert updated.partnership_end_date == first.partnership_end_date
