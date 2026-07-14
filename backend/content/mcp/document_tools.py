"""
Tool registry for the Documents MCP connector.

Lets claude.ai browse the panel's document manager (/panel/documents):
list folders, list/read markdown documents, and create/edit/delete them.
Documents are authored in Markdown; the panel turns them into branded PDFs
downstream, so producing correct Markdown is enough here.

Guardrails baked in:
- Only MARKDOWN-type documents are visible or mutable. Commercial
  collection accounts (cuentas de cobro) live in the same table and are
  deliberately out of reach.
- Published documents cannot be deleted (unpublish first or use the panel).
- Folders can be listed, created and renamed, but not deleted, so the MCP
  cannot dismantle the existing structure.

Each entry: {'name', 'description', 'input_schema', 'handler'}. Handlers
receive the raw `arguments` dict, return a JSON-serializable dict, and raise
ToolError for business errors. They reuse the exact same parser and
document_type helpers as the panel so the PDF pipeline stays identical.
"""
from content.mcp.protocol import ToolError
from content.models import Document, DocumentFolder
from content.services.document_type_codes import MARKDOWN
from content.services.document_type_utils import get_markdown_document_type
from content.services.markdown_parser import markdown_to_blocks

LANGUAGE_CHOICES = {c[0] for c in Document.Language.choices}
STATUS_CHOICES = {c[0] for c in Document.Status.choices}
COVER_TYPE_CHOICES = {c[0] for c in Document.CoverType.choices}


# ── Querysets & lookups ──────────────────────────────────────────────────────

def _markdown_qs():
    """Only markdown documents — never commercial collection accounts."""
    return Document.objects.filter(document_type__code=MARKDOWN)


def _get_markdown_doc_or_error(document_id):
    try:
        return _markdown_qs().get(pk=int(document_id))
    except (Document.DoesNotExist, TypeError, ValueError):
        raise ToolError(
            f'No existe un documento markdown con id={document_id}. '
            'Usa list_documents para ver los disponibles.'
        )


def _resolve_folder(folder_id):
    """Turn a folder_id argument into a DocumentFolder (or None for root)."""
    if folder_id in (None, '', 'none', 'null'):
        return None
    try:
        return DocumentFolder.objects.get(pk=int(folder_id))
    except (DocumentFolder.DoesNotExist, TypeError, ValueError):
        raise ToolError(
            f'No existe una carpeta con id={folder_id}. '
            'Usa list_folders para ver las disponibles.'
        )


# ── Payload shaping ──────────────────────────────────────────────────────────

def _folder_path(folder):
    names = [a.name for a in folder.get_ancestors()] + [folder.name]
    return ' / '.join(names)


def _folder_payload(folder):
    return {
        'id': folder.id,
        'name': folder.name,
        'path': _folder_path(folder),
        'parent_id': folder.parent_id,
        # Count only markdown docs, to match what list_documents exposes.
        'document_count': folder.documents.filter(document_type__code=MARKDOWN).count(),
    }


def _doc_summary(doc):
    return {
        'id': doc.id,
        'title': doc.title,
        'slug': doc.slug,
        'status': doc.status,
        'language': doc.language,
        'folder_id': doc.folder_id,
        'folder_name': doc.folder.name if doc.folder else None,
        'updated_at': doc.updated_at.isoformat() if doc.updated_at else None,
    }


def _doc_detail(doc):
    return {**_doc_summary(doc), 'content_markdown': doc.content_markdown}


def _build_content_json(doc, markdown_text):
    """Mirror the panel views: meta header + parsed blocks for the PDF stage."""
    return {
        'meta': {
            'title': doc.title,
            'client_name': doc.client_name,
            'cover_type': doc.cover_type,
            'include_portada': doc.include_portada,
            'include_subportada': doc.include_subportada,
            'include_contraportada': doc.include_contraportada,
        },
        'blocks': markdown_to_blocks(markdown_text),
    }


# ── Handlers ─────────────────────────────────────────────────────────────────

def list_folders(arguments):
    folders = DocumentFolder.objects.all().select_related('parent')
    return {'folders': [_folder_payload(f) for f in folders]}


def create_folder(arguments):
    name = (arguments.get('name') or '').strip()
    if not name:
        raise ToolError('El nombre de la carpeta es obligatorio.')
    parent = _resolve_folder(arguments.get('parent_id'))
    folder = DocumentFolder.objects.create(name=name, parent=parent)
    return _folder_payload(folder)


def rename_folder(arguments):
    folder_id = arguments.get('folder_id')
    if folder_id in (None, '', 'none', 'null'):
        raise ToolError('folder_id es obligatorio para renombrar una carpeta.')
    folder = _resolve_folder(folder_id)
    name = (arguments.get('name') or '').strip()
    if not name:
        raise ToolError('El nuevo nombre de la carpeta es obligatorio.')
    # The slug is set once on creation and left untouched, so links and PDF
    # references stay stable when only the display name changes.
    folder.name = name
    folder.save(update_fields=['name', 'updated_at'])
    return _folder_payload(folder)


def list_documents(arguments):
    try:
        page = max(1, int(arguments.get('page', 1) or 1))
        page_size = max(1, min(int(arguments.get('page_size', 20) or 20), 50))
    except (TypeError, ValueError):
        raise ToolError('page y page_size deben ser enteros.')

    qs = _markdown_qs().select_related('folder')
    folder_arg = arguments.get('folder_id')
    if folder_arg == 'none':
        qs = qs.filter(folder__isnull=True)
    elif folder_arg not in (None, '', 'all'):
        folder = _resolve_folder(folder_arg)
        qs = qs.filter(folder=folder)

    total = qs.count()
    start = (page - 1) * page_size
    page_docs = list(qs[start:start + page_size])
    return {
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': [_doc_summary(d) for d in page_docs],
    }


def read_document(arguments):
    doc = _get_markdown_doc_or_error(arguments.get('document_id'))
    return _doc_detail(doc)


def create_document(arguments):
    title = (arguments.get('title') or '').strip()
    markdown_text = arguments.get('markdown')
    if not title:
        raise ToolError('title es obligatorio.')
    if not isinstance(markdown_text, str) or not markdown_text.strip():
        raise ToolError('markdown es obligatorio y debe ser texto.')

    language = arguments.get('language', 'es')
    if language not in LANGUAGE_CHOICES:
        raise ToolError(f'language inválido: usa uno de {sorted(LANGUAGE_CHOICES)}.')

    folder = _resolve_folder(arguments.get('folder_id'))
    client_name = arguments.get('client_name', '') or ''

    doc = Document(
        title=title,
        document_type=get_markdown_document_type(),
        folder=folder,
        client_name=client_name,
        language=language,
        content_markdown=markdown_text,
    )
    doc.content_json = _build_content_json(doc, markdown_text)
    doc.save()
    return _doc_detail(doc)


def update_document(arguments):
    doc = _get_markdown_doc_or_error(arguments.get('document_id'))

    update_fields = set()
    if 'title' in arguments:
        title = (arguments.get('title') or '').strip()
        if not title:
            raise ToolError('title no puede quedar vacío.')
        doc.title = title
        update_fields.add('title')

    if 'client_name' in arguments:
        doc.client_name = arguments.get('client_name', '') or ''
        update_fields.add('client_name')

    if 'language' in arguments:
        language = arguments.get('language')
        if language not in LANGUAGE_CHOICES:
            raise ToolError(f'language inválido: usa uno de {sorted(LANGUAGE_CHOICES)}.')
        doc.language = language
        update_fields.add('language')

    if 'status' in arguments:
        new_status = arguments.get('status')
        if new_status not in STATUS_CHOICES:
            raise ToolError(f'status inválido: usa uno de {sorted(STATUS_CHOICES)}.')
        doc.status = new_status
        update_fields.add('status')

    if 'folder_id' in arguments:
        doc.folder = _resolve_folder(arguments.get('folder_id'))
        update_fields.add('folder')

    markdown_changed = 'markdown' in arguments
    if markdown_changed:
        markdown_text = arguments.get('markdown')
        if not isinstance(markdown_text, str) or not markdown_text.strip():
            raise ToolError('markdown debe ser texto no vacío.')
        doc.content_markdown = markdown_text
        update_fields.add('content_markdown')

    if not update_fields:
        raise ToolError(
            'No se indicó ningún campo para actualizar. Envía al menos uno de: '
            'title, markdown, folder_id, status, client_name, language.'
        )

    # content_json must always reflect the current title/meta + markdown, so
    # rebuild it whenever the markdown or any meta field changed.
    doc.content_json = _build_content_json(doc, doc.content_markdown)
    update_fields.add('content_json')
    doc.save(update_fields=list(update_fields) + ['updated_at'])
    return _doc_detail(doc)


def append_document(arguments):
    """Append a markdown chunk to an existing document.

    A single MCP call cannot carry very large documents, so big uploads are
    done as create_document + N append_document calls. The chunk is joined
    with a separator (default blank line) and content_json is rebuilt from
    the full markdown.
    """
    doc = _get_markdown_doc_or_error(arguments.get('document_id'))

    markdown_text = arguments.get('markdown')
    if not isinstance(markdown_text, str) or not markdown_text.strip():
        raise ToolError('markdown es obligatorio y debe ser texto no vacío.')

    separator = arguments.get('separator')
    if separator is None:
        separator = '\n\n'
    if not isinstance(separator, str):
        raise ToolError('separator debe ser texto (por ejemplo "\\n\\n" o "\\n").')

    doc.content_markdown = (
        (doc.content_markdown or '').rstrip('\n') + separator + markdown_text
    )
    doc.content_json = _build_content_json(doc, doc.content_markdown)
    doc.save(update_fields=['content_markdown', 'content_json', 'updated_at'])
    return _doc_detail(doc)


def delete_document(arguments):
    doc = _get_markdown_doc_or_error(arguments.get('document_id'))
    if doc.status == Document.Status.PUBLISHED:
        raise ToolError(
            'Este documento está publicado. Cámbialo a borrador con '
            'update_document (status="draft") antes de eliminarlo, o bórralo '
            'desde el panel.'
        )
    doc_id = doc.id
    doc.delete()
    return {'deleted': True, 'id': doc_id}


# ── Registry ─────────────────────────────────────────────────────────────────

_DOCUMENT_ID_PROP = {
    'document_id': {'type': 'integer', 'description': 'ID del documento markdown.'},
}

DOCUMENT_TOOLS = [
    {
        'name': 'list_folders',
        'description': (
            'Lista todas las carpetas del gestor de documentos con su ruta '
            'jerárquica y cuántos documentos contiene cada una. Úsala para '
            'saber dónde colocar o buscar documentos.'
        ),
        'input_schema': {'type': 'object', 'properties': {}},
        'handler': list_folders,
    },
    {
        'name': 'create_folder',
        'description': (
            'Crea una carpeta nueva para organizar documentos. Opcionalmente '
            'anídala bajo otra con parent_id (de list_folders).'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Nombre de la carpeta.'},
                'parent_id': {
                    'type': 'integer',
                    'description': 'ID de la carpeta padre (omitir para raíz).',
                },
            },
            'required': ['name'],
        },
        'handler': create_folder,
    },
    {
        'name': 'rename_folder',
        'description': (
            'Cambia el nombre de una carpeta existente. Envía folder_id (de '
            'list_folders) y el nuevo name. No mueve ni borra la carpeta.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'folder_id': {'type': 'integer', 'description': 'ID de la carpeta a renombrar.'},
                'name': {'type': 'string', 'description': 'Nuevo nombre.'},
            },
            'required': ['folder_id', 'name'],
        },
        'handler': rename_folder,
    },
    {
        'name': 'list_documents',
        'description': (
            'Lista documentos markdown con paginación. Filtra por carpeta con '
            'folder_id (un id, "none" para los que están en la raíz, o "all"). '
            'Devuelve resúmenes sin el contenido; usa read_document para el markdown.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'folder_id': {
                    'type': ['integer', 'string'],
                    'description': 'ID de carpeta, "none" (raíz) o "all" (todas).',
                },
                'page': {'type': 'integer', 'default': 1},
                'page_size': {'type': 'integer', 'default': 20, 'maximum': 50},
            },
        },
        'handler': list_documents,
    },
    {
        'name': 'read_document',
        'description': 'Devuelve un documento markdown completo, incluido su content_markdown.',
        'input_schema': {
            'type': 'object',
            'properties': _DOCUMENT_ID_PROP,
            'required': ['document_id'],
        },
        'handler': read_document,
    },
    {
        'name': 'create_document',
        'description': (
            'Crea un documento nuevo a partir de markdown. El sistema lo '
            'convierte en PDF con marca luego; basta con enviar buen markdown. '
            'Opcional: folder_id (de list_folders), language (es/en), client_name.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'markdown': {'type': 'string', 'description': 'Contenido en Markdown.'},
                'folder_id': {'type': 'integer', 'description': 'Carpeta destino (opcional).'},
                'language': {'type': 'string', 'enum': ['es', 'en'], 'default': 'es'},
                'client_name': {'type': 'string'},
            },
            'required': ['title', 'markdown'],
        },
        'handler': create_document,
    },
    {
        'name': 'update_document',
        'description': (
            'Actualiza un documento markdown existente (parcial). Envía '
            'document_id y al menos uno de: title, markdown, folder_id, '
            'status (draft/published/archived), client_name, language. Al '
            'cambiar el markdown se reprocesa el contenido para el PDF.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                **_DOCUMENT_ID_PROP,
                'title': {'type': 'string'},
                'markdown': {'type': 'string'},
                'folder_id': {
                    'type': ['integer', 'null'],
                    'description': 'Carpeta destino (null para mover a la raíz).',
                },
                'status': {'type': 'string', 'enum': ['draft', 'published', 'archived']},
                'client_name': {'type': 'string'},
                'language': {'type': 'string', 'enum': ['es', 'en']},
            },
            'required': ['document_id'],
        },
        'handler': update_document,
    },
    {
        'name': 'append_document',
        'description': (
            'Añade un fragmento de markdown AL FINAL de un documento '
            'existente, sin reenviar el contenido previo. Úsala para subir '
            'documentos largos por partes: create_document con el primer '
            'tramo y append_document con los siguientes. El contenido se '
            'reprocesa completo para el PDF en cada llamada.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                **_DOCUMENT_ID_PROP,
                'markdown': {
                    'type': 'string',
                    'description': 'Fragmento de Markdown a añadir al final.',
                },
                'separator': {
                    'type': 'string',
                    'description': (
                        'Texto entre el contenido existente y el fragmento '
                        '(default: línea en blanco "\\n\\n").'
                    ),
                },
            },
            'required': ['document_id', 'markdown'],
        },
        'handler': append_document,
    },
    {
        'name': 'delete_document',
        'description': (
            'Elimina un documento markdown NO publicado. Los publicados no se '
            'pueden borrar por MCP: pásalos a borrador primero o usa el panel.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': _DOCUMENT_ID_PROP,
            'required': ['document_id'],
        },
        'handler': delete_document,
    },
]
