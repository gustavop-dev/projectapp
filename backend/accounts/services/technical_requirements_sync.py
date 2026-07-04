"""
Sync platform data from a BusinessProposal into the client's project:

* ``ProjectScopeItem`` rows mirror the commercial vistas/componentes/funcionalidades
  from the ``functional_requirements`` section (the client-facing grouping backbone
  for the Kanban).
* ``Requirement`` cards (the trackable work) are upserted from the
  ``technical_document`` epics/requirements and linked to their primary scope item
  via ``linked_item_ids``.
* ``Deliverable`` (one per epic) and ``DataModelEntity`` rows keep mirroring the
  ``technical_document`` epics/dataModel as before.

Requirements are phase-scoped (rebuilt around ``ProjectPhase`` after the 2026-05-17
refactor); ``_ensure_phase`` guarantees a phase exists before any card is attached.
Re-sync is idempotent and preserves client/team-owned Kanban state (status, order,
comments); proposal-authored content is overwritten unless ``content_overridden``.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max

from accounts.models import (
    DataModelEntity,
    Deliverable,
    ProjectPhase,
    ProjectScopeItem,
    Requirement,
)
from accounts.services.archive import archive_record, unarchive_record
from content.models import ProposalSection
from content.services.proposal_module_links import (
    ensure_functional_requirements_item_ids,
    normalize_linked_module_ids,
)

User = get_user_model()


def _str(value: Any) -> str:
    """Normalize any value to a stripped string ('' for None)."""
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return value.strip()


def _map_priority(value: Any) -> str:
    """Map a proposal priority string to a valid Requirement priority (default medium)."""
    v = _str(value).lower()
    valid = {choice[0] for choice in Requirement.PRIORITY_CHOICES}
    return v if v in valid else Requirement.PRIORITY_MEDIUM


def _ensure_phase(project, bp) -> ProjectPhase:
    """
    Return the ProjectPhase for (project, bp), creating it if missing.

    The acceptance/onboarding path creates a Project + root Deliverable but no
    ProjectPhase; since Requirements/ProjectScopeItems are phase-scoped, this
    closes that gap. Keyed on the unique (project, business_proposal).
    """
    phase = ProjectPhase.objects.filter(project=project, business_proposal=bp).first()
    if phase:
        return phase
    next_order = (project.phases.aggregate(m=Max('order'))['m'] or 0) + 1
    return ProjectPhase.objects.create(
        project=project, business_proposal=bp, order=next_order,
    )


def _read_functional_requirements(bp) -> dict[str, Any] | None:
    """
    Return the proposal's functional_requirements content_json with item ids
    ensured (in memory only), or None if the section is absent/disabled.
    """
    section = (
        ProposalSection.objects.filter(
            proposal=bp,
            section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
            is_enabled=True,
        )
        .values('content_json')
        .first()
    )
    if not section:
        return None
    return ensure_functional_requirements_item_ids(section['content_json'] or {})


def _sync_scope_items(phase, fr_json: dict[str, Any], stats: dict[str, Any]) -> dict[str, ProjectScopeItem]:
    """
    Upsert ProjectScopeItem rows (keyed by source_item_id) from a
    functional_requirements content_json. Faithful mirror of every group in
    ``groups`` + ``additionalModules`` (incl. hidden groups). Scope items carry
    no client-owned state, so descriptive fields are always overwritten and
    re-added items are resurrected; items removed from the proposal are archived.

    Returns {source_item_id: ProjectScopeItem} for requirement linking.
    """
    scope_by_source: dict[str, ProjectScopeItem] = {}
    if not isinstance(fr_json, dict):
        return scope_by_source

    seen_item_ids: set[str] = set()
    group_order = 0

    for section_key in ('groups', 'additionalModules'):
        entries = fr_json.get(section_key)
        if not isinstance(entries, list):
            continue
        origin = (
            ProjectScopeItem.ORIGIN_ADDITIONAL
            if section_key == 'additionalModules'
            else ProjectScopeItem.ORIGIN_GROUP
        )
        for group in entries:
            if not isinstance(group, dict):
                continue
            gid = _str(group.get('id'))[:200]
            gtitle = _str(group.get('title'))[:300]
            gicon = _str(group.get('icon'))[:50]
            gvisible = group.get('is_visible') is not False
            item_order = 0
            for item in group.get('items') or []:
                if not isinstance(item, dict):
                    continue
                sid = _str(item.get('id'))
                if not sid:
                    continue
                seen_item_ids.add(sid)
                defaults = {
                    'origin': origin,
                    'group_id': gid,
                    'group_title': gtitle,
                    'group_icon': gicon,
                    'group_order': group_order,
                    'group_is_visible': gvisible,
                    'name': _str(item.get('name'))[:300] or sid[:300],
                    'description': (item.get('description') or '')[:5000],
                    'icon': _str(item.get('icon'))[:50],
                    'item_order': item_order,
                    'synced_from_proposal': True,
                }
                si, created = ProjectScopeItem.objects.get_or_create(
                    phase=phase, source_item_id=sid, defaults=defaults,
                )
                if created:
                    stats['scope_items_created'] += 1
                else:
                    changed = [f for f, v in defaults.items() if getattr(si, f) != v]
                    if changed:
                        for f in changed:
                            setattr(si, f, defaults[f])
                        si.save(update_fields=changed + ['updated_at'])
                        stats['scope_items_updated'] += 1
                    if si.is_archived:
                        unarchive_record(si)
                        stats['scope_items_unarchived'] += 1
                scope_by_source[sid] = si
                item_order += 1
            group_order += 1

    # Archive scope items removed from the proposal (safe: no client-owned state).
    for si in (
        ProjectScopeItem.objects.filter(phase=phase, is_archived=False)
        .exclude(source_item_id__in=seen_item_ids)
    ):
        archive_record(si)
        stats['scope_items_archived'] += 1

    return scope_by_source


def _parse_epics_from_json(content_json: dict) -> list:
    """Extract and normalize the epics list from a technical_document content_json."""
    epics = (content_json or {}).get('epics') or []
    return epics if isinstance(epics, list) else []


def _parse_data_model_entities(content_json: dict) -> list:
    """Extract and normalize the entities list from a technical_document content_json."""
    dm = (content_json or {}).get('dataModel') or {}
    entities = dm.get('entities') or []
    return entities if isinstance(entities, list) else []


def compute_sync_diff(project, new_content_json: dict) -> dict[str, Any]:
    """
    Compute a read-only diff between the new_content_json and the current DB state
    for the given project. Never writes to the database.

    Returns a dict with 'epics' and 'requirements', each containing
    'to_create', 'to_update' (with changed_fields), and 'to_delete' lists.
    """
    epics_list = _parse_epics_from_json(new_content_json)

    # Build lookup of current non-archived Deliverables by source_epic_key
    current_deliverables = {
        d.source_epic_key: d
        for d in Deliverable.objects.filter(
            project=project,
            source_epic_key__isnull=False,
            is_archived=False,
        )
        if d.source_epic_key
    }

    # Build lookup of current non-archived Requirements by source_flow_key
    current_requirements = {
        r.source_flow_key: r
        for r in Requirement.objects.filter(
            phase__project=project,
            source_flow_key__isnull=False,
            is_archived=False,
        )
        if r.source_flow_key
    }

    diff: dict[str, Any] = {
        'epics': {'to_create': [], 'to_update': [], 'to_delete': []},
        'requirements': {'to_create': [], 'to_update': [], 'to_delete': []},
        'data_model_entities': {'to_create': [], 'to_update': [], 'to_delete': []},
    }

    seen_epic_keys: set[str] = set()
    seen_flow_keys: set[str] = set()

    for idx, epic in enumerate(epics_list):
        if not isinstance(epic, dict):
            continue
        key = (epic.get('epicKey') or '').strip()
        title = (epic.get('title') or '').strip() or key or f'Módulo {idx + 1}'
        description = (epic.get('description') or '')
        reqs = epic.get('requirements') or []
        if not isinstance(reqs, list):
            reqs = []

        if not key:
            if not reqs:
                continue
            key = f'_sync_epic_{idx}'

        seen_epic_keys.add(key)

        if key not in current_deliverables:
            diff['epics']['to_create'].append({'epicKey': key, 'title': title})
        else:
            d = current_deliverables[key]
            changed: list[str] = []
            if d.title != title[:300]:
                changed.append('title')
            if d.description != description[:2000]:
                changed.append('description')
            if changed:
                diff['epics']['to_update'].append({'epicKey': key, 'title': title, 'changed_fields': changed})

        for r in reqs:
            if not isinstance(r, dict):
                continue
            flow_key = (r.get('flowKey') or '').strip()
            r_title = (r.get('title') or '').strip()
            if not r_title or not flow_key:
                continue

            seen_flow_keys.add(flow_key)
            flow_text = (r.get('usageFlow') or r.get('flow') or '')[:5000]
            conf = (r.get('configuration') or '')[:5000]
            desc = (r.get('description') or '')[:5000]

            if flow_key not in current_requirements:
                diff['requirements']['to_create'].append({
                    'flowKey': flow_key, 'title': r_title, 'epicKey': key,
                })
            else:
                req = current_requirements[flow_key]
                changed_r: list[str] = []
                if req.title != r_title[:300]:
                    changed_r.append('title')
                if req.description != desc:
                    changed_r.append('description')
                if req.flow != flow_text:
                    changed_r.append('flow')
                if req.configuration != conf:
                    changed_r.append('configuration')
                if changed_r:
                    diff['requirements']['to_update'].append({
                        'flowKey': flow_key, 'title': r_title, 'epicKey': key,
                        'changed_fields': changed_r,
                    })

    # Records that exist in DB but are not in the new JSON → to_delete
    for key, d in current_deliverables.items():
        if key not in seen_epic_keys:
            diff['epics']['to_delete'].append({'epicKey': key, 'title': d.title})

    for flow_key, req in current_requirements.items():
        if flow_key not in seen_flow_keys:
            diff['requirements']['to_delete'].append({
                'flowKey': flow_key, 'title': req.title,
                'epicKey': req.source_epic_key or '',
            })

    # --- Data model entities diff ---
    # Entities are duplicated per deliverable; diff only needs one representative
    # per source_entity_name, so we use setdefault to keep the first occurrence.
    entities_list = _parse_data_model_entities(new_content_json)
    current_entities: dict[str, DataModelEntity] = {}
    for e in DataModelEntity.objects.filter(
        deliverable__project=project,
        is_archived=False,
    ):
        if e.source_entity_name:
            current_entities.setdefault(e.source_entity_name, e)
    seen_entity_names: set[str] = set()

    for ent in entities_list:
        if not isinstance(ent, dict):
            continue
        ent_name = (ent.get('name') or '').strip()
        if not ent_name:
            continue
        seen_entity_names.add(ent_name)
        ent_desc = (ent.get('description') or '').strip()
        ent_kf = (ent.get('keyFields') or '').strip()

        if ent_name not in current_entities:
            diff['data_model_entities']['to_create'].append({
                'name': ent_name, 'description': ent_desc,
            })
        else:
            existing = current_entities[ent_name]
            changed_e: list[str] = []
            if existing.description != ent_desc:
                changed_e.append('description')
            if existing.key_fields != ent_kf:
                changed_e.append('key_fields')
            if changed_e:
                diff['data_model_entities']['to_update'].append({
                    'name': ent_name, 'changed_fields': changed_e,
                })

    for ent_name, ent_obj in current_entities.items():
        if ent_name not in seen_entity_names:
            diff['data_model_entities']['to_delete'].append({'name': ent_name})

    return diff


def _sync_technical_requirements_core(
    project,
    bp,
    acting_user: User,
    delete_removed: bool = False,
) -> dict[str, Any]:
    """
    Upsert, from the linked proposal:
      * ProjectScopeItem rows (per functional_requirements item) — grouping backbone;
      * one Deliverable per epic (by source_epic_key);
      * Requirement cards per flowKey, linked to their primary scope item;
      * DataModelEntity rows (per dataModel entity).
    Skips requirement rows without title or without flowKey. Preserves client-owned
    Kanban state on re-sync (see module docstring).
    """
    section = (
        ProposalSection.objects.filter(
            proposal=bp,
            section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
            is_enabled=True,
        )
        .values('content_json')
        .first()
    )
    if not section:
        return {'ok': False, 'error': 'no_technical_section', 'detail': 'No hay sección técnica habilitada en la propuesta.'}

    doc = section['content_json'] or {}
    epics = doc.get('epics') or []
    if not isinstance(epics, list):
        epics = []

    stats = {
        'ok': True,
        'epics_processed': 0,
        'scope_items_created': 0,
        'scope_items_updated': 0,
        'scope_items_unarchived': 0,
        'scope_items_archived': 0,
        'deliverables_created': 0,
        'deliverables_updated': 0,
        'deliverables_deleted': 0,
        'requirements_created': 0,
        'requirements_updated': 0,
        'requirements_skipped': 0,
        'requirements_deleted': 0,
        'entities_created': 0,
        'entities_updated': 0,
        'entities_deleted': 0,
    }

    with transaction.atomic():
        phase = _ensure_phase(project, bp)
        fr_json = _read_functional_requirements(bp)
        scope_by_source = (
            _sync_scope_items(phase, fr_json, stats) if fr_json is not None else {}
        )

        seen_epic_keys: set[str] = set()
        seen_flow_keys: set[str] = set()
        synced_deliverables: list[Deliverable] = []
        next_req_order = (
            Requirement.objects.filter(phase=phase).aggregate(m=Max('order'))['m'] or 0
        ) + 1

        for idx, epic in enumerate(epics):
            if not isinstance(epic, dict):
                continue
            key = (epic.get('epicKey') or '').strip()
            title = (epic.get('title') or '').strip() or key or f'Módulo {idx + 1}'
            description = epic.get('description') or ''
            reqs = epic.get('requirements') or []
            if not isinstance(reqs, list):
                reqs = []

            if not key:
                if not reqs:
                    continue
                key = f'_sync_epic_{idx}'

            seen_epic_keys.add(key)

            d, created = Deliverable.objects.get_or_create(
                project=project,
                source_epic_key=key,
                defaults={
                    'category': Deliverable.CATEGORY_DOCUMENTS,
                    'title': title[:300],
                    'description': (description or '')[:2000],
                    'file': None,
                    'uploaded_by': acting_user,
                    'source_epic_title': title[:300],
                },
            )
            synced_deliverables.append(d)
            if created:
                stats['deliverables_created'] += 1
            else:
                updated = False
                if d.title != title[:300]:
                    d.title = title[:300]
                    updated = True
                if d.source_epic_title != title[:300]:
                    d.source_epic_title = title[:300]
                    updated = True
                if d.description != (description or '')[:2000]:
                    d.description = (description or '')[:2000]
                    updated = True
                if updated:
                    d.save()
                    stats['deliverables_updated'] += 1

            stats['epics_processed'] += 1

            for r in reqs:
                if not isinstance(r, dict):
                    stats['requirements_skipped'] += 1
                    continue
                flow_key = _str(r.get('flowKey'))
                r_title = _str(r.get('title'))
                if not flow_key or not r_title:
                    stats['requirements_skipped'] += 1
                    continue
                seen_flow_keys.add(flow_key)

                r_desc = (r.get('description') or '')[:5000]
                r_flow = (r.get('usageFlow') or r.get('flow') or '')[:5000]
                r_conf = (r.get('configuration') or '')[:5000]
                r_priority = _map_priority(r.get('priority'))

                # Primary scope item = first linked_item_id that resolves in this phase.
                scope_item = None
                for sid in normalize_linked_module_ids(
                    r.get('linked_item_ids') or r.get('linkedItemIds')
                ):
                    if sid in scope_by_source:
                        scope_item = scope_by_source[sid]
                        break

                req, created = Requirement.objects.get_or_create(
                    phase=phase,
                    source_flow_key=flow_key,
                    defaults={
                        'title': r_title[:300],
                        'description': r_desc,
                        'flow': r_flow,
                        'configuration': r_conf,
                        'priority': r_priority,
                        'status': Requirement.STATUS_BACKLOG,
                        'order': next_req_order,
                        'source_epic_key': key[:200],
                        'source_epic_title': title[:300],
                        'scope_item': scope_item,
                        'synced_from_proposal': True,
                    },
                )
                if created:
                    stats['requirements_created'] += 1
                    next_req_order += 1
                    continue

                # Existing card: re-point grouping/provenance every sync; overwrite
                # proposal-authored content unless an admin has taken it over.
                changed: list[str] = []
                new_scope_id = scope_item.id if scope_item else None
                if req.scope_item_id != new_scope_id:
                    req.scope_item = scope_item
                    changed.append('scope_item')
                if req.source_epic_key != key[:200]:
                    req.source_epic_key = key[:200]
                    changed.append('source_epic_key')
                if req.source_epic_title != title[:300]:
                    req.source_epic_title = title[:300]
                    changed.append('source_epic_title')
                if not req.synced_from_proposal:
                    req.synced_from_proposal = True
                    changed.append('synced_from_proposal')
                if not req.content_overridden:
                    for field, value in (
                        ('title', r_title[:300]),
                        ('description', r_desc),
                        ('flow', r_flow),
                        ('configuration', r_conf),
                        ('priority', r_priority),
                    ):
                        if getattr(req, field) != value:
                            setattr(req, field, value)
                            changed.append(field)
                if changed:
                    req.save(update_fields=changed + ['updated_at'])
                    stats['requirements_updated'] += 1

        if delete_removed and seen_epic_keys:
            to_del_d = Deliverable.objects.filter(
                project=project,
                source_epic_key__isnull=False,
                is_archived=False,
            ).exclude(source_epic_key__in=seen_epic_keys)
            for d_del in to_del_d:
                archive_record(d_del)
                stats['deliverables_deleted'] += 1

        if delete_removed and seen_flow_keys:
            to_del_r = Requirement.objects.filter(
                phase=phase,
                is_archived=False,
            ).exclude(source_flow_key='').exclude(source_flow_key__in=seen_flow_keys)
            for r_del in to_del_r:
                archive_record(r_del)
                stats['requirements_deleted'] += 1

        # --- Sync data model entities ---
        entities_list = _parse_data_model_entities(doc)
        seen_entity_names: set[str] = set()

        # Prefetch all existing entities in one query → in-memory lookup
        existing_entity_map: dict[tuple[int, str], DataModelEntity] = {
            (e.deliverable_id, e.source_entity_name): e
            for e in DataModelEntity.objects.filter(
                deliverable__in=synced_deliverables,
            )
            if e.source_entity_name
        }

        to_create: list[DataModelEntity] = []
        to_update: list[DataModelEntity] = []

        for ent in entities_list:
            if not isinstance(ent, dict):
                continue
            ent_name = (ent.get('name') or '').strip()
            if not ent_name:
                continue
            seen_entity_names.add(ent_name)
            ent_desc = (ent.get('description') or '')[:5000]
            ent_kf = (ent.get('keyFields') or '')[:5000]

            for d in synced_deliverables:
                existing = existing_entity_map.get((d.id, ent_name))
                if existing:
                    updated = False
                    if existing.name != ent_name[:300]:
                        existing.name = ent_name[:300]
                        updated = True
                    if existing.description != ent_desc:
                        existing.description = ent_desc
                        updated = True
                    if existing.key_fields != ent_kf:
                        existing.key_fields = ent_kf
                        updated = True
                    if updated:
                        existing.synced_from_proposal = True
                        to_update.append(existing)
                        stats['entities_updated'] += 1
                else:
                    to_create.append(DataModelEntity(
                        deliverable=d,
                        name=ent_name[:300],
                        description=ent_desc,
                        key_fields=ent_kf,
                        source_entity_name=ent_name[:300],
                        synced_from_proposal=True,
                    ))
                    stats['entities_created'] += 1

        if to_create:
            DataModelEntity.objects.bulk_create(to_create)
        if to_update:
            DataModelEntity.objects.bulk_update(
                to_update, ['name', 'description', 'key_fields', 'synced_from_proposal'],
            )

        if delete_removed and seen_entity_names:
            to_del_e = DataModelEntity.objects.filter(
                deliverable__project=project,
                source_entity_name__isnull=False,
                is_archived=False,
            ).exclude(source_entity_name='').exclude(
                source_entity_name__in=seen_entity_names,
            )
            for e_del in to_del_e:
                archive_record(e_del)
                stats['entities_deleted'] += 1

        total = Requirement.objects.filter(
            phase__project=project, is_archived=False,
        ).count()
        if total == 0:
            project.progress = 0
        else:
            done = Requirement.objects.filter(
                phase__project=project,
                status=Requirement.STATUS_DONE,
                is_archived=False,
            ).count()
            project.progress = round((done / total) * 100)
        project.save(update_fields=['progress', 'updated_at'])

    return stats


def sync_technical_requirements_for_project(
    project, acting_user: User, delete_removed: bool = False,
) -> dict[str, Any]:
    """
    Upsert deliverables (per épica) and requirements from the linked proposal's
    technical_document section (first BusinessProposal on a project deliverable).
    """
    bp = project.linked_business_proposal()
    if not bp:
        return {'ok': False, 'error': 'no_linked_proposal', 'detail': 'El proyecto no tiene propuesta en un entregable.'}

    return _sync_technical_requirements_core(project, bp, acting_user, delete_removed=delete_removed)


def sync_technical_requirements_for_deliverable(
    deliverable, acting_user: User, delete_removed: bool = False,
) -> dict[str, Any]:
    """
    Same as project sync but anchored to the deliverable that owns the BusinessProposal.
    """
    bp = getattr(deliverable, 'business_proposal', None)
    if not bp:
        return {
            'ok': False,
            'error': 'no_business_proposal',
            'detail': 'Este entregable no tiene propuesta comercial vinculada.',
        }
    project = deliverable.project
    return _sync_technical_requirements_core(project, bp, acting_user, delete_removed=delete_removed)
