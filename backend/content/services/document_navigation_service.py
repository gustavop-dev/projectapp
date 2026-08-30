"""Aggregated navigation facets for the document manager sidebar.

Associations are counted from their canonical direct foreign keys. Folder depth
does not change ownership, so each folder and document contributes exactly once
to its project, its client and the global total.
"""

from collections import defaultdict

from django.db.models import Count, F

from accounts.models import Project, UserProfile
from accounts.services.proposal_client_service import build_client_display_name
from content.models import Document, DocumentFolder
from content.services.project_document_folder_service import project_catalog_bucket


def _empty_counts():
    return {
        'active': {'folders': 0, 'documents': 0},
        'archived': {'folders': 0, 'documents': 0},
    }


def _add(counts, *, archived, kind, total):
    scope = 'archived' if archived else 'active'
    counts[scope][kind] += total


def _grouped_rows(model):
    return list(
        model.objects
        .annotate(client_profile_id=F('client_user__profile__id'))
        .values('project_id', 'client_profile_id', 'is_archived')
        .annotate(total=Count('id'))
    )


def _state_payload(project):
    state = project.current_state
    if state is None:
        return None
    # Kept for compatibility with older consumers. Project inclusion is owned by
    # Project.document_manager_enabled; lifecycle only selects the catalog bucket.
    return {
        'id': state.pk,
        'name': state.name,
        'system_key': state.system_key,
        'color': state.color,
        'operational_effect': state.operational_effect,
        'show_in_document_manager': state.show_in_document_manager,
    }


def build_document_navigation():
    """Return project/client facets using a constant number of database queries."""
    document_rows = _grouped_rows(Document)
    folder_rows = _grouped_rows(DocumentFolder)
    projects = list(
        Project.objects.filter(document_manager_enabled=True)
        .select_related(
            'client__profile__user',
            'current_state',
            'document_root_folder',
        )
    )
    clients = list(
        UserProfile.objects.clients()
        .select_related('user')
    )
    valid_client_ids = {profile.pk for profile in clients}

    totals = _empty_counts()
    project_unassigned = _empty_counts()
    client_unassigned = _empty_counts()
    project_counts = defaultdict(_empty_counts)
    client_counts = defaultdict(_empty_counts)

    for kind, rows in (('documents', document_rows), ('folders', folder_rows)):
        for row in rows:
            archived = row['is_archived']
            total = row['total']
            project_id = row['project_id']
            client_id = row['client_profile_id']

            _add(totals, archived=archived, kind=kind, total=total)
            if project_id:
                _add(
                    project_counts[project_id],
                    archived=archived,
                    kind=kind,
                    total=total,
                )
            else:
                _add(
                    project_unassigned,
                    archived=archived,
                    kind=kind,
                    total=total,
                )

            if client_id in valid_client_ids:
                _add(
                    client_counts[client_id],
                    archived=archived,
                    kind=kind,
                    total=total,
                )
            else:
                _add(
                    client_unassigned,
                    archived=archived,
                    kind=kind,
                    total=total,
                )

    project_entries = []
    for project in projects:
        state = _state_payload(project)
        profile = getattr(project.client, 'profile', None)
        root = getattr(project, 'document_root_folder', None)
        project_entries.append({
            'id': project.pk,
            'name': project.name,
            'client': profile.pk if profile else None,
            'client_display_name': (
                build_client_display_name(profile) if profile else project.client.email
            ),
            'managed_root_id': root.pk if root else None,
            'state': state,
            'document_manager_enabled': True,
            'catalog_bucket': project_catalog_bucket(project),
            # Compatibility for consumers predating catalog_bucket: every row
            # returned by this endpoint is visible somewhere in the catalog.
            'is_visible': True,
            'counts': project_counts[project.pk],
        })

    client_entries = [
        {
            'id': profile.pk,
            'name': build_client_display_name(profile),
            'is_inactive': profile.is_inactive_client,
            'catalog_bucket': (
                'archived' if profile.is_inactive_client else 'active'
            ),
            'counts': client_counts[profile.pk],
        }
        for profile in clients
    ]

    project_entries.sort(key=lambda entry: entry['name'].casefold())
    client_entries.sort(key=lambda entry: entry['name'].casefold())
    return {
        'totals': totals,
        'unassigned': {
            'project': project_unassigned,
            'client': client_unassigned,
        },
        'projects': project_entries,
        'clients': client_entries,
    }
