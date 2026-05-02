"""Tests for the diagnostic markdown template admin endpoints."""
import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


class TestListDiagnosticTemplates:
    def test_returns_three_templates(self, admin_client):
        url = reverse('list-diagnostic-templates')
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        slugs = {item['slug'] for item in data}
        assert slugs == {'diagnostico-aplicacion', 'diagnostico-tecnico', 'anexo'}
        for item in data:
            assert item['title']
            assert item['filename'].endswith('.md')
            assert item['size_bytes'] > 0
            assert item['updated_at']

    def test_requires_admin(self, client):
        url = reverse('list-diagnostic-templates')
        response = client.get(url)
        assert response.status_code in (401, 403)


class TestGetDiagnosticTemplate:
    def test_returns_markdown_content(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'diagnostico-aplicacion'},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data['slug'] == 'diagnostico-aplicacion'
        assert data['filename'] == 'diagnostico_aplicacion_es.md'
        assert isinstance(data['content_markdown'], str)
        assert len(data['content_markdown']) > 100

    def test_returns_404_for_unknown_slug(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'inexistente'},
        )
        response = admin_client.get(url)
        assert response.status_code == 404

    def test_without_diagnostic_id_keeps_placeholders_intact(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'diagnostico-aplicacion'},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        markdown = response.json()['content_markdown']
        assert '{{investment_amount}}' in markdown
        assert '{{payment_initial_pct}}' in markdown
        assert '{{payment_final_pct}}' in markdown
        assert '{{currency}}' in markdown
        assert '{{duration_label}}' in markdown

    # quality: disable too_many_assertions (10 assertions verify one contract: 5 placeholder-removal checks + 4 value-injection checks + status)
    def test_with_diagnostic_id_substitutes_placeholders(
        self, admin_client, diagnostic,
    ):
        diagnostic.investment_amount = 5000000
        diagnostic.currency = 'COP'
        diagnostic.duration_label = '1 semana'
        diagnostic.payment_terms = {'initial_pct': 60, 'final_pct': 40}
        diagnostic.save(update_fields=[
            'investment_amount', 'currency', 'duration_label', 'payment_terms',
        ])

        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'diagnostico-aplicacion'},
        )
        response = admin_client.get(url, {'diagnostic_id': diagnostic.id})
        assert response.status_code == 200
        markdown = response.json()['content_markdown']
        assert '{{investment_amount}}' not in markdown
        assert '{{payment_initial_pct}}' not in markdown
        assert '{{payment_final_pct}}' not in markdown
        assert '{{currency}}' not in markdown
        assert '{{duration_label}}' not in markdown
        assert '60% al inicio' in markdown
        assert '40% al final' in markdown
        assert 'COP' in markdown
        assert '1 semana' in markdown

    def test_with_unknown_diagnostic_id_returns_404(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'diagnostico-aplicacion'},
        )
        response = admin_client.get(url, {'diagnostic_id': 999999})
        assert response.status_code == 404

    def test_anexo_no_longer_contains_fuente_section(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'anexo'},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        markdown = response.json()['content_markdown']
        assert 'Fuente de la medición preliminar' not in markdown
        assert 'levantamiento técnico medido' not in markdown

    def test_investment_amount_has_dollar_sign(self, admin_client, diagnostic):
        diagnostic.investment_amount = 5000000
        diagnostic.currency = 'COP'
        diagnostic.duration_label = '1 semana'
        diagnostic.save(update_fields=['investment_amount', 'currency', 'duration_label'])

        url = reverse('get-diagnostic-template', kwargs={'slug': 'diagnostico-aplicacion'})
        markdown = admin_client.get(url, {'diagnostic_id': diagnostic.id}).json()['content_markdown']
        assert '$' in markdown
        assert '{{investment_amount}}' not in markdown

    def test_missing_investment_amount_shows_pending_text(self, admin_client, diagnostic):
        diagnostic.investment_amount = None
        diagnostic.duration_label = '1 semana'
        diagnostic.save(update_fields=['investment_amount', 'duration_label'])

        url = reverse('get-diagnostic-template', kwargs={'slug': 'diagnostico-aplicacion'})
        markdown = admin_client.get(url, {'diagnostic_id': diagnostic.id}).json()['content_markdown']
        assert 'pendiente de definir' in markdown
        assert '{{investment_amount}}' not in markdown

    def test_missing_duration_label_shows_pending_text(self, admin_client, diagnostic):
        diagnostic.investment_amount = 5000000
        diagnostic.duration_label = ''
        diagnostic.save(update_fields=['investment_amount', 'duration_label'])

        url = reverse('get-diagnostic-template', kwargs={'slug': 'diagnostico-aplicacion'})
        markdown = admin_client.get(url, {'diagnostic_id': diagnostic.id}).json()['content_markdown']
        assert 'pendiente de definir' in markdown
        assert '{{duration_label}}' not in markdown
