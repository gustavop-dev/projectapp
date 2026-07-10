"""Tests for the hosting cycle history (total_paid source of truth)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import HostingCycle, HostingRecord
from content.services import accounting_service, hosting_cycle_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


def make_hosting(**overrides):
    defaults = {
        'client_name': 'German - Kore',
        'monthly_value': Decimal('91667.00'),
        'payment_modality': 'semiannual',
        'payment_per_cycle': Decimal('550002.00'),
        'valid_from': date(2026, 1, 2),
        'valid_to': date(2026, 7, 2),
    }
    defaults.update(overrides)
    return HostingRecord.objects.create(**defaults)


class TestRegisterCycle:
    def test_defaults_from_contract_and_advances_validity(self):
        hosting = make_hosting()
        cycle = hosting_cycle_service.register_cycle_payment(
            hosting, data={},
        )
        assert cycle.amount == Decimal('550002.00')
        assert cycle.modality == 'semiannual'
        assert cycle.period_from == date(2026, 7, 2)
        assert cycle.period_to == date(2027, 1, 2)
        hosting.refresh_from_db()
        assert hosting.valid_to == date(2027, 1, 2)
        assert hosting.total_paid == Decimal('550002.00')
        assert hosting.cycles_count == 1

    def test_modality_switch_adds_up_correctly(self):
        hosting = make_hosting()
        hosting_cycle_service.register_cycle_payment(hosting, data={})
        hosting.refresh_from_db()
        # Client switches to quarterly for the next period.
        hosting_cycle_service.register_cycle_payment(
            hosting,
            data={'modality': 'quarterly', 'amount': Decimal('275001.00')},
        )
        hosting.refresh_from_db()
        assert hosting.total_paid == Decimal('825003.00')
        assert hosting.cycles_count == 2
        assert hosting.valid_to == date(2027, 4, 2)

    def test_advance_validity_off_keeps_valid_to(self):
        hosting = make_hosting()
        hosting_cycle_service.register_cycle_payment(
            hosting, data={'advance_validity': False},
        )
        hosting.refresh_from_db()
        assert hosting.valid_to == date(2026, 7, 2)
        assert hosting.total_paid == Decimal('550002.00')

    def test_renewal_rearms_expiry_cadence(self):
        hosting = make_hosting(
            expiry_notice_target=date(2026, 7, 2),
            expiry_notice_count=2,
            expiry_notice_last_sent_at=date(2026, 6, 25),
        )
        hosting_cycle_service.register_cycle_payment(hosting, data={})
        hosting.refresh_from_db()
        # The target snapshot no longer matches: the daily task re-arms.
        assert hosting.expiry_notice_target != hosting.valid_to

    def test_audits_the_hosting_change(self):
        from content.models import AccountingChangeLog

        hosting = make_hosting()
        hosting_cycle_service.register_cycle_payment(hosting, data={})
        log = AccountingChangeLog.objects.get(entity_type='hosting')
        changed_fields = {change['field'] for change in log.changes}
        assert 'total_paid' in changed_fields
        assert 'valid_to' in changed_fields


class TestDeleteCycle:
    def test_delete_recalculates_but_keeps_validity(self):
        hosting = make_hosting()
        cycle = hosting_cycle_service.register_cycle_payment(hosting, data={})
        hosting.refresh_from_db()
        hosting_cycle_service.delete_cycle(hosting, cycle)
        hosting.refresh_from_db()
        assert hosting.total_paid == Decimal('0')
        assert hosting.cycles_count == 0
        assert hosting.valid_to == date(2027, 1, 2)


class TestEndpoints:
    def test_cycle_crud_flow(self, super_client):
        hosting = make_hosting()
        create = super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/cycles/create/',
            {'amount': '550002.00'},
            format='json',
        )
        assert create.status_code == 201, create.data
        assert create.data['hosting']['total_paid'] == '550002.00'
        assert create.data['cycle']['modality_label'] == 'Semestral'
        cycle_id = create.data['cycle']['id']

        listing = super_client.get(
            f'/api/accounting/hostings/{hosting.pk}/cycles/',
        )
        assert [c['id'] for c in listing.data['results']] == [cycle_id]

        delete = super_client.delete(
            f'/api/accounting/hostings/{hosting.pk}/cycles/{cycle_id}/delete/',
        )
        assert delete.status_code == 204
        hosting.refresh_from_db()
        assert hosting.total_paid == Decimal('0')

    def test_write_serializer_ignores_direct_totals(self, super_client):
        hosting = make_hosting()
        HostingCycle.objects.create(
            hosting_record=hosting, modality='semiannual',
            amount=Decimal('100.00'), paid_at=date(2026, 1, 2),
        )
        hosting_cycle_service.recalculate_hosting_totals(hosting)
        response = super_client.patch(
            f'/api/accounting/hostings/{hosting.pk}/update/',
            {'total_paid': '999999.00', 'cycles_count': 42},
            format='json',
        )
        assert response.status_code == 200
        hosting.refresh_from_db()
        assert hosting.total_paid == Decimal('100.00')
        assert hosting.cycles_count == 1
