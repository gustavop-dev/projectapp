import copy
import logging

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.http import content_disposition_header
from django.views.decorators.clickjacking import xframe_options_sameorigin
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.api_errors import error_response
from content.models import Document
from content.serializers.document import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentCreateUpdateSerializer,
    DocumentFromMarkdownSerializer,
)
from content.services import document_archive_service
from content.services.collection_account_service import (
    CollectionAccountError,
    delete_collection_account,
    is_collection_account,
)
from content.services.document_content import build_content_json, resolve_blocks
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.services.document_type_utils import get_markdown_document_type
from content.utils import safe_slug

logger = logging.getLogger(__name__)

_ARCHIVE_ORDER = {'newest': '-archived_at', 'oldest': 'archived_at'}

_SCOPES = ('active', 'archived', 'all')

_SEARCH_MAX_LENGTH = 200


def wants_archived(request):
    """True cuando el caller pide el scope archivado (`?archived=1`)."""
    raw = request.query_params.get('archived')
    return str(raw or '').strip().lower() in ('1', 'true', 'yes', 'on')


def archive_scope(request):
    """Scope pedido: 'active' (default), 'archived' o 'all'. None si es inválido.

    `?archived=1` se conserva como alias heredado del store del panel y de la
    batería de tests que llegó con el archivado; si llegan los dos, manda
    `scope`. El parámetro selecciona datos, así que un valor inválido responde
    400 — igual que `folder` y `tags`, y a diferencia de `order`, que sólo los
    presenta.
    """
    raw = str(request.query_params.get('scope') or '').strip().lower()
    if not raw:
        return 'archived' if wants_archived(request) else 'active'
    return raw if raw in _SCOPES else None


def apply_archive_scope(queryset, scope):
    """Filtra por `is_archived`; 'all' no filtra y deja ver el estado mixto."""
    if scope == 'all':
        return queryset
    return queryset.filter(is_archived=(scope == 'archived'))


def search_term(request):
    """Texto de búsqueda ya normalizado; cadena vacía cuando no se pidió.

    Un `search` en blanco no es un error sino un no-op: a diferencia de un
    `folder` malformado, no hay ninguna intención que malinterpretar.
    """
    return str(request.query_params.get('search') or '').strip()[:_SEARCH_MAX_LENGTH]


def archived_order_field(request):
    """Campo de orden para el scope archivado; `order` inválido cae a newest.

    A diferencia de `folder`/`tags`, que seleccionan datos y por eso responden
    400, `order` sólo los presenta: un valor raro no justifica romper la vista.
    """
    raw = str(request.query_params.get('order') or '').strip().lower()
    return _ARCHIVE_ORDER.get(raw, _ARCHIVE_ORDER['newest'])


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_documents(request):
    """List all documents, optionally filtered by folder, tags and/or search.

    Por defecto sólo devuelve documentos activos; `?scope=archived` devuelve
    únicamente los archivados, ordenados por fecha de archivado, y `?scope=all`
    devuelve los dos estados mezclados — cada fila trae `is_archived`, que es lo
    que permite marcarla en una lista mixta.
    """
    scope = archive_scope(request)
    if scope is None:
        return Response(
            {'scope': 'El estado solicitado no es válido. Usa active, archived o all.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    documents = (
        apply_archive_scope(Document.objects.all(), scope)
        .prefetch_related('tags')
        .select_related('folder', 'project', 'client_user__profile')
    )

    folder_param = request.query_params.get('folder')
    if folder_param == 'none':
        documents = documents.filter(folder__isnull=True)
    elif folder_param not in (None, '', 'all'):
        try:
            documents = documents.filter(folder_id=int(folder_param))
        except (TypeError, ValueError):
            return Response(
                {'folder': 'El identificador de carpeta no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    client_param = request.query_params.get('client')
    if client_param == 'none':
        documents = documents.filter(client_user__isnull=True)
    elif client_param not in (None, '', 'all'):
        try:
            client_ids = [int(c) for c in client_param.split(',') if c.strip()]
        except ValueError:
            return Response(
                {'client': 'El identificador de cliente no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if client_ids:
            # El panel habla en pk de UserProfile; el modelo persiste auth.User.
            documents = documents.filter(client_user__profile__id__in=client_ids)

    project_param = request.query_params.get('project')
    if project_param == 'none':
        documents = documents.filter(project__isnull=True)
    elif project_param not in (None, '', 'all'):
        try:
            project_ids = [int(p) for p in project_param.split(',') if p.strip()]
        except ValueError:
            return Response(
                {'project': 'El identificador de proyecto no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if project_ids:
            documents = documents.filter(project_id__in=project_ids)

    tags_param = request.query_params.get('tags')
    if tags_param:
        try:
            tag_ids = [int(t) for t in tags_param.split(',') if t.strip()]
        except ValueError:
            return Response(
                {'tags': 'La lista de etiquetas no es válida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if tag_ids:
            documents = documents.filter(tags__id__in=tag_ids).distinct()

    search = search_term(request)
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | Q(client_name__icontains=search),
        )

    if scope == 'archived':
        # `-created_at` desempata y protege el orden si alguna fila quedara sin
        # `archived_at` (datos antiguos migrados a mano). Con `scope=all` no se
        # aplica: las filas activas tienen `archived_at` en NULL y el orden
        # mentiría; ahí manda el `-created_at` del modelo.
        documents = documents.order_by(archived_order_field(request), '-created_at')

    serializer = DocumentListSerializer(documents, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document(request):
    """Create a document from direct JSON input."""
    serializer = DocumentCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    document = serializer.save()
    if not document.document_type_id:
        document.document_type = get_markdown_document_type()
        document.save(update_fields=['document_type'])

    # If markdown was provided but no JSON, parse it
    if document.content_markdown and not document.content_json:
        document.content_json = build_content_json(document)
        document.save(update_fields=['content_json'])

    detail = DocumentDetailSerializer(document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document_from_markdown(request):
    """Create a document from markdown text."""
    serializer = DocumentFromMarkdownSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    markdown_text = data['markdown']

    document = Document(
        title=data['title'],
        document_type=get_markdown_document_type(),
        folder=data.get('folder_id'),
        client_name=data.get('client_name', ''),
        client_user=data.get('client_user'),
        project=data.get('project'),
        language=data.get('language', 'es'),
        cover_type=data.get('cover_type', 'generic'),
        template_style=data.get('template_style', 'professional'),
        include_portada=data.get('include_portada', True),
        include_subportada=data.get('include_subportada', True),
        include_contraportada=data.get('include_contraportada', True),
        content_markdown=markdown_text,
    )
    document.content_json = build_content_json(document, markdown_text)
    document.save()

    tag_ids = data.get('tag_ids')
    if tag_ids:
        document.tags.set(tag_ids)

    detail = DocumentDetailSerializer(document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def upload_document_markdown(request):
    """Create a document from an uploaded .md file."""
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response(
            {'file': 'No se adjuntó ningún archivo.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Read file content
    try:
        markdown_text = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response(
            {'file': 'El archivo debe ser un texto válido en formato UTF-8.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    title = request.data.get('title', uploaded_file.name.rsplit('.', 1)[0])
    client_name = request.data.get('client_name', '')
    language = request.data.get('language', 'es')
    cover_type = request.data.get('cover_type', 'generic')
    template_style = request.data.get('template_style', 'professional')

    def _to_bool(value, default=True):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() not in ('false', '0', '')
        return default if value is None else bool(value)

    include_portada = _to_bool(request.data.get('include_portada'), default=True)
    include_subportada = _to_bool(request.data.get('include_subportada'), default=True)
    include_contraportada = _to_bool(request.data.get('include_contraportada'), default=True)

    folder_id = request.data.get('folder_id') or None
    folder = None
    if folder_id not in (None, '', 'null'):
        from content.models import DocumentFolder
        folder = DocumentFolder.objects.filter(pk=folder_id).first()

    # La guarda va en la vista y no en un serializer porque este endpoint no
    # pasa por ninguno: recibe multipart y arma el documento a mano.
    try:
        document_archive_service.ensure_active_target(folder)
    except document_archive_service.DocumentArchiveError as exc:
        return Response({'folder_id': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    document = Document(
        title=title,
        document_type=get_markdown_document_type(),
        folder=folder,
        client_name=client_name,
        language=language,
        cover_type=cover_type,
        template_style=template_style,
        include_portada=include_portada,
        include_subportada=include_subportada,
        include_contraportada=include_contraportada,
        content_markdown=markdown_text,
    )
    document.content_json = build_content_json(document, markdown_text)
    document.save()

    tag_ids_raw = request.data.get('tag_ids')
    if tag_ids_raw:
        if isinstance(tag_ids_raw, str):
            try:
                tag_id_list = [int(t) for t in tag_ids_raw.split(',') if t.strip()]
            except ValueError:
                tag_id_list = []
        elif isinstance(tag_ids_raw, (list, tuple)):
            tag_id_list = [int(t) for t in tag_ids_raw if str(t).strip()]
        else:
            tag_id_list = []
        if tag_id_list:
            document.tags.set(tag_id_list)

    detail = DocumentDetailSerializer(document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_document(request, document_id):
    """Get document detail."""
    document = get_object_or_404(Document, pk=document_id)
    serializer = DocumentDetailSerializer(document)
    return Response(serializer.data)


def _locked_collection_account_error(document):
    """400 when a cuenta de cobro already left draft.

    Draft cuentas are provisional and stay editable/deletable here; once
    issued (or paid/cancelled) the document is a fact — the only path for a
    mistake is anular y reemitir from the cuentas module, never rewriting
    the record the number was assigned to.
    """
    is_cuenta = (
        document.document_type
        and document.document_type.code == COLLECTION_ACCOUNT
    )
    if not is_cuenta:
        return None
    if document.commercial_status == Document.CommercialStatus.DRAFT:
        return None
    return error_response(
        'Esta cuenta de cobro ya fue emitida y no se puede modificar ni '
        'eliminar desde Documentos.',
        code='collection_account_locked',
        hint='Anúlala y emite una nueva desde Contabilidad → Cuentas de cobro.',
    )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document(request, document_id):
    """Update a document."""
    document = get_object_or_404(Document, pk=document_id)
    locked = _locked_collection_account_error(document)
    if locked:
        return locked
    serializer = DocumentCreateUpdateSerializer(
        document, data=request.data, partial=True,
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    # Re-parse markdown if it changed
    if 'content_markdown' in request.data and document.content_markdown:
        document.content_json = build_content_json(document)
        document.save(update_fields=['content_json'])

    detail = DocumentDetailSerializer(document)
    return Response(detail.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_document(request, document_id):
    """Delete a document.

    Los archivados siguen siendo borrables: archivar es el paso intermedio,
    eliminar sigue disponible para la limpieza final.
    """
    document = get_object_or_404(Document, pk=document_id)
    locked = _locked_collection_account_error(document)
    if locked:
        return locked
    # A draft cuenta reaching this far is still a cuenta de cobro: route it
    # through the accounting service so it leaves the same audit row a delete
    # from the Cuentas de cobro tab would. Deleting it here used to be the one
    # way to make one disappear with no trace in the historial.
    if is_collection_account(document):
        try:
            delete_collection_account(document, acting_user=request.user)
        except CollectionAccountError as exc:
            # Unreachable through the lock above today, but a 500 is the wrong
            # way to say "this cuenta is not deletable".
            return error_response(str(exc))
        return Response(status=status.HTTP_204_NO_CONTENT)
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def archive_document(request, document_id):
    """Saca un documento de la vista principal sin destruirlo."""
    document = get_object_or_404(Document, pk=document_id)
    document_archive_service.archive_document(document)
    return Response(DocumentListSerializer(document).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def unarchive_document(request, document_id):
    """Devuelve un documento archivado a la vista principal.

    Reabre además la cadena de carpetas que lo contiene, y la reporta en
    `restored_chain` para que la UI pueda decir qué carpeta volvió con él. Si su
    carpeta fue eliminada mientras tanto, reaparece en «Sin carpeta».

    Las claves extra van al lado de los campos del documento y no en un
    envelope: el store devuelve `response.data` tal cual a la página.
    """
    document = get_object_or_404(Document, pk=document_id)
    result = document_archive_service.unarchive_document(document)
    return Response({
        **DocumentListSerializer(document).data,
        'restored_chain': [
            {'id': folder.id, 'name': folder.name}
            for folder in result['restored_chain']
        ],
        'moved_to_root': result['moved_to_root'],
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def document_counts(request):
    """Contadores autoritativos del panel lateral. No acepta filtros a propósito."""
    return Response(document_archive_service.panel_counts())


@api_view(['POST'])
@permission_classes([IsAdminUser])
def duplicate_document(request, document_id):
    """Duplicate a document.

    La copia hereda la carpeta sólo si sigue activa: el duplicado nace sin
    archivar, y dejarlo dentro de una carpeta archivada lo volvería invisible
    en las dos vistas del panel.
    """
    document = get_object_or_404(Document, pk=document_id)
    if document.document_type and document.document_type.code == COLLECTION_ACCOUNT:
        return Response(
            {'detail': 'Las cuentas de cobro no se pueden duplicar desde el panel.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    doc_type = document.document_type or get_markdown_document_type()
    folder = document.folder if document.folder and not document.folder.is_archived else None
    new_document = Document.objects.create(
        title=f'{document.title} (copia)',
        document_type=doc_type,
        client_name=document.client_name,
        client_user=document.client_user,
        project=document.project,
        language=document.language,
        cover_type=document.cover_type,
        include_portada=document.include_portada,
        include_subportada=document.include_subportada,
        include_contraportada=document.include_contraportada,
        # Va con las casillas y no aparte: las cuatro deciden cómo sale el PDF,
        # y una copia que cambia de estilo sola no es una copia.
        template_style=document.template_style,
        folder=folder,
        status=Document.Status.DRAFT,
        content_markdown=document.content_markdown,
        content_json=copy.deepcopy(document.content_json),
    )

    detail = DocumentDetailSerializer(new_document)
    return Response(detail.data, status=status.HTTP_201_CREATED)


# sameorigin porque la previsualización del panel embebe `?inline=1` en un
# visor: el DENY por defecto del middleware dejaría el visor en blanco.
@xframe_options_sameorigin
@api_view(['GET'])
@permission_classes([IsAdminUser])
def download_document_pdf(request, document_id):
    """Generate the document PDF, as a download or inline for the previewer.

    El PDF se arma SIEMPRE con la configuración guardada del documento
    (`include_portada`/`include_subportada`/`include_contraportada`): esta vista
    no acepta banderas por request a propósito, para que lo previsualizado y lo
    descargado sean el mismo archivo. El panel avisa de los cambios sin guardar
    antes de llegar acá.
    """
    document = get_object_or_404(Document, pk=document_id)

    # `resolve_blocks` y no `content_json['blocks']`: un documento cuyo writer
    # se saltó el parseo sigue teniendo el markdown, y ése es el contenido real.
    if not resolve_blocks(document):
        return Response(
            {'detail': 'El documento no tiene contenido para generar el PDF.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from content.services.document_pdf_service import DocumentPdfService  # noqa: E402
    requested = request.query_params.get('template')
    valid = {'professional', 'friendly'}
    style = requested if requested in valid else document.template_style
    pdf_bytes = DocumentPdfService.generate(document, template_style=style)

    if not pdf_bytes:
        return Response(
            {'detail': 'No se pudo generar el PDF.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    filename = f'{safe_slug(document.title)}.pdf'

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    # `?inline=1` deja que el panel lo embeba en un visor en vez de bajarlo:
    # previsualizar no debería llenar la carpeta de descargas. El default sigue
    # siendo `attachment`, así que ningún caller existente cambia.
    as_attachment = not request.query_params.get('inline')
    response['Content-Disposition'] = content_disposition_header(
        as_attachment, filename,
    )
    return response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def suggest_folder_client(request):
    """Cliente mayoritario de una carpeta, para prellenar el form de crear.

    La carpeta ya está diciendo de quién es: si la mayoría estricta de sus
    documentos activos vinculados pertenece a un cliente (y son al menos dos),
    ése es el default propuesto. Una carpeta inexistente o sin señal devuelve
    sugerencia nula — la sugerencia nunca es un error, sólo un prellenado.
    """
    try:
        folder_id = int(request.query_params.get('folder'))
    except (TypeError, ValueError):
        return Response(
            {'folder': 'El identificador de carpeta no es válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    docs = Document.objects.filter(folder_id=folder_id, is_archived=False)
    ranking = list(
        docs.filter(client_user__isnull=False)
        .values('client_user')
        .annotate(total=Count('id'))
        .order_by('-total'),
    )
    linked_total = sum(row['total'] for row in ranking)

    client_id = None
    client_display_name = None
    if ranking:
        top = ranking[0]
        if top['total'] >= 2 and top['total'] * 2 > linked_total:
            user = get_user_model().objects.filter(pk=top['client_user']).first()
            profile = getattr(user, 'profile', None) if user else None
            if profile is not None:
                from accounts.services.proposal_client_service import (
                    build_client_display_name,
                )
                client_id = profile.id
                client_display_name = build_client_display_name(profile)

    return Response({
        'client': client_id,
        'client_display_name': client_display_name,
        'linked_documents': linked_total,
        'folder_documents': docs.count(),
    })
