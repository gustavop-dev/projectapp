"""Adopción de la carpeta madre de un cliente.

Espejo reducido de `project_document_folder_service`, con dos asimetrías que
impone el dominio y conviene no "corregir" por simetría:

1. **No hay provisión automática.** Un proyecto crea su raíz en el `post_save`
   porque todo proyecto tiene espacio documental. Los clientes no: hay decenas
   de perfiles y sólo un puñado con carpeta, así que un signal llenaría el
   gestor de carpetas vacías. La raíz de cliente se ADOPTA, siempre a pedido.

2. **No hay plantilla de subcarpetas.** `PROJECT_FOLDER_TEMPLATE` existe porque
   un proyecto tiene entregables, propuestas y cuentas de cobro conocidas de
   antemano. Un cliente no tiene una estructura equivalente: la suya es la que
   ya trajo su carpeta histórica.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone

from content.models import DocumentFolder


class ClientFolderAdoptionRequired(RuntimeError):
    """Raised when a client has no managed root and one was required."""


def require_client_folder(client_user):
    """Return the managed root without provisioning it silently."""
    root = DocumentFolder.objects.filter(
        managed_client=client_user,
        parent__isnull=True,
        is_archived=False,
    ).first()
    if root is None:
        raise ClientFolderAdoptionRequired(
            f'El cliente «{client_user}» no tiene una carpeta documental '
            'gestionada. Adóptala antes de archivar documentos en ella.'
        )
    return root


def _synchronize_root(root, client_user):
    """Keep the root coherent with the client it represents."""
    update_fields = []
    expected = {
        'parent_id': None,
        'client_user_id': client_user.pk,
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

    # El subárbol hereda al cliente, igual que en proyectos. Sólo se rellenan
    # los huecos: una subrama reasignada a propósito a otro cliente se respeta.
    descendant_ids = root.get_descendant_ids()
    if descendant_ids:
        DocumentFolder.objects.filter(
            pk__in=descendant_ids,
            client_user__isnull=True,
        ).update(client_user_id=client_user.pk, updated_at=timezone.now())
    return root


@transaction.atomic
def synchronize_existing_client_folder(client_user):
    """Synchronize an adopted root, but never provision a missing one."""
    root = DocumentFolder.objects.select_for_update().filter(
        managed_client=client_user,
    ).first()
    if root is None:
        return None
    return _synchronize_root(root, client_user)


@transaction.atomic
def adopt_client_folder(folder, client_user):
    """Mark an existing manual root as the client's canonical folder.

    A diferencia de `ensure_project_folder`, no crea nada: recibe la carpeta que
    el operador ya revisó. La relación única es el guardia de concurrencia.
    """
    if folder.parent_id is not None:
        raise ValueError('Sólo una carpeta raíz puede ser la carpeta madre de un cliente.')
    if folder.managed_project_id is not None:
        raise ValueError('La carpeta ya es la raíz gestionada de un proyecto.')
    if folder.project_id is not None:
        raise ValueError('Una carpeta de cliente no puede estar asociada a un proyecto.')

    locked = DocumentFolder.objects.select_for_update().get(pk=folder.pk)
    existing = DocumentFolder.objects.filter(managed_client=client_user).first()
    if existing is not None and existing.pk != locked.pk:
        raise ValueError(
            f'El cliente ya tiene la carpeta madre {existing.pk} «{existing.name}».'
        )

    locked.managed_client = client_user
    locked.client_user = client_user
    try:
        with transaction.atomic():
            locked.save(update_fields=['managed_client', 'client_user', 'updated_at'])
    except IntegrityError as exc:
        # Otro proceso ganó la carrera del OneToOne mientras tanto.
        raise ValueError('El cliente ya tiene una carpeta madre.') from exc
    return _synchronize_root(locked, client_user)
