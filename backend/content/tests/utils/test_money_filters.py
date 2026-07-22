"""Tests for the `cop` template filter (COP amounts in email templates)."""
from decimal import Decimal

from django.template import Context, Template


def render_cop(value):
    return Template('{% load money_filters %}${{ v|cop }}').render(Context({'v': value}))


class TestCopFilter:
    def test_formats_decimal_with_separators(self):
        # Autoescape (HTML emails) escapes the millions apostrophe; renders
        # identically in mail clients.
        assert render_cop(Decimal('6476857.00')) == "$6&#x27;476.857"

    def test_plain_text_context_keeps_raw_apostrophe(self):
        rendered = Template(
            '{% load money_filters %}{% autoescape off %}${{ v|cop }}{% endautoescape %}'
        ).render(Context({'v': Decimal('6476857.00')}))
        assert rendered == "$6'476.857"

    def test_formats_thousands_without_apostrophe(self):
        assert render_cop(Decimal('550002.00')) == '$550.002'

    def test_none_renders_empty(self):
        assert render_cop(None) == '$'
