"""MCP folder operations use the same validation and locks as the panel."""
from content.mcp.protocol import ToolError
from content.models import CommunicationFolder
from content.serializers.communication_folder import CommunicationFolderSerializer
from content.services import communication_folder_service as service
from content.services.communication_service import CommunicationError


def list_folders(arguments):
    from content.mcp.communication_tools import _positive_int, _reject_unknown_fields
    _reject_unknown_fields(arguments, {'client_id', 'project_id'})
    folders = CommunicationFolder.objects.all()
    for field in ('client', 'project'):
        value = _positive_int(arguments.get(f'{field}_id'), field=f'{field}_id')
        if value:
            folders = folders.filter(**{f'{field}_id': value})
    return {'results': CommunicationFolderSerializer(folders, many=True).data}


def _write(arguments, *, update=False):
    from content.mcp.communication_tools import _positive_int, _reject_unknown_fields, _serializer_error
    allowed = {'name', 'parent', 'client', 'project'}
    _reject_unknown_fields(arguments, allowed | ({'folder_id'} if update else set()))
    folder = None
    if update:
        folder = CommunicationFolder.objects.filter(
            pk=_positive_int(arguments.get('folder_id'), field='folder_id'),
        ).first()
        if folder is None:
            raise ToolError('No existe la carpeta.')
    serializer = CommunicationFolderSerializer(
        folder, data={key: value for key, value in arguments.items() if key in allowed},
        partial=update,
    )
    if not serializer.is_valid():
        raise ToolError(_serializer_error(serializer.errors))
    try:
        folder = service.save_folder(folder=folder, data=serializer.validated_data)
    except CommunicationError as exc:
        raise ToolError(str(exc)) from exc
    return CommunicationFolderSerializer(folder).data


def create_folder(arguments):
    return _write(arguments)


def update_folder(arguments):
    return _write(arguments, update=True)


def delete_folder(arguments):
    from content.mcp.communication_tools import _positive_int, _reject_unknown_fields
    _reject_unknown_fields(arguments, {'folder_id'})
    folder_id = _positive_int(arguments.get('folder_id'), field='folder_id')
    folder = CommunicationFolder.objects.filter(pk=folder_id).first()
    if folder is None:
        raise ToolError('No existe la carpeta.')
    try:
        service.delete_folder(folder)
    except CommunicationError as exc:
        raise ToolError(str(exc)) from exc
    return {'deleted': True, 'id': folder_id}


_ID = {'type': 'integer', 'minimum': 1}
_NULL_ID = {'type': ['integer', 'null'], 'minimum': 1}
_FIELDS = {'name': {'type': 'string'}, 'parent': _NULL_ID, 'client': _ID, 'project': _NULL_ID}
COMMUNICATION_FOLDER_TOOLS = [
    {
        'name': name, 'description': description,
        'input_schema': {
            'type': 'object', 'properties': properties,
            'required': required, 'additionalProperties': False,
        },
        'handler': handler,
    }
    for name, description, properties, required, handler in (
        ('list_folders', 'Lista carpetas de comunicaciones por perfil de cliente/proyecto.',
         {'client_id': _ID, 'project_id': _ID}, [], list_folders),
        ('create_folder', 'Crea una carpeta o subcarpeta; client es el ID del perfil de cliente.',
         _FIELDS, ['name', 'client'], create_folder),
        ('update_folder', 'Renombra o mueve una carpeta dentro del mismo contexto; client/project son inmutables.',
         {**_FIELDS, 'folder_id': _ID}, ['folder_id'], update_folder),
        ('delete_folder', 'Elimina exclusivamente una carpeta vacía, sin hilos activos ni archivados.',
         {'folder_id': _ID}, ['folder_id'], delete_folder),
    )
]
