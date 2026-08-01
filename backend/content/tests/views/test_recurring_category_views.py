"""API tests for the recurring-payment category catalog and reordering."""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import RecurringCategory, RecurringPayment
from content.services import accounting_service


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


@pytest.fixture(autouse=True)
def _drop_seeded_categories():
    """Start from an empty catalog.

    Migration 0171 seeds four starter categories, so they exist in every
    fresh test database; these tests assert on their own fixtures.
    """
    RecurringCategory.objects.all().delete()


def make_category(name, order=0):
    return RecurringCategory.objects.create(name=name, order=order)


def make_payment(name, category=None, order=0, **kwargs):
    defaults = {
        'price': Decimal('100.00'),
        'cop_equivalent': Decimal('100.00'),
        'frequency': 'monthly',
    }
    defaults.update(kwargs)
    return RecurringPayment.objects.create(
        name=name, category=category, order=order, **defaults,
    )


@pytest.mark.django_db
class TestRecurringCategoryCrud:
    def test_list_returns_categories_in_order_with_payment_count(self, super_client):
        infra = make_category('Infraestructura', order=1)
        make_category('IA', order=0)
        make_payment('Hostinger', category=infra)
        make_payment('GoDaddy', category=infra)

        response = super_client.get('/api/accounting/recurring-categories/')

        assert response.status_code == 200
        results = response.data['results']
        assert [c['name'] for c in results] == ['IA', 'Infraestructura']
        assert [c['payment_count'] for c in results] == [0, 2]

    def test_create_derives_a_slug(self, super_client):
        response = super_client.post(
            '/api/accounting/recurring-categories/create/',
            {'name': 'Suscripciones de IA'},
            format='json',
        )

        assert response.status_code == 201, response.data
        assert response.data['slug'] == 'suscripciones-de-ia'

    def test_create_rejects_a_blank_name(self, super_client):
        response = super_client.post(
            '/api/accounting/recurring-categories/create/',
            {'name': '   '},
            format='json',
        )

        assert response.status_code == 400
        assert 'name' in response.data

    def test_update_renames_the_category(self, super_client):
        category = make_category('Extras')

        response = super_client.patch(
            f'/api/accounting/recurring-categories/{category.id}/update/',
            {'name': 'Extras / otros'},
            format='json',
        )

        assert response.status_code == 200, response.data
        category.refresh_from_db()
        assert category.name == 'Extras / otros'

    def test_delete_removes_an_empty_category(self, super_client):
        category = make_category('Vacía')

        response = super_client.delete(
            f'/api/accounting/recurring-categories/{category.id}/delete/',
        )

        assert response.status_code == 204
        assert not RecurringCategory.objects.filter(pk=category.id).exists()

    def test_delete_is_blocked_while_the_category_has_payments(self, super_client):
        category = make_category('Con pagos')
        make_payment('Netflix', category=category)

        response = super_client.delete(
            f'/api/accounting/recurring-categories/{category.id}/delete/',
        )

        assert response.status_code == 409
        assert response.data['payment_count'] == 1
        assert RecurringCategory.objects.filter(pk=category.id).exists()


@pytest.mark.django_db
class TestRecurringCategoryReorder:
    def test_reorder_applies_the_array_position(self, super_client):
        first = make_category('Primera', order=0)
        second = make_category('Segunda', order=1)
        third = make_category('Tercera', order=2)

        response = super_client.post(
            '/api/accounting/recurring-categories/reorder/',
            {'ids': [third.id, first.id, second.id]},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert list(
            RecurringCategory.objects.values_list('name', flat=True)
        ) == ['Tercera', 'Primera', 'Segunda']

    def test_reorder_rejects_a_non_list_payload(self, super_client):
        response = super_client.post(
            '/api/accounting/recurring-categories/reorder/',
            {'ids': 'nope'},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'invalid_reorder_payload'


@pytest.mark.django_db
class TestRecurringPaymentReorder:
    def test_reorder_persists_the_manual_order(self, super_client):
        category = make_category('IA')
        chatgpt = make_payment('Chat-GPT', category=category, order=0)
        claude = make_payment('Claude Code 20x', category=category, order=1)

        response = super_client.post(
            '/api/accounting/recurring/reorder/',
            {'items': [
                {'id': claude.id, 'category': category.id, 'order': 0},
                {'id': chatgpt.id, 'category': category.id, 'order': 1},
            ]},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['reordered'] == 2
        assert list(
            RecurringPayment.objects.values_list('name', flat=True)
        ) == ['Claude Code 20x', 'Chat-GPT']

    def test_reorder_moves_a_payment_to_another_category(self, super_client):
        ia = make_category('IA', order=0)
        extras = make_category('Extras', order=1)
        netflix = make_payment('Netflix', category=ia, order=0)

        response = super_client.post(
            '/api/accounting/recurring/reorder/',
            {'items': [{'id': netflix.id, 'category': extras.id, 'order': 0}]},
            format='json',
        )

        assert response.status_code == 200, response.data
        netflix.refresh_from_db()
        assert netflix.category_id == extras.id

    def test_reorder_ignores_unknown_ids(self, super_client):
        category = make_category('IA')
        payment = make_payment('Chat-GPT', category=category, order=5)

        response = super_client.post(
            '/api/accounting/recurring/reorder/',
            {'items': [
                {'id': payment.id, 'category': category.id, 'order': 0},
                {'id': 999999, 'category': category.id, 'order': 1},
            ]},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['reordered'] == 1
        payment.refresh_from_db()
        assert payment.order == 0

    def test_reorder_rejects_a_non_list_payload(self, super_client):
        response = super_client.post(
            '/api/accounting/recurring/reorder/',
            {'items': {'id': 1}},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'invalid_reorder_payload'

    def test_reorder_rejects_an_unknown_category(self, super_client):
        category = make_category('IA')
        payment = make_payment('Chat-GPT', category=category, order=0)

        response = super_client.post(
            '/api/accounting/recurring/reorder/',
            {'items': [{'id': payment.id, 'category': 999999, 'order': 0}]},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'unknown_category'
        payment.refresh_from_db()
        assert payment.category_id == category.id


@pytest.mark.django_db
class TestRecurringPaymentCategoryWiring:
    def test_list_is_ordered_by_category_then_manual_slot(self, super_client):
        ia = make_category('IA', order=0)
        infra = make_category('Infraestructura', order=1)
        make_payment('Hostinger', category=infra, order=0)
        make_payment('Claude Code 20x', category=ia, order=1)
        make_payment('Chat-GPT', category=ia, order=0)

        response = super_client.get('/api/accounting/recurring/')

        assert [r['name'] for r in response.data['results']] == [
            'Chat-GPT', 'Claude Code 20x', 'Hostinger',
        ]

    def test_list_exposes_the_monthly_columns(self, super_client):
        category = make_category('Infraestructura')
        make_payment(
            'NameCheap', category=category, price=Decimal('10.98'),
            currency='USD', cop_equivalent=Decimal('43920.00'),
            frequency='annual',
        )

        response = super_client.get('/api/accounting/recurring/')
        row = response.data['results'][0]

        assert row['monthly_price'] == '0.92'
        assert row['monthly_cop_cost'] == '3660.00'
        assert row['category_name'] == 'Infraestructura'

    def test_filter_by_category(self, super_client):
        ia = make_category('IA', order=0)
        infra = make_category('Infraestructura', order=1)
        make_payment('Chat-GPT', category=ia)
        make_payment('Hostinger', category=infra)

        response = super_client.get(
            f'/api/accounting/recurring/?category={ia.id}',
        )

        assert [r['name'] for r in response.data['results']] == ['Chat-GPT']

    def test_created_payment_lands_at_the_end_of_its_category(self, super_client):
        category = make_category('IA')
        make_payment('Chat-GPT', category=category, order=0)
        make_payment('Claude Code 20x', category=category, order=1)

        response = super_client.post(
            '/api/accounting/recurring/create/',
            {
                'name': 'Perplexity',
                'price': '20.00',
                'currency': 'COP',
                'category': category.id,
            },
            format='json',
        )

        assert response.status_code == 201, response.data
        assert RecurringPayment.objects.get(name='Perplexity').order == 2

    def test_changing_category_sends_the_payment_to_the_end(self, super_client):
        ia = make_category('IA', order=0)
        extras = make_category('Extras', order=1)
        make_payment('Netflix', category=extras, order=0)
        make_payment('Spotify', category=extras, order=1)
        moved = make_payment('Chat-GPT', category=ia, order=0)

        response = super_client.patch(
            f'/api/accounting/recurring/{moved.id}/update/',
            {'category': extras.id},
            format='json',
        )

        assert response.status_code == 200, response.data
        moved.refresh_from_db()
        assert moved.category_id == extras.id
        assert moved.order == 2
