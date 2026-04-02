"""Tests for the ContractTemplate model."""
import pytest

from content.models import ContractTemplate

pytestmark = pytest.mark.django_db


class TestContractTemplateCreation:
    def test_str_includes_name(self, contract_template):
        assert 'Standard Contract' in str(contract_template)

    def test_str_includes_default_label_when_is_default(self, contract_template):
        assert 'default' in str(contract_template).lower() or '(default)' in str(contract_template)

    def test_str_excludes_default_label_when_not_default(self, db):
        tpl = ContractTemplate.objects.create(
            name='Custom Contract', content_markdown='# Custom', is_default=False,
        )
        result = str(tpl)
        assert 'Custom Contract' in result


class TestContractTemplateDefaultSingleton:
    def test_save_clears_other_defaults(self, contract_template):
        new_tpl = ContractTemplate.objects.create(
            name='New Default', content_markdown='# New', is_default=True,
        )
        contract_template.refresh_from_db()
        assert contract_template.is_default is False
        assert new_tpl.is_default is True

    def test_save_preserves_non_default_templates(self, contract_template):
        other = ContractTemplate.objects.create(
            name='Other', content_markdown='# Other', is_default=False,
        )
        contract_template.content_markdown = '# Updated'
        contract_template.save()
        other.refresh_from_db()
        assert other.is_default is False

    def test_get_default_returns_default_template(self, contract_template):
        result = ContractTemplate.get_default()
        assert result is not None
        assert result.pk == contract_template.pk

    def test_get_default_returns_none_when_no_default(self, db):
        ContractTemplate.objects.all().update(is_default=False)
        assert ContractTemplate.get_default() is None
