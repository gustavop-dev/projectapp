"""Filing operations shared by the panel and MCP.

Serialize a client's tree writes using its profile row, including thread filing,
so concurrent reparenting cannot introduce cycles or race a folder deletion.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from accounts.models import UserProfile
from content.models import CommunicationFolder
from content.services.communication_service import CommunicationError


def lock_client(client_id):
    UserProfile.objects.select_for_update().get(pk=client_id)


def validate_thread_folder(thread):
    if not thread.folder_id:
        return
    folder = CommunicationFolder.objects.filter(pk=thread.folder_id).first()
    if folder is None:
        raise CommunicationError({'folder': 'La carpeta ya no existe.'})
    if thread.thread_kind != 'manual':
        raise CommunicationError({'folder': 'La comunicación madre permanece en la raíz.'})
    if folder.client_id != thread.client_id or (
        folder.project_id and folder.project_id != thread.project_id
    ):
        raise CommunicationError({'folder': 'La carpeta no corresponde al cliente o proyecto del hilo.'})


@transaction.atomic
def save_folder(*, data, folder=None):
    client_id = folder.client_id if folder else data['client'].pk
    lock_client(client_id)
    if folder:
        folder = CommunicationFolder.objects.select_for_update().get(pk=folder.pk)
        for field in ('client', 'project'):
            if field in data and getattr(data[field], 'pk', None) != getattr(folder, f'{field}_id'):
                raise CommunicationError({field: 'El contexto de la carpeta no se puede cambiar.'})
    else:
        folder = CommunicationFolder()
    for field, value in data.items():
        setattr(folder, field, value)
    folder.name = folder.name.strip()
    try:
        folder.full_clean()
    except ValidationError as exc:
        raise CommunicationError(exc.message_dict) from exc
    folder.save()
    return folder


@transaction.atomic
def delete_folder(folder):
    lock_client(folder.client_id)
    try:
        folder.delete()
    except ProtectedError as exc:
        raise CommunicationError('Solo se pueden eliminar carpetas vacías; mueve antes sus hilos y subcarpetas.') from exc
