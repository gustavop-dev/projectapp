"""API tests for the credit-card statement endpoints (superuser-only)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import (
    CreditCardStatement,
    CreditCardTransaction,
    MerchantAlias,
)
from content.services import accounting_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


CREATE_PAYLOAD = {
    'card_name': 'Visa Bancolombia',
    'period': None,  # replaced below
    'period_date': '2026-06',
    'purchases_total': '100000.00',
    'transactions': [
        {
            'transaction_date': '2026-06-05',
            'raw_description': 'PAYU*NETFLIX 990011',
            'amount': '60000.00',
        },
        {
            'transaction_date': '2026-06-09',
            'raw_description': 'PRIMAX 8811',
            'amount': '40000.00',
        },
    ],
}
CREATE_PAYLOAD.pop('period')


def _create_statement(client):
    response = client.post(
        '/api/accounting/statements/create/', CREATE_PAYLOAD, format='json',
    )
    assert response.status_code == 201, response.data
    return response.data


class TestStatementAuth:
    def test_requires_authentication(self, api_client):
        assert api_client.get(
            '/api/accounting/statements/',
        ).status_code in (401, 403)

    def test_staff_without_superuser_is_rejected(self, admin_client):
        assert admin_client.get(
            '/api/accounting/statements/',
        ).status_code == 403


class TestStatementCreate:
    def test_creates_draft_with_nested_transactions(self, super_client):
        data = _create_statement(super_client)
        assert data['status'] == 'draft'
        assert len(data['transactions']) == 2
        assert data['transactions_sum'] == '100000.00'

    def test_duplicate_card_period_returns_400(self, super_client):
        _create_statement(super_client)
        response = super_client.post(
            '/api/accounting/statements/create/', CREATE_PAYLOAD,
            format='json',
        )
        assert response.status_code == 400
        assert 'Ya existe un extracto' in str(response.data)

    def test_invalid_transaction_rolls_back_everything(self, super_client):
        payload = {
            **CREATE_PAYLOAD,
            'transactions': [
                CREATE_PAYLOAD['transactions'][0],
                {'transaction_date': '2026-06-09'},  # missing fields
            ],
        }
        response = super_client.post(
            '/api/accounting/statements/create/', payload, format='json',
        )
        assert response.status_code == 400
        assert CreditCardStatement.objects.count() == 0
        assert CreditCardTransaction.objects.count() == 0


class TestStatementStatusGrid:
    def test_status_endpoint_resolves_before_detail_route(self, super_client):
        _create_statement(super_client)
        response = super_client.get(
            '/api/accounting/statements/status/?year=2026',
        )
        assert response.status_code == 200
        assert len(response.data['months']) == 12
        assert response.data['months'][5]['has_draft'] is True

    def test_rejects_invalid_year(self, super_client):
        response = super_client.get(
            '/api/accounting/statements/status/?year=abc',
        )
        assert response.status_code == 400


class TestStatementLifecycleEndpoints:
    def test_finalize_mismatch_returns_400_with_difference(self, super_client):
        data = _create_statement(super_client)
        CreditCardStatement.objects.filter(pk=data['id']).update(
            purchases_total=Decimal('999999.00'),
        )
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/finalize/", {},
            format='json',
        )
        assert response.status_code == 400
        assert 'diferencia' in str(response.data)

    def test_finalize_and_reopen_roundtrip(self, super_client):
        data = _create_statement(super_client)
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/finalize/", {},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['status'] == 'processed'
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/reopen/", {},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['status'] == 'draft'

    def test_delete_cascades_transactions(self, super_client):
        data = _create_statement(super_client)
        response = super_client.delete(
            f"/api/accounting/statements/{data['id']}/delete/",
        )
        assert response.status_code == 204
        assert CreditCardTransaction.objects.count() == 0


class TestTransactionEndpoints:
    def test_bulk_create_appends_to_draft(self, super_client):
        data = _create_statement(super_client)
        response = super_client.post(
            f"/api/accounting/statements/{data['id']}/transactions/batch/",
            {'transactions': [{
                'transaction_date': '2026-06-15',
                'raw_description': 'UBER TRIP',
                'amount': '25000.00',
            }]},
            format='json',
        )
        assert response.status_code == 201
        assert CreditCardTransaction.objects.count() == 3

    def test_update_transaction_of_processed_statement_is_blocked(
        self, super_client,
    ):
        data = _create_statement(super_client)
        super_client.post(
            f"/api/accounting/statements/{data['id']}/finalize/", {},
            format='json',
        )
        tx_id = data['transactions'][0]['id']
        response = super_client.patch(
            f"/api/accounting/statements/{data['id']}/transactions/{tx_id}/update/",
            {'merchant_name': 'Netflix'},
            format='json',
        )
        assert response.status_code == 400


class TestMerchantAliasEndpoints:
    def test_resolve_endpoint_matches_normalized(self, super_client):
        MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX', merchant_name='Netflix',
            default_category='software',
        )
        response = super_client.post(
            '/api/accounting/merchant-aliases/resolve/',
            {'raw_descriptions': ['payu*netflix 990011', 'RARO SAS']},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['resolved'][0]['merchant_name'] == 'Netflix'
        assert response.data['unresolved'] == ['RARO SAS']

    def test_create_alias_normalizes_match_text(self, super_client):
        response = super_client.post(
            '/api/accounting/merchant-aliases/create/',
            {'match_text': 'primax 881100', 'merchant_name': 'Primax',
             'default_category': 'fuel'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['match_text'] == 'PRIMAX'


class TestUpdateMerchantAlias:
    """The panel patches aliases inline from the learned-merchants table."""

    @staticmethod
    def _url(alias):
        return f'/api/accounting/merchant-aliases/{alias.pk}/update/'

    @pytest.fixture
    def alias(self):
        return MerchantAlias.objects.create(
            match_text='PAYU*NETFLIX', merchant_name='Netflix',
            default_category='software',
        )

    def test_patches_merchant_name_and_category(self, super_client, alias):
        """The response carries the stored values and the fresh label the
        panel renders in the learned-merchants row."""
        response = super_client.patch(
            self._url(alias),
            {'merchant_name': 'Netflix Colombia', 'default_category': 'other'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['merchant_name'] == 'Netflix Colombia'
        assert response.data['default_category'] == 'other'
        assert response.data['default_category_label'] == 'Otros'
        alias.refresh_from_db()
        assert alias.merchant_name == 'Netflix Colombia'

    def test_patching_one_field_leaves_the_rest_untouched(
        self, super_client, alias,
    ):
        response = super_client.patch(
            self._url(alias), {'merchant_name': 'Netflix Inc'}, format='json',
        )

        assert response.status_code == 200
        assert response.data['match_text'] == 'PAYU*NETFLIX'
        assert response.data['default_category'] == 'software'

    def test_patching_match_text_normalizes_it(self, super_client, alias):
        response = super_client.patch(
            self._url(alias), {'match_text': 'payu netflix 990011'},
            format='json',
        )

        assert response.status_code == 200
        # Uppercased and stripped of the 6-digit reference code.
        assert response.data['match_text'] == 'PAYU NETFLIX'

    def test_rejects_a_match_text_owned_by_another_alias(
        self, super_client, alias,
    ):
        """Two aliases resolving the same descriptor would make the match
        ambiguous, so the collision is refused and nothing is written."""
        MerchantAlias.objects.create(
            match_text='PRIMAX', merchant_name='Primax',
            default_category='fuel',
        )

        response = super_client.patch(
            self._url(alias), {'match_text': 'primax'}, format='json',
        )

        assert response.status_code == 400
        assert 'match_text' in response.data
        alias.refresh_from_db()
        assert alias.match_text == 'PAYU*NETFLIX'

    def test_keeping_its_own_match_text_is_allowed(self, super_client, alias):
        """The uniqueness check must exclude the instance being updated."""
        response = super_client.patch(
            self._url(alias),
            {'match_text': 'payu*netflix', 'merchant_name': 'Netflix Inc'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['match_text'] == 'PAYU*NETFLIX'

    def test_rejects_an_empty_match_text(self, super_client, alias):
        response = super_client.patch(
            self._url(alias), {'match_text': '   '}, format='json',
        )

        assert response.status_code == 400

    def test_unknown_alias_returns_404(self, super_client):
        response = super_client.patch(
            '/api/accounting/merchant-aliases/999999/update/',
            {'merchant_name': 'Nadie'}, format='json',
        )

        assert response.status_code == 404


class TestLearnMerchantAlias:
    """The panel learns aliases from hand-typed merchant corrections."""

    URL = '/api/accounting/merchant-aliases/learn/'

    def test_learns_a_new_alias_from_the_raw_description(self, super_client):
        response = super_client.post(
            self.URL,
            {'raw_description': 'primax 881100', 'merchant_name': 'Primax',
             'category': 'fuel'},
            format='json',
        )
        assert response.status_code == 200, response.data
        assert response.data['alias']['match_text'] == 'PRIMAX'
        assert response.data['alias']['merchant_name'] == 'Primax'
        assert response.data['applied'] == 0

    def test_rewrites_an_existing_alias_instead_of_failing(self, super_client):
        """A manual fix must be able to correct a wrong mapping."""
        MerchantAlias.objects.create(
            match_text='PRIMAX', merchant_name='Equivocado',
            default_category='other',
        )

        # Normalizing drops the 6-digit token, so this lands on 'PRIMAX'.
        response = super_client.post(
            self.URL,
            {'raw_description': 'primax 881100', 'merchant_name': 'Primax',
             'category': 'fuel'},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert MerchantAlias.objects.filter(match_text='PRIMAX').count() == 1
        alias = MerchantAlias.objects.get(match_text='PRIMAX')
        assert alias.merchant_name == 'Primax'
        assert alias.default_category == 'fuel'

    def test_back_applies_to_the_unidentified_rows_of_the_statement(
        self, super_client,
    ):
        statement = _create_statement(super_client)

        response = super_client.post(
            self.URL,
            {'raw_description': 'PRIMAX 8811', 'merchant_name': 'Primax',
             'category': 'fuel', 'statement_id': statement['id']},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['applied'] == 1
        tx = CreditCardTransaction.objects.get(raw_description='PRIMAX 8811')
        assert tx.merchant_name == 'Primax'
        assert tx.category == 'fuel'
        assert tx.is_identified is True

    def test_rejects_a_blank_merchant(self, super_client):
        response = super_client.post(
            self.URL,
            {'raw_description': 'PRIMAX 8811', 'merchant_name': '   '},
            format='json',
        )
        assert response.status_code == 400
        assert not MerchantAlias.objects.exists()

    def test_rejects_an_unknown_category(self, super_client):
        response = super_client.post(
            self.URL,
            {'raw_description': 'PRIMAX 8811', 'merchant_name': 'Primax',
             'category': 'crypto'},
            format='json',
        )
        assert response.status_code == 400
        assert not MerchantAlias.objects.exists()

    def test_rejects_a_non_numeric_statement_id(self, super_client):
        response = super_client.post(
            self.URL,
            {'raw_description': 'PRIMAX 8811', 'merchant_name': 'Primax',
             'statement_id': 'abc'},
            format='json',
        )
        assert response.status_code == 400

    def test_staff_without_superuser_is_rejected(self, admin_client):
        response = admin_client.post(
            self.URL,
            {'raw_description': 'PRIMAX 8811', 'merchant_name': 'Primax'},
            format='json',
        )
        assert response.status_code in (401, 403)


class TestStatementPdfEndpoints:
    def _upload(self, client, statement_id, name='extracto.pdf', size=4):
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(name, b'x' * size, content_type='application/pdf')
        return client.post(
            f'/api/accounting/statements/{statement_id}/pdf/upload/',
            {'file': file},
            format='multipart',
        )

    def test_upload_view_and_delete_cycle(self, super_client):
        statement = _create_statement(super_client)
        response = self._upload(super_client, statement['id'])
        assert response.status_code == 200, response.data
        assert response.data['pdf_file_url']

        deletion = super_client.delete(
            f"/api/accounting/statements/{statement['id']}/pdf/delete/",
        )
        assert deletion.status_code == 200
        assert deletion.data['pdf_file_url'] is None

    def test_upload_rejects_non_pdf(self, super_client):
        statement = _create_statement(super_client)
        response = self._upload(super_client, statement['id'], name='extracto.png')
        assert response.status_code == 400
        assert response.data['code'] == 'statement_pdf_type_not_allowed'

    def test_upload_rejects_oversize(self, super_client):
        statement = _create_statement(super_client)
        response = self._upload(
            super_client, statement['id'], size=15 * 1024 * 1024 + 1,
        )
        assert response.status_code == 400
        assert response.data['code'] == 'statement_pdf_too_large'

    def test_delete_without_pdf_is_rejected(self, super_client):
        statement = _create_statement(super_client)
        response = super_client.delete(
            f"/api/accounting/statements/{statement['id']}/pdf/delete/",
        )
        assert response.status_code == 400
        assert response.data['code'] == 'statement_pdf_missing'
