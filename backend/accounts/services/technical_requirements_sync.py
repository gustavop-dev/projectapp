"""
Sync platform Kanban requirements from BusinessProposal technical_document JSON.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Deliverable, Requirement
from content.models import ProposalSection

User = get_user_model()


def _sync_technical_requirements_core(
    project,
    bp,
    acting_user: User,
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
        'requirements_created': 0,
        'requirements_updated': 0,
        'requirements_skipped': 0,
    }

    with transaction.atomic():
        for idx, epic in enumerate(epics):
            if not isinstance(epic, dict):
                continue
            key = (epic.get('epicKey') or '').strip()
            title = (epic.get('title') or '').strip() or key or f'Épica {idx + 1}'
            description = epic.get('description') or ''
            reqs = epic.get('requirements') or []
            if not isinstance(reqs, list):
                reqs = []

            if not key:
                if not reqs:
                    continue
                key = f'_sync_epic_{idx}'

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

        total = Requirement.objects.filter(deliverable__project=project).count()
        if total == 0:
            project.progress = 0
        else:
            done = Requirement.objects.filter(
                deliverable__project=project, status=Requirement.STATUS_DONE,
            ).count()
            project.progress = round((done / total) * 100)
        project.save(update_fields=['progress', 'updated_at'])

    return stats


def sync_technical_requirements_for_project(project, acting_user: User) -> dict[str, Any]:
    """
    Upsert deliverables (per épica) and requirements from the linked proposal's
    technical_document section (first BusinessProposal on a project deliverable).
    """
    bp = project.linked_business_proposal()
    if not bp:
        return {'ok': False, 'error': 'no_linked_proposal', 'detail': 'El proyecto no tiene propuesta en un entregable.'}

    return _sync_technical_requirements_core(project, bp, acting_user)


def sync_technical_requirements_for_deliverable(deliverable, acting_user: User) -> dict[str, Any]:
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
    return _sync_technical_requirements_core(project, bp, acting_user)
