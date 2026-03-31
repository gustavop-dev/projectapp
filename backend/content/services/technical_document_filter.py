"""
Filter technical_document content_json by commercial module selection.

Requirements may declare linked_module_ids (or linkedModuleIds): module-{id} / group-{id}.
Rows without links are always visible (base scope).
"""

from __future__ import annotations

import copy
from typing import Any


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip()


def _norm_module_ids(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        return [s] if s else []
    if isinstance(raw, list):
        return [x.strip() for x in raw if isinstance(x, str) and x.strip()]
    return []


def _requirement_visible(req: dict, selected_set: set[str] | None) -> bool:
    ids = _norm_module_ids(req.get('linked_module_ids') or req.get('linkedModuleIds'))
    if not ids:
        return True
    if selected_set is None:
        return True
    return bool(selected_set.intersection(ids))


def _epic_gated_out(epic: dict, selected_set: set[str] | None) -> bool:
    ids = _norm_module_ids(epic.get('linked_module_ids') or epic.get('linkedModuleIds'))
    if not ids or selected_set is None:
        return False
    return not bool(selected_set.intersection(ids))


def _epic_meaningful_header(epic: dict) -> bool:
    return (
        _nonempty_str(epic.get('title'))
        or _nonempty_str(epic.get('description'))
        or _nonempty_str(epic.get('epicKey'))
    )


def filter_technical_document_by_module_selection(
    content_json: dict[str, Any] | None,
    selected_module_ids: list[str] | None,
) -> dict[str, Any]:
    """
    Return a deep copy of content_json with epics/requirements filtered.

    selected_module_ids:
        None — no module filtering (legacy / full document).
        [] or non-empty — apply visibility rules for linked_module_ids.
    """
    if not isinstance(content_json, dict):
        return {}
    out = copy.deepcopy(content_json)
    selected_set: set[str] | None = None if selected_module_ids is None else set(selected_module_ids)

    epics = out.get('epics')
    if not isinstance(epics, list):
        return out

    new_epics: list[dict] = []
    for epic in epics:
        if not isinstance(epic, dict):
            continue
        if _epic_gated_out(epic, selected_set):
            continue
        reqs_in = epic.get('requirements') or []
        if not isinstance(reqs_in, list):
            reqs_in = []
        filtered_reqs = [
            r for r in reqs_in
            if isinstance(r, dict) and _requirement_visible(r, selected_set)
        ]
        if filtered_reqs:
            ne = copy.deepcopy(epic)
            ne['requirements'] = filtered_reqs
            new_epics.append(ne)
        elif _epic_meaningful_header(epic):
            ne = copy.deepcopy(epic)
            ne['requirements'] = []
            new_epics.append(ne)

    out['epics'] = new_epics
    return out
