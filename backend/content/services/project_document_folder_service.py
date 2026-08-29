"""Automatic document-folder lifecycle for platform projects.

`DocumentFolder.project` is the PA-64 association copied to descendants and
documents. `managed_project` has a narrower job: it marks the single root that
the system owns for a Project. Keeping those concepts separate lets operators
continue creating ordinary project-associated folders without turning them
into lifecycle-managed roots.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone

from content.models import DocumentFolder


PROJECT_FOLDER_TEMPLATE = (
    'Cuentas de cobro',
    'Propuestas',
    'Entregables',
    'QA',
)


@transaction.atomic
def ensure_project_folder(project):
    """Return the project's single managed root, creating it when absent.

    The unique database relation is the concurrency guard. Template folders
    are created only with a genuinely new root, so adopting an existing tree
    during the reviewed migration never injects duplicate structure.
    """
    defaults = {
        'name': project.name,
        'parent': None,
        'project': project,
        'client_user': project.client,
    }
    try:
        # The nested savepoint keeps the outer transaction usable when the
        # unique constraint reports a concurrent winner.
        with transaction.atomic():
            root, created = DocumentFolder.objects.get_or_create(
                managed_project=project,
                defaults=defaults,
            )
    except IntegrityError:
        # A concurrent creator won the OneToOne race. Its transaction owns the
        # template creation; this caller only needs the canonical root.
        root = DocumentFolder.objects.select_for_update().get(
            managed_project=project,
        )
        created = False

    update_fields = []
    expected = {
        'name': project.name,
        'parent_id': None,
        'project_id': project.pk,
        'client_user_id': project.client_id,
        'is_archived': False,
        'archived_at': None,
        'archived_via_folder_id': None,
    }
    for field, value in expected.items():
        if getattr(root, field) != value:
            setattr(root, field, value)
            update_fields.append(field.removesuffix('_id'))
    if update_fields:
        root.save(update_fields=[*update_fields, 'updated_at'])

    if created:
        for order, name in enumerate(PROJECT_FOLDER_TEMPLATE):
            DocumentFolder.objects.create(
                name=name,
                parent=root,
                order=order,
                project=project,
                client_user=project.client,
            )

    # A Project client move keeps only folders that still point at that same
    # project coherent. A deliberately reassigned sub-branch is left alone.
    descendant_ids = root.get_descendant_ids()
    if descendant_ids:
        DocumentFolder.objects.filter(
            pk__in=descendant_ids,
            project_id=project.pk,
        ).exclude(client_user_id=project.client_id).update(
            client_user_id=project.client_id,
            updated_at=timezone.now(),
        )
    return root
