"""
Sync platform Kanban requirements from BusinessProposal technical_document JSON.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Deliverable, Requirement
from accounts.services.archive import archive_record
from content.models import ProposalSection

User = get_user_model()


def _parse_epics_from_json(content_json: dict) -> list:
    """Extract and normalize the epics list from a technical_document content_json."""
    epics = (content_json or {}).get('epics') or []
    return epics if isinstance(epics, list) else []


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
            deliverable__project=project,
            source_flow_key__isnull=False,
            is_archived=False,
        )
        if r.source_flow_key
    }

    diff: dict[str, Any] = {
        'epics': {'to_create': [], 'to_update': [], 'to_delete': []},
        'requirements': {'to_create': [], 'to_update': [], 'to_delete': []},
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

    return diff


def _sync_technical_requirements_core(
    project,
    bp,
    acting_user: User,
    delete_removed: bool = False,
) -> dict[str, Any]:
    """
    Upsert one Deliverable per epic (by source_epic_key) and Requirements per flowKey.
    Skips requirement rows without title or without flowKey.
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
        'deliverables_created': 0,
        'deliverables_updated': 0,
        'deliverables_deleted': 0,
        'requirements_created': 0,
        'requirements_updated': 0,
        'requirements_skipped': 0,
        'requirements_deleted': 0,
    }

    with transaction.atomic():
        seen_epic_keys: set[str] = set()
        seen_flow_keys: set[str] = set()

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
                flow_key = (r.get('flowKey') or '').strip()
                t = (r.get('title') or '').strip()
                if not t or not flow_key:
                    stats['requirements_skipped'] += 1
                    continue

                seen_flow_keys.add(flow_key)
                flow_text = (r.get('usageFlow') or r.get('flow') or '')[:5000]
                conf = (r.get('configuration') or '')[:5000]
                desc = (r.get('description') or '')[:5000]

                existing = Requirement.objects.filter(
                    deliverable=d, source_flow_key=flow_key,
                ).first()
                if existing:
                    existing.title = t[:300]
                    existing.description = desc
                    existing.configuration = conf
                    existing.flow = flow_text
                    existing.source_epic_key = key[:200]
                    existing.source_epic_title = title[:300]
                    existing.synced_from_proposal = True
                    existing.save()
                    stats['requirements_updated'] += 1
                else:
                    max_order = Requirement.objects.filter(
                        deliverable=d, status=Requirement.STATUS_BACKLOG,
                    ).count()
                    Requirement.objects.create(
                        deliverable=d,
                        title=t[:300],
                        description=desc,
                        configuration=conf,
                        flow=flow_text,
                        status=Requirement.STATUS_BACKLOG,
                        priority=Requirement.PRIORITY_MEDIUM,
                        order=max_order,
                        source_epic_key=key[:200],
                        source_epic_title=title[:300],
                        source_flow_key=flow_key[:200],
                        synced_from_proposal=True,
                    )
                    stats['requirements_created'] += 1

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
                deliverable__project=project,
                source_flow_key__isnull=False,
                is_archived=False,
            ).exclude(source_flow_key__in=seen_flow_keys)
            for r_del in to_del_r:
                archive_record(r_del)
                stats['requirements_deleted'] += 1

        total = Requirement.objects.filter(
            deliverable__project=project, is_archived=False,
        ).count()
        if total == 0:
            project.progress = 0
        else:
            done = Requirement.objects.filter(
                deliverable__project=project,
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
