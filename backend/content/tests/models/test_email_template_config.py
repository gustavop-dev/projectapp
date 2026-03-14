"""Tests for EmailTemplateConfig model."""
import pytest

from content.models import EmailTemplateConfig

pytestmark = pytest.mark.django_db


class TestEmailTemplateConfigStr:
    def test_str_returns_formatted_template_key(self):
        config = EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
        )

        assert str(config) == 'EmailTemplateConfig(proposal_sent_client)'
