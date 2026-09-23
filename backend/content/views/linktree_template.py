"""Session/CSRF panel API and narrowly scoped public publication resources."""
import secrets

from django.core import signing
from django.db import transaction
from django.db.models import F
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from content.models import Linktree, LinktreeTemplateClick, LinktreeTemplateVersion
from content.serializers.linktree import normalize_handle
from content.services.linktree_templates import service
from content.services.linktree_templates.package import asset_batch
from content.services.linktree_templates.render import content_security_policy, preview_document, public_document
from content.services.linktree_templates.syntax import TemplateError
from content.storage import get_private_storage


class TemplateUploadThrottle(UserRateThrottle):
    scope = 'linktree-template-upload'
    rate = '20/hour'


class TemplateClickThrottle(AnonRateThrottle):
    scope = 'linktree-template-click'
    rate = '60/minute'


class TemplateSelection(serializers.Serializer):
    template_id = serializers.UUIDField(required=False)
    version_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if len(attrs) != 1:
            raise serializers.ValidationError('Selecciona una plantilla o una versión.')
        return attrs


def tree_for_panel(linktree_id):
    return get_object_or_404(Linktree.objects.select_related('project').prefetch_related('buttons'), pk=linktree_id)


def version_for_panel(tree, version_id):
    return get_object_or_404(tree.template_versions.select_related('template'), pk=version_id)


def validation_error(error):
    return Response({'issues': [error.issue]}, status=400)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def template_library(request, linktree_id):
    tree = tree_for_panel(linktree_id)
    if request.method == 'GET':
        service.expire_pending(tree)
        offset = serializers.IntegerField(min_value=0).run_validation(request.query_params.get('offset', 0))
        versions = list(tree.template_versions.select_related('template').defer('document', 'profile', 'template__html', 'template__css', 'template__assets')[offset:offset + 21])
        # Sources and binary metadata never travel in the editor listing.
        library = service.available_templates(tree).values('id', 'name', 'is_shared', 'owner_id')[:100]
        return Response({'templates': [{**t, 'can_share': t['owner_id'] == tree.pk and bool(service.client_id(tree))} for t in library],
                         'versions': [service.version_summary(v, tree) for v in versions[:20]],
                         'next_offset': offset + 20 if len(versions) > 20 else None,
                         'active_version_id': tree.active_template_version_id,
                         'can_share': bool(service.client_id(tree))})
    for throttle in [TemplateUploadThrottle()]:
        if not throttle.allow_request(request, template_library):
            return Response({'detail': 'Se alcanzó el límite de cargas. Inténtalo más tarde.'}, status=429)
    try:
        service.check_pending(tree)
        with asset_batch(), transaction.atomic():
            previous = None
            if request.FILES:
                files = [(key if key not in {'files', 'package'} else item.name, item)
                         for key, items in request.FILES.lists() for item in items]
                template = service.upload_package(tree, files)
            else:
                selection = TemplateSelection(data=request.data)
                selection.is_valid(raise_exception=True)
                if 'version_id' in selection.validated_data:
                    previous = version_for_panel(tree, selection.validated_data['version_id'])
                    template = previous.template
                else:
                    template = get_object_or_404(service.available_templates(tree), pk=selection.validated_data['template_id'])
            version = service.create_version(tree, template, previous=previous)
        version.refresh_from_db()
        return Response(service.version_summary(version, tree), status=201)
    except TemplateError as exc:
        return validation_error(exc)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def publish_template(request, linktree_id, version_id):
    tree = tree_for_panel(linktree_id)
    version = version_for_panel(tree, version_id)
    try:
        service.publish_version(tree, version)
    except TemplateError as exc:
        return validation_error(exc)
    tree.refresh_from_db()
    return Response(service.version_summary(version, tree))


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_template(request, linktree_id):
    tree = tree_for_panel(linktree_id)
    tree.active_template_version = None
    tree.save(update_fields=['active_template_version', 'updated_at'])
    return Response({'active_version_id': None})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def share_template(request, linktree_id, template_id):
    tree = tree_for_panel(linktree_id)
    template = get_object_or_404(tree.owned_templates, pk=template_id)
    value = serializers.BooleanField().run_validation(request.data.get('is_shared'))
    if value and not service.client_id(tree):
        return Response({'detail': 'Vincula el Linktree a un proyecto antes de compartir.'}, status=400)
    template.is_shared = value
    template.client_id = service.client_id(tree)
    template.save(update_fields=['is_shared', 'client'])
    return Response({'id': template.pk, 'is_shared': template.is_shared})


@api_view(['POST', 'DELETE'])
@permission_classes([IsAdminUser])
@throttle_classes([TemplateUploadThrottle])
def template_asset_override(request, linktree_id, version_id, key):
    tree = tree_for_panel(linktree_id)
    previous = version_for_panel(tree, version_id)
    image = request.FILES.get('image')
    if request.method == 'POST' and not image:
        return Response({'detail': 'Selecciona una imagen.'}, status=400)
    try:
        with asset_batch():
            version = service.create_version(tree, previous.template, previous=previous,
                                             replacement=(key, image) if image else None,
                                             reset_key=key if request.method == 'DELETE' else None)
        version.refresh_from_db()
        return Response(service.version_summary(version, tree), status=201)
    except TemplateError as exc:
        return validation_error(exc)


def html_response(document, *, preview=False, nonce=None):
    response = HttpResponse(document, content_type='text/html; charset=utf-8')
    response['Content-Security-Policy'] = content_security_policy(nonce, preview)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Referrer-Policy'] = 'no-referrer'
    response['Cache-Control'] = 'no-store'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def template_preview(request, linktree_id, version_id):
    version = version_for_panel(tree_for_panel(linktree_id), version_id)
    return html_response(preview_document(version), preview=True)


def private_image(path, mime):
    try:
        response = FileResponse(get_private_storage().open(path, 'rb'), content_type=mime)
    except (FileNotFoundError, OSError):
        raise Http404
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def template_screenshot(request, linktree_id, version_id, width):
    version = version_for_panel(tree_for_panel(linktree_id), version_id)
    path = version.screenshots.get(str(width))
    if not path:
        raise Http404
    return private_image(path, 'image/png')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def template_asset_preview(request, linktree_id, version_id, key):
    version = version_for_panel(tree_for_panel(linktree_id), version_id)
    asset = version.assets.get(key)
    if not asset or key not in version.template.manifest['editable_assets']:
        raise Http404
    return private_image(asset['paths']['1'], asset['mime'])


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def public_template_asset(request, version_id, key, density):
    version = get_object_or_404(LinktreeTemplateVersion.objects.select_related('linktree').only('assets', 'published_at', 'linktree__is_active'), pk=version_id)
    permitted = version.published_at and version.linktree.is_active
    if not permitted:
        try:
            permitted = signing.loads(request.query_params.get('preview', ''), salt='linktree-template-preview', max_age=3600) == str(version.pk)
        except signing.BadSignature:
            permitted = False
    asset = version.assets.get(key)
    if not permitted or not asset or str(density) not in asset['paths']:
        raise Http404
    response = private_image(asset['paths'][str(density)], asset['mime'])
    return response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def public_template(request, handle):
    tree = get_object_or_404(Linktree.objects.select_related('active_template_version'), handle=normalize_handle(handle), is_active=True)
    version = tree.active_template_version
    if not version or version.status != 'valid' or not version.published_at:
        raise Http404
    nonce = secrets.token_urlsafe(24)
    return html_response(public_document(version, nonce), nonce=nonce)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([TemplateClickThrottle])
def template_click(request, version_id):
    version = get_object_or_404(LinktreeTemplateVersion, pk=version_id, published_at__isnull=False, linktree__is_active=True)
    key = request.data.get('key')
    if not isinstance(key, str) or key not in {b['key'] for b in version.profile['buttons']}:
        return Response({'detail': 'Enlace no válido.'}, status=400)
    row, _ = LinktreeTemplateClick.objects.get_or_create(version=version, link_key=key, day=timezone.localdate())
    LinktreeTemplateClick.objects.filter(pk=row.pk).update(count=F('count') + 1)
    return Response(status=204)


def localized_linktree(request, locale, handle):
    """Preserve the shareable locale URL and apply HTTP CSP before Nuxt loads."""
    if Linktree.objects.filter(handle=normalize_handle(handle), is_active=True, active_template_version__isnull=False).exists():
        return public_template(request, handle)
    from projectapp.views import serve_nuxt
    return serve_nuxt(request, path=f'{locale}/lk/{handle}')


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def template_manifest(request, handle):
    tree = get_object_or_404(Linktree.objects.select_related('active_template_version'), handle=normalize_handle(handle), is_active=True, active_template_version__isnull=False)
    version = tree.active_template_version
    if not version.profile.get('pwa_enabled'):
        raise Http404
    response = JsonResponse({'id': tree.public_path, 'name': version.profile['name'],
                             'short_name': version.profile['name'][:30], 'start_url': tree.public_path,
                             'scope': '/', 'display': 'standalone',
                             'icons': [{'src': f'/img/icons/icon-logo-{size}x{size}.png', 'sizes': f'{size}x{size}', 'type': 'image/png'} for size in (192, 512)]}, content_type='application/manifest+json')
    response['Cache-Control'] = 'no-cache'
    return response
