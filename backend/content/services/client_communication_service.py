"""Adopción de la comunicación madre de un cliente.

Sólo adopción, sin signal: hay 32 perfiles de cliente y un puñado de hilos, así
que provisionar automáticamente llenaría el módulo de conversaciones vacías. Es
el mismo criterio que ya se aplicó a `client_document_folder_service`.
"""
from django.db import IntegrityError, transaction

from content.models import CommunicationThread


class ClientCommunicationThreadUnavailable(RuntimeError):
    """Raised when a client has no adopted root thread and one was required."""


def require_client_thread(profile):
    thread = CommunicationThread.objects.filter(
        managed_client=profile,
        is_archived=False,
    ).first()
    if thread is None:
        raise ClientCommunicationThreadUnavailable(
            f'El cliente «{profile}» no tiene comunicación madre adoptada.'
        )
    return thread


@transaction.atomic
def adopt_client_thread(thread, profile):
    """Marca un hilo existente como la comunicación madre de su cliente.

    No crea nada: recibe el hilo que una persona ya revisó. Un hilo con proyecto
    no sirve — ése pertenece al espacio del proyecto, no al del cliente.
    """
    if thread.managed_project_id is not None:
        raise ValueError('El hilo ya es la comunicación madre de un proyecto.')
    if thread.project_id is not None:
        raise ValueError('Una comunicación de cliente no puede estar asociada a un proyecto.')
    if thread.client_id != profile.pk:
        raise ValueError('El hilo pertenece a otro cliente.')
    if thread.is_archived:
        raise ValueError('Restaura el hilo antes de adoptarlo como madre.')

    locked = CommunicationThread.objects.select_for_update().get(pk=thread.pk)
    existing = CommunicationThread.objects.filter(managed_client=profile).first()
    if existing is not None and existing.pk != locked.pk:
        raise ValueError(
            f'El cliente ya tiene la comunicación madre {existing.pk} «{existing.title}».'
        )

    locked.managed_client = profile
    try:
        with transaction.atomic():
            locked.save(update_fields=['managed_client', 'updated_at'])
    except IntegrityError as exc:
        raise ValueError('El cliente ya tiene una comunicación madre.') from exc
    return locked
