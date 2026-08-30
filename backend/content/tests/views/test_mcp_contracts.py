"""Contracts that make model/tool drift fail loudly during delivery."""
import re

import pytest
from django.apps import apps

from content.mcp.contracts import MCP_MODEL_CONTRACTS
from content.views.mcp_blog import TOOLS_BY_SLUG


CONNECTOR_SLUGS = tuple(MCP_MODEL_CONTRACTS)
TOOL_NAME = re.compile(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$')
pytestmark = pytest.mark.django_db


def _current_fields(model_label):
    return {
        field.name
        for field in apps.get_model(model_label)._meta.get_fields()
        if not (field.auto_created and not field.concrete)
    }


def _field_contract_problems(slug):
    problems = []
    for contract in MCP_MODEL_CONTRACTS[slug]:
        overlaps = (
            (contract.read_only & contract.read_write)
            | (contract.read_only & frozenset(contract.excluded))
            | (contract.read_write & frozenset(contract.excluded))
        )
        if overlaps:
            problems.append(
                f'{contract.model_label}: clasificación duplicada {sorted(overlaps)}'
            )
        current = _current_fields(contract.model_label)
        missing = current - contract.classified_fields
        stale = contract.classified_fields - current
        if missing:
            problems.append(
                f'{contract.model_label}: campos nuevos sin revisar {sorted(missing)}'
            )
        if stale:
            problems.append(
                f'{contract.model_label}: campos obsoletos {sorted(stale)}'
            )
        empty_reasons = sorted(
            field for field, reason in contract.excluded.items() if not reason.strip()
        )
        if empty_reasons:
            problems.append(
                f'{contract.model_label}: exclusiones sin motivo {empty_reasons}'
            )
    return problems


def _tool_contract_problems(slug):
    tools = TOOLS_BY_SLUG[slug]
    names = [tool['name'] for tool in tools]
    problems = []
    if len(names) != len(set(names)):
        problems.append('hay nombres de herramienta duplicados')
    invalid_names = sorted(name for name in names if not TOOL_NAME.fullmatch(name))
    if invalid_names:
        problems.append(f'nombres fuera de snake_case: {invalid_names}')
    short_descriptions = sorted(
        tool['name'] for tool in tools if len(tool['description'].strip()) < 40
    )
    if short_descriptions:
        problems.append(f'descripciones imprecisas: {short_descriptions}')
    invalid_schemas = sorted(
        tool['name']
        for tool in tools
        if tool.get('input_schema', {}).get('type') != 'object'
        or not isinstance(tool.get('input_schema', {}).get('properties'), dict)
    )
    if invalid_schemas:
        problems.append(f'input schemas inválidos: {invalid_schemas}')
    return problems


def test_registry_and_field_contracts_cover_the_same_connectors():
    assert set(TOOLS_BY_SLUG) == set(MCP_MODEL_CONTRACTS)


def test_documents_contract_excludes_project_inclusion_control():
    project_contract = next(
        contract
        for contract in MCP_MODEL_CONTRACTS['documents']
        if contract.model_label == 'accounts.Project'
    )

    reason = project_contract.excluded['document_manager_enabled']

    assert 'panel' in reason


@pytest.mark.parametrize('slug', CONNECTOR_SLUGS)
def test_model_fields_are_classified_for_connector(slug):
    assert _field_contract_problems(slug) == []


@pytest.mark.parametrize('slug', CONNECTOR_SLUGS)
def test_tool_metadata_is_actionable_for_connector(slug):
    assert _tool_contract_problems(slug) == []
