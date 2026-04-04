"""Tests for email_template_registry utility functions."""
from content.services.email_template_registry import (
    EMAIL_TEMPLATE_REGISTRY,
    get_all_keys,
    get_default_field_values,
    get_registry,
    get_template_entry,
    resolve_field_values,
    substitute_variables,
)


class TestGetRegistry:
    def test_returns_full_registry_dict(self):
        result = get_registry()

        assert result is EMAIL_TEMPLATE_REGISTRY
        assert isinstance(result, dict)
        assert len(result) > 0


class TestGetTemplateEntry:
    def test_returns_entry_for_known_key(self):
        entry = get_template_entry('proposal_sent_client')

        assert entry is not None
        assert entry['name'] == 'Propuesta Enviada'
        assert entry['category'] == 'client'

    def test_returns_none_for_unknown_key(self):
        entry = get_template_entry('nonexistent_key')

        assert entry is None


class TestGetAllKeys:
    def test_returns_list_of_all_keys(self):
        keys = get_all_keys()

        assert isinstance(keys, list)
        assert 'proposal_sent_client' in keys
        assert 'proposal_reminder' in keys
        assert 'contact_notification' in keys


class TestGetDefaultFieldValues:
    def test_returns_defaults_for_known_template(self):
        defaults = get_default_field_values('proposal_sent_client')

        assert isinstance(defaults, dict)
        assert 'subject' in defaults
        assert 'greeting' in defaults
        assert 'body' in defaults

    def test_returns_empty_dict_for_unknown_template(self):
        defaults = get_default_field_values('nonexistent_template')

        assert defaults == {}


class TestResolveFieldValues:
    def test_returns_defaults_when_no_overrides(self):
        result = resolve_field_values('proposal_sent_client')

        defaults = get_default_field_values('proposal_sent_client')
        assert result == defaults

    def test_merges_valid_overrides_into_defaults(self):
        overrides = {'greeting': 'Custom greeting'}

        result = resolve_field_values('proposal_sent_client', overrides)

        assert result['greeting'] == 'Custom greeting'

    def test_ignores_override_keys_not_in_defaults(self):
        overrides = {'nonexistent_field': 'value'}

        result = resolve_field_values('proposal_sent_client', overrides)

        assert 'nonexistent_field' not in result

    def test_ignores_empty_string_overrides(self):
        defaults = get_default_field_values('proposal_sent_client')
        original_greeting = defaults['greeting']
        overrides = {'greeting': ''}

        result = resolve_field_values('proposal_sent_client', overrides)

        assert result['greeting'] == original_greeting


class TestSubstituteVariables:
    def test_replaces_known_variables(self):
        text = 'Hello {client_name}, your project {title} is ready.'
        context = {'client_name': 'Carlos', 'title': 'E-commerce'}

        result = substitute_variables(text, context)

        assert result == 'Hello Carlos, your project E-commerce is ready.'

    def test_returns_empty_string_for_empty_text(self):
        result = substitute_variables('', {'key': 'value'})

        assert result == ''

    def test_returns_empty_string_for_none_text(self):
        result = substitute_variables(None, {'key': 'value'})

        assert result == ''

    def test_returns_original_text_for_empty_context(self):
        result = substitute_variables('Hello {name}', {})

        assert result == 'Hello {name}'

    def test_returns_original_text_for_none_context(self):
        result = substitute_variables('Hello {name}', None)

        assert result == 'Hello {name}'

    def test_leaves_unknown_placeholders_intact(self):
        text = 'Hello {client_name}, your {unknown_var} is ready.'
        context = {'client_name': 'Carlos'}

        result = substitute_variables(text, context)

        assert result == 'Hello Carlos, your {unknown_var} is ready.'

    def test_handles_format_exception_gracefully(self):
        text = 'Price is {0} and {invalid!x}'
        context = {'client_name': 'Carlos'}

        result = substitute_variables(text, context)

        assert result == text


class TestComposedEmailRegistryEntries:
    """Verify branded_email and proposal_email registry entries."""

    def test_branded_email_entry_has_required_fields(self):
        entry = get_template_entry('branded_email')
        assert entry is not None
        assert 'html_template' in entry
        assert 'txt_template' in entry
        assert 'editable_fields' in entry
        assert len(entry['editable_fields']) >= 2

    def test_proposal_email_entry_matches_branded_structure(self):
        branded = get_template_entry('branded_email')
        proposal = get_template_entry('proposal_email')
        assert proposal is not None
        for key in ('html_template', 'txt_template', 'editable_fields',
                    'available_variables', 'category'):
            assert branded[key] == proposal[key], f'{key} mismatch'
        assert branded['name'] != proposal['name']
