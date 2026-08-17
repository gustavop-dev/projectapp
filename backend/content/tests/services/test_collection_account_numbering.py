"""Per-client numbering: code derivation and PA-{CODE}-{NNN} allocation."""
from decimal import Decimal

import pytest
from accounts.models import UserProfile
from django.contrib.auth import get_user_model

from content.models import ClientDocumentNumberSequence, Document, IssuerProfile
from content.services.collection_account_numbering import (
    allocate_client_number,
    derive_billing_code,
    ensure_billing_code,
    peek_next_client_number,
)
from content.services.collection_account_service import (
    CollectionAccountError,
    delete_collection_account,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def issuer():
    return IssuerProfile.objects.create(
        name='ProjectApp',
        legal_name='ProjectApp SAS',
        public_number_prefix='PA',
    )


def make_profile(company='Acme Soluciones', email='acme@example.com', **extra):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345',
    )
    return UserProfile.objects.create(
        user=user, company_name=company, **extra,
    )


class TestDeriveBillingCode:
    def test_derives_from_company_name_capped_at_8(self):
        profile = make_profile(company='Acme Soluciones')
        assert derive_billing_code(profile) == 'ACMESOLU'

    def test_strips_accents_and_symbols(self):
        profile = make_profile(company='Café & Diseño S.A.S.')
        assert derive_billing_code(profile) == 'CAFEDISE'

    def test_numeric_only_gets_c_prefix(self):
        profile = make_profile(company='123456')
        assert derive_billing_code(profile) == 'C123456'

    def test_empty_base_falls_back_to_c_pk(self):
        profile = make_profile(company='', email='---@example.com')
        assert derive_billing_code(profile) == f'C{profile.pk}'

    def test_collision_with_other_profile_appends_suffix(self):
        first = make_profile(company='Acme Soluciones')
        first.billing_code = ensure_billing_code(first)
        second = make_profile(
            company='Acme Soluciones', email='acme2@example.com',
        )
        assert derive_billing_code(second) == 'ACMESOLU2'

    def test_ensure_respects_manually_set_code(self):
        profile = make_profile()
        profile.billing_code = 'CUSTOM'
        profile.save(update_fields=['billing_code'])
        assert ensure_billing_code(profile) == 'CUSTOM'


class TestAllocateClientNumber:
    def test_allocates_continuous_series(self, issuer):
        profile = make_profile()
        assert allocate_client_number(profile, issuer) == 'PA-ACMESOLU-001'
        assert allocate_client_number(profile, issuer) == 'PA-ACMESOLU-002'
        seq = ClientDocumentNumberSequence.objects.get(client_profile=profile)
        assert seq.last_value == 2

    def test_manual_number_collision_raises_spanish_error(self, issuer):
        profile = make_profile()
        Document.objects.create(
            document_type=get_collection_account_document_type(),
            title='Legacy',
            public_number='PA-2026-0007',
            total=Decimal('1'),
        )
        with pytest.raises(CollectionAccountError) as exc:
            allocate_client_number(
                profile, issuer, manual_number='PA-2026-0007',
            )
        assert 'ya está en uso' in str(exc.value)

    def test_manual_number_fast_forwards_own_series(self, issuer):
        profile = make_profile()
        manual = allocate_client_number(
            profile, issuer, manual_number='PA-ACMESOLU-009',
        )
        assert manual == 'PA-ACMESOLU-009'
        assert allocate_client_number(profile, issuer) == 'PA-ACMESOLU-010'

    def test_deleting_a_cuenta_leaves_a_hole_instead_of_reusing_its_number(
        self, issuer,
    ):
        """A hole in the series can be explained; two documents sharing a
        number cannot. The sequence only moves forward, so removing the row
        that held 002 must not hand 002 to the next cuenta."""
        profile = make_profile()
        allocate_client_number(profile, issuer)
        second = Document.objects.create(
            document_type=get_collection_account_document_type(),
            title='Por error',
            public_number=allocate_client_number(profile, issuer),
            total=Decimal('1'),
        )
        assert second.public_number == 'PA-ACMESOLU-002'

        delete_collection_account(second)

        assert allocate_client_number(profile, issuer) == 'PA-ACMESOLU-003'

    def test_peek_suggests_without_consuming(self, issuer):
        profile = make_profile()
        code, suggested = peek_next_client_number(profile, issuer)
        assert (code, suggested) == ('ACMESOLU', 'PA-ACMESOLU-001')
        # Peeking again yields the same suggestion; allocating then takes it.
        assert peek_next_client_number(profile, issuer)[1] == 'PA-ACMESOLU-001'
        assert allocate_client_number(profile, issuer) == 'PA-ACMESOLU-001'
