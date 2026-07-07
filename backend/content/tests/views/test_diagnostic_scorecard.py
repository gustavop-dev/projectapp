"""Pre-send scorecard endpoint + the send gate it powers."""
import pytest

pytestmark = pytest.mark.django_db

URL = '/api/diagnostics/{id}/scorecard/'


def _check(data, key):
    return next(c for c in data['checks'] if c['key'] == key)


def test_send_ready_diagnostic_can_send(admin_client, diagnostic):
    resp = admin_client.get(URL.format(id=diagnostic.id))
    assert resp.status_code == 200
    data = resp.json()
    assert data['can_send'] is True
    assert data['blockers'] == []
    assert data['score'] >= 1
    assert data['score'] <= 10


def test_missing_client_email_is_blocker(admin_client, diagnostic):
    diagnostic.client_email = ''
    diagnostic.save(update_fields=['client_email'])
    data = admin_client.get(URL.format(id=diagnostic.id)).json()
    assert data['can_send'] is False
    assert _check(data, 'client_email')['passed'] is False
    assert any(b['key'] == 'client_email' for b in data['blockers'])


def test_zero_investment_is_blocker(admin_client, diagnostic):
    diagnostic.investment_amount = 0
    diagnostic.save(update_fields=['investment_amount'])
    data = admin_client.get(URL.format(id=diagnostic.id)).json()
    assert any(b['key'] == 'investment_amount' for b in data['blockers'])


def test_empty_radiography_blocks_when_section_enabled(admin_client, diagnostic):
    diagnostic.radiography = {}
    diagnostic.save(update_fields=['radiography'])
    data = admin_client.get(URL.format(id=diagnostic.id)).json()
    assert any(b['key'] == 'radiography' for b in data['blockers'])


def test_radiography_not_checked_when_section_disabled(admin_client, diagnostic):
    diagnostic.radiography = {}
    diagnostic.save(update_fields=['radiography'])
    diagnostic.sections.filter(section_type='radiography').update(is_enabled=False)
    data = admin_client.get(URL.format(id=diagnostic.id)).json()
    assert all(c['key'] != 'radiography' for c in data['checks'])


def test_no_enabled_sections_is_blocker(admin_client, diagnostic):
    diagnostic.sections.update(is_enabled=False)
    data = admin_client.get(URL.format(id=diagnostic.id)).json()
    assert any(b['key'] == 'enabled_sections' for b in data['blockers'])


def test_missing_phone_fails_check_without_blocking(admin_client, diagnostic):
    data = admin_client.get(URL.format(id=diagnostic.id)).json()
    phone = _check(data, 'client_phone')
    assert phone['passed'] is False
    assert phone['blocker'] is False
    assert data['can_send'] is True


def test_send_initial_is_gated_by_blockers(admin_client, diagnostic):
    diagnostic.client_email = ''
    diagnostic.save(update_fields=['client_email'])
    resp = admin_client.post(f'/api/diagnostics/{diagnostic.id}/send-initial/')
    assert resp.status_code == 400
    data = resp.json()
    assert data['code'] == 'scorecard_blockers'
    assert 'client_email' in data['blockers']
    diagnostic.refresh_from_db()
    assert diagnostic.status == 'draft'


def test_send_final_is_gated_by_blockers(admin_client, diagnostic):
    diagnostic.status = 'negotiating'
    diagnostic.investment_amount = None
    diagnostic.save(update_fields=['status', 'investment_amount'])
    resp = admin_client.post(f'/api/diagnostics/{diagnostic.id}/send-final/')
    assert resp.status_code == 400
    assert resp.json()['code'] == 'scorecard_blockers'


def test_scorecard_requires_admin(api_client, diagnostic):
    resp = api_client.get(URL.format(id=diagnostic.id))
    assert resp.status_code in (401, 403)
