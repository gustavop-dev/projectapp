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


def test_project_has_no_module_specific_catalog_opt_out():
    project_contract = next(
        contract
        for contract in MCP_MODEL_CONTRACTS['documents']
        if contract.model_label == 'accounts.Project'
    )

    assert 'document_manager_enabled' not in _current_fields('accounts.Project')
    assert 'document_manager_enabled' not in project_contract.classified_fields


def test_document_threads_are_exposed_by_the_documents_connector():
    contracts = {
        contract.model_label: contract
        for contract in MCP_MODEL_CONTRACTS['documents']
    }

    thread = contracts['content.DocumentThread']
    assert thread.read_write == frozenset({'title'})
    assert thread.read_only == frozenset({
        'id', 'created_by', 'updated_by', 'created_at', 'updated_at',
    })
    assert thread.excluded == {}

    item = contracts['content.DocumentThreadItem']
    assert item.read_write == frozenset({'thread', 'document', 'occurred_on'})
    assert item.read_only == frozenset({
        'id', 'linked_by', 'updated_by', 'linked_at', 'updated_at',
    })
    # La posición es derivada: el conector envía fechas y el servidor ordena.
    assert set(item.excluded) == {'position'}
    assert item.excluded['position'].strip()


def test_documents_connector_registers_the_five_thread_tools():
    tool_names = {tool['name'] for tool in TOOLS_BY_SLUG['documents']}

    assert {
        'get_document_thread',
        'list_document_threads',
        'create_document_thread',
        'update_document_thread',
        'dissolve_document_thread',
    } <= tool_names
    assert len(TOOLS_BY_SLUG['documents']) == 22


@pytest.mark.parametrize('slug', CONNECTOR_SLUGS)
def test_model_fields_are_classified_for_connector(slug):
    assert _field_contract_problems(slug) == []


@pytest.mark.parametrize('slug', CONNECTOR_SLUGS)
def test_tool_metadata_is_actionable_for_connector(slug):
    assert _tool_contract_problems(slug) == []
