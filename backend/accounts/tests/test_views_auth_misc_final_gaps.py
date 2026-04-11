"""Tests for remaining uncovered branches in accounts/views.py — auth, profile, and misc helpers.

Covers:
- login_view: inactive user (line 105)
- resend_code_view: invalid token exception (lines 203-204)
- me_view PATCH: custom_cover_image upload (lines 278-279)
- client_list_view POST: duplicate email ValueError (lines 364-365)
- client_detail_view PATCH: is_active update (line 409)
- admin_detail_view: non-staff user rejected (line 504)
- _generate_next_payment: nil billing_start (line 2718)
- _handle_payment_approved: notification exception silenced (lines 2786-2787)
- _get_plan_discount: stored hosting_tiers match (lines 2945-2946) and linked BP fallback (2950, 2955)
- payment_card_pay_view: invalid project_id (line 3106)
- payment_verify_transaction_view: invalid project_id (line 3195)
- wompi_webhook_view: PA-pattern matches but payment not found (lines 3293-3294)
- project_subscription_view: invalid project_id (line 2840)
- project_payments_view: invalid project_id (line 2970)
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.test import APIClient

from accounts.models import (
    HostingSubscription,
    Payment,
    Project,
    UserProfile,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@authgaps.com', email='admin@authgaps.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@authgaps.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@authgaps.com', email='client@authgaps.com', password='clientpass1',
        first_name='Test', last_name='Client',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@authgaps.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Auth Gaps Project', client=client_user,
        status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def subscription(project):
    sub = HostingSubscription(
        project=project, plan=HostingSubscription.PLAN_MONTHLY,
        base_monthly_amount=Decimal('300000'), discount_percent=0,
        start_date='2026-01-01', next_billing_date='2026-02-01',
        status=HostingSubscription.STATUS_ACTIVE,
    )
    sub.calculate_amounts()
    sub.save()
    return sub


@pytest.fixture
def pending_payment(subscription):
    return Payment.objects.create(
        subscription=subscription,
        amount=subscription.billing_amount,
        description='Monthly hosting',
        billing_period_start='2026-02-01',
        billing_period_end='2026-02-28',
        due_date='2026-02-01',
        status=Payment.STATUS_PENDING,
    )


# ===========================================================================
# login_view — inactive user (line 105)
# ===========================================================================

class TestLoginViewInactiveUser:
    @patch('accounts.views.authenticate')
    def test_inactive_user_returns_403(self, mock_auth, api_client):
        """When authenticate returns an inactive user, login returns 403."""
        inactive = User(
            username='off@authgaps.com', email='off@authgaps.com', is_active=False,
        )
        mock_auth.return_value = inactive

        resp = api_client.post('/api/accounts/login/', {
            'email': 'off@authgaps.com', 'password': 'anypass',
        }, format='json')

        assert resp.status_code == 403


# ===========================================================================
# resend_code_view — invalid token exception (lines 203-204)
# ===========================================================================

class TestResendCodeViewInvalidToken:
    def test_invalid_bearer_token_returns_401(self, api_client):
        """Malformed or expired JWT token in resend-code/ triggers exception → 401."""
        resp = api_client.post(
            '/api/accounts/resend-code/',
            HTTP_AUTHORIZATION='Bearer this.is.not.a.valid.jwt.token',
        )

        assert resp.status_code == 401


# ===========================================================================
# me_view PATCH — custom_cover_image upload (lines 278-279)
# ===========================================================================

class TestMeViewCustomCoverImage:
    def test_patch_custom_cover_image_updates_profile(self, api_client, client_headers):
        """PATCH /me/ with custom_cover_image file updates the profile field."""
        from io import BytesIO
        from PIL import Image

        buf = BytesIO()
        Image.new('RGB', (1, 1), color='red').save(buf, format='JPEG')
        buf.seek(0)

        resp = api_client.patch(
            '/api/accounts/me/',
            data={'custom_cover_image': ContentFile(buf.read(), name='cover.jpg')},
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 200


# ===========================================================================
# client_list_view POST — duplicate email ValueError (lines 364-365)
# ===========================================================================

class TestClientListViewDuplicateEmail:
    def test_duplicate_email_returns_400(self, api_client, admin_headers, client_user):
        """POST /clients/ with existing email raises ValueError → 400."""
        resp = api_client.post('/api/accounts/clients/', {
            'email': client_user.email,  # already exists
            'first_name': 'Dup',
            'last_name': 'Client',
        }, format='json', **admin_headers)

        assert resp.status_code == 400


# ===========================================================================
# client_detail_view PATCH — is_active update (line 409)
# ===========================================================================

class TestClientDetailViewIsActive:
    def test_admin_can_deactivate_client(self, api_client, admin_headers, client_user):
        """PATCH /clients/{id}/ with is_active=false deactivates the user."""
        resp = api_client.patch(
            f'/api/accounts/clients/{client_user.id}/',
            {'is_active': False},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 200
        client_user.refresh_from_db()
        assert client_user.is_active is False


# ===========================================================================
# admin_detail_view — non-staff user rejected (line 504)
# ===========================================================================

class TestAdminDetailViewNonStaff:
    def test_non_staff_admin_returns_403(self, api_client, admin_headers, admin_user):
        """Non-staff admin accessing admin_detail_view gets 403 (requires is_staff)."""
        resp = api_client.get(
            f'/api/accounts/admins/{admin_user.id}/',
            **admin_headers,
        )

        assert resp.status_code == 403


# ===========================================================================
# _generate_next_payment — nil billing_start (line 2718)
# ===========================================================================

class TestGenerateNextPaymentNilStart:
    def test_returns_none_when_next_billing_date_is_none(self, subscription):
        """_generate_next_payment returns None immediately when next_billing_date is None."""
        from accounts.views import _generate_next_payment

        # Set next_billing_date to None in memory without DB save (avoids NOT NULL constraint)
        subscription.next_billing_date = None

        result = _generate_next_payment(subscription)

        assert result is None


# ===========================================================================
# _handle_payment_approved — notification exception silenced (lines 2786-2787)
# ===========================================================================

class TestHandlePaymentApprovedNotificationException:
    @patch('accounts.services.notifications.notify', side_effect=Exception('notify fail'))
    def test_notification_exception_is_silenced(self, mock_notify, project, subscription, pending_payment):
        """Exception in the notification block is caught and logged — payment is still updated."""
        from accounts.views import _handle_payment_approved

        # Refresh to get proper date objects (string dates from create() cause TypeError in date arithmetic)
        pending_payment.refresh_from_db()

        _handle_payment_approved(pending_payment, 'test')

        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.STATUS_PAID


# ===========================================================================
# _get_plan_discount — stored hosting_tiers match (lines 2945-2946)
# ===========================================================================

class TestGetPlanDiscountStoredTiers:
    def test_returns_discount_from_matching_tier(self, project):
        """When project.hosting_tiers has a matching frequency, its discount_percent is returned."""
        from accounts.views import _get_plan_discount

        project.hosting_tiers = [
            {'frequency': 'monthly', 'discount_percent': 0},
            {'frequency': 'quarterly', 'discount_percent': 15},
        ]
        project.save(update_fields=['hosting_tiers'])

        result = _get_plan_discount(project, 'quarterly')

        assert result == 15

    def test_returns_discount_from_linked_bp_when_no_tier_match(
        self, project, subscription,
    ):
        """Falls back to linked BusinessProposal when no matching tier in project.hosting_tiers."""
        from content.models import BusinessProposal
        from accounts.models import Deliverable
        from accounts.views import _get_plan_discount

        project.hosting_tiers = [{'frequency': 'monthly', 'discount_percent': 0}]
        project.save(update_fields=['hosting_tiers'])

        d = Deliverable.objects.create(
            project=project, title='BP Deliverable',
            category=Deliverable.CATEGORY_DOCUMENTS,
            uploaded_by=subscription.project.client,
        )
        BusinessProposal.objects.create(
            title='Test BP', client_name='Client',
            hosting_discount_quarterly=12,
            hosting_discount_semiannual=22,
            deliverable=d,
        )

        result = _get_plan_discount(project, 'quarterly')

        assert result == 12


# ===========================================================================
# payment_card_pay_view — invalid project_id returns 404 (line 3106)
# ===========================================================================

class TestPaymentCardPayInvalidProject:
    def test_invalid_project_returns_404(self, api_client, client_headers):
        """payment_card_pay_view returns 404 when project_id does not exist."""
        url = '/api/accounts/projects/99999/payments/1/card-pay/'
        resp = api_client.post(url, {}, format='json', **client_headers)

        assert resp.status_code == 404


# ===========================================================================
# payment_verify_transaction_view — invalid project_id returns 404 (line 3195)
# ===========================================================================

class TestPaymentVerifyInvalidProject:
    def test_invalid_project_returns_404(self, api_client, client_headers):
        """payment_verify_transaction_view returns 404 when project_id does not exist."""
        url = '/api/accounts/projects/99999/payments/1/verify/'
        resp = api_client.post(url, {'transaction_id': 'x'}, format='json', **client_headers)

        assert resp.status_code == 404


# ===========================================================================
# wompi_webhook_view — PA-pattern matches but payment not found (lines 3293-3294)
# ===========================================================================

class TestWompiWebhookPaPatternNotFound:
    def test_pa_pattern_with_nonexistent_payment_id_not_found(self, api_client):
        """PA-pattern reference with non-existent payment ID falls through to 404."""
        reference = 'PA99999P1T1234567890'
        resp = api_client.post('/api/accounts/webhooks/wompi/', {
            'event': 'transaction.updated',
            'data': {
                'transaction': {
                    'id': 'txn_pa_miss',
                    'status': 'APPROVED',
                    'reference': reference,
                },
            },
        }, format='json')

        assert resp.status_code == 404


# ===========================================================================
# project_subscription_view — invalid project_id (line 2840)
# ===========================================================================

class TestProjectSubscriptionInvalidProject:
    def test_invalid_project_returns_404(self, api_client, client_headers):
        """project_subscription_view returns 404 when project_id does not exist."""
        url = '/api/accounts/projects/99999/subscription/'
        resp = api_client.get(url, **client_headers)

        assert resp.status_code == 404


# ===========================================================================
# project_payments_view — invalid project_id (line 2970)
# ===========================================================================

class TestProjectPaymentsInvalidProject:
    def test_invalid_project_returns_404(self, api_client, client_headers):
        """project_payments_view returns 404 when project_id does not exist."""
        url = '/api/accounts/projects/99999/payments/'
        resp = api_client.get(url, **client_headers)

        assert resp.status_code == 404
