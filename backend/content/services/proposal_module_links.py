"""
Canonical commercial-module ids shared by technical_document filtering and admin editing.
"""

from __future__ import annotations

import copy
from typing import Any


def _string_id(value: Any) -> str:
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return value.strip()


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        value = _string_id(raw)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def build_proposal_module_link_catalog(sections: list[dict] | None) -> dict[str, Any]:
    options: list[dict[str, Any]] = []
    alias_map: dict[str, str] = {}
    always_included_ids: list[str] = []

    if not isinstance(sections, list):
        return {
            'options': options,
            'alias_map': alias_map,
            'always_included_ids': always_included_ids,
        }

    def add_option(option: dict[str, Any]) -> None:
        options.append(option)
        for alias in option.get('aliases', []):
            alias_map[alias] = option['id']
        if option.get('is_always_included'):
            always_included_ids.append(option['id'])

    fr = next(
        (section for section in sections if section.get('section_type') == 'functional_requirements'),
        None,
    )
    inv = next(
        (section for section in sections if section.get('section_type') == 'investment'),
        None,
    )
    content_json = fr.get('content_json') if isinstance(fr, dict) else {}
    groups = []
    if isinstance(content_json, dict):
        groups.extend(content_json.get('groups') or [])
        groups.extend(content_json.get('additionalModules') or [])

    for group in groups:
        if not isinstance(group, dict) or group.get('is_visible') is False:
            continue
        raw_id = _string_id(group.get('id'))
        if not raw_id:
            continue
        if not group.get('title') and not (group.get('items') or []):
            continue
        is_calc = group.get('is_calculator_module') is True
        canonical_id = f'module-{raw_id}' if is_calc else f'group-{raw_id}'
        label = f'{group.get("icon") or ""} {group.get("title") or raw_id}'.strip()
        price_percent = group.get('price_percent') or 0
        try:
            price_percent = float(price_percent)
        except (TypeError, ValueError):
            price_percent = 0
        is_always_included = (
            price_percent == 0 and not group.get('is_invite')
            if is_calc
            else price_percent == 0
        )
        aliases = _unique_strings([canonical_id, raw_id])
        add_option({
            'id': canonical_id,
            'label': label,
            'aliases': aliases,
            'is_always_included': is_always_included,
        })

    inv_content = inv.get('content_json') if isinstance(inv, dict) else {}
    modules = inv_content.get('modules') if isinstance(inv_content, dict) else []
    for module in modules or []:
        if not isinstance(module, dict):
            continue
        module_id = _string_id(module.get('id'))
        if not module_id:
            continue
        label = f'{module.get("icon") or ""} {module.get("title") or module_id}'.strip()
        add_option({
            'id': module_id,
            'label': label,
            'aliases': [module_id],
            'is_always_included': module.get('is_required') is True,
        })

    return {
        'options': options,
        'alias_map': alias_map,
        'always_included_ids': _unique_strings(always_included_ids),
    }


def normalize_linked_module_ids(raw: Any, alias_map: dict[str, str] | None = None) -> list[str]:
    alias_map = alias_map or {}
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = raw
    else:
        values = []
    return _unique_strings([
        alias_map.get(_string_id(value), _string_id(value))
        for value in values
    ])


def normalize_technical_document_module_links(
    content_json: dict[str, Any] | None,
    sections: list[dict] | None,
) -> dict[str, Any]:
    if not isinstance(content_json, dict):
        return {}

    catalog = build_proposal_module_link_catalog(sections)
    alias_map = catalog['alias_map']
    out = copy.deepcopy(content_json)
    epics = out.get('epics')
    if not isinstance(epics, list):
        return out

    normalized_epics: list[dict[str, Any]] = []
    for epic in epics:
        if not isinstance(epic, dict):
            continue
        normalized_epic = copy.deepcopy(epic)
        normalized_epic.pop('linkedModuleIds', None)
        normalized_epic['linked_module_ids'] = normalize_linked_module_ids(
            epic.get('linked_module_ids') or epic.get('linkedModuleIds'),
            alias_map,
        )
        requirements = epic.get('requirements')
        if isinstance(requirements, list):
            normalized_requirements: list[dict[str, Any]] = []
            for requirement in requirements:
                if not isinstance(requirement, dict):
                    continue
                normalized_requirement = copy.deepcopy(requirement)
                normalized_requirement.pop('linkedModuleIds', None)
                normalized_requirement['linked_module_ids'] = normalize_linked_module_ids(
                    requirement.get('linked_module_ids') or requirement.get('linkedModuleIds'),
                    alias_map,
                )
                normalized_requirements.append(normalized_requirement)
            normalized_epic['requirements'] = normalized_requirements
        normalized_epics.append(normalized_epic)

    out['epics'] = normalized_epics
    return out
