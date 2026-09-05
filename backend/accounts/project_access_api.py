"""Shared request handlers for the panel and platform access-detail APIs."""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from accounts.models import Project, ProjectAccessNote, ProjectAdminAccess
from accounts.serializers_project_access import (
    ProjectAccessNoteCreateSerializer,
    ProjectAccessNoteUpdateSerializer,
    ProjectAccessUpdateSerializer,
    ProjectLegacyAccessClassifySerializer,
)
from accounts.services.project_access import (
    ProjectAccessConflict,
    ProjectAccessSecretMissing,
    classify_legacy_access,
    create_note,
    delete_environment_password,
    reveal_environment_password,
    reveal_note_content,
    serialize_project_access,
    update_access_field,
    update_note,
)
from content.api_errors import error_response


def _get_project(project_id):
    return get_object_or_404(
        Project.objects.select_related('client').prefetch_related(
            Prefetch(
                'admin_accesses',
                queryset=ProjectAdminAccess.objects.select_related('updated_by'),
            ),
            Prefetch(
                'access_notes',
                queryset=ProjectAccessNote.objects.select_related('updated_by'),
            ),
        ),
        pk=project_id,
    )


def _detail_response(project_id, *, response_status=status.HTTP_200_OK):
    response = Response(
        serialize_project_access(_get_project(project_id)),
        status=response_status,
    )
    return _prevent_sensitive_caching(response)


def _prevent_sensitive_caching(response):
    response['Cache-Control'] = 'no-store, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


def _secret_response(secret):
    return _prevent_sensitive_caching(Response({'secret': secret}))


def _valid_environment(environment):
    return environment in ProjectAdminAccess.Environment.values


def project_access_detail_handler(request, project_id):
    project = _get_project(project_id)
    if request.method == 'GET':
        return _prevent_sensitive_caching(Response(serialize_project_access(project)))

    serializer = ProjectAccessUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    update_access_field(project, serializer.validated_data, request.user)
    return _detail_response(project.pk)


def project_access_password_reveal_handler(request, project_id, environment):
    if not _valid_environment(environment):
        return error_response(
            'El ambiente indicado no existe.',
            code='invalid_project_environment',
        )
    project = _get_project(project_id)
    try:
        secret = reveal_environment_password(project, environment)
    except ProjectAccessSecretMissing as exc:
        return error_response(
            str(exc),
            code='project_access_secret_missing',
            status=status.HTTP_404_NOT_FOUND,
        )
    return _secret_response(secret)


def project_access_password_delete_handler(request, project_id, environment):
    if not _valid_environment(environment):
        return error_response(
            'El ambiente indicado no existe.',
            code='invalid_project_environment',
        )
    project = _get_project(project_id)
    delete_environment_password(project, environment, request.user)
    return _detail_response(project.pk)


def project_access_notes_handler(request, project_id):
    project = _get_project(project_id)
    serializer = ProjectAccessNoteCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    create_note(project, serializer.validated_data, request.user)
    return _detail_response(project.pk, response_status=status.HTTP_201_CREATED)


def project_access_note_detail_handler(request, project_id, note_id):
    project = _get_project(project_id)
    note = get_object_or_404(ProjectAccessNote, pk=note_id, project=project)
    if request.method == 'DELETE':
        note.delete()
        return _detail_response(project.pk)

    serializer = ProjectAccessNoteUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    update_note(note, serializer.validated_data, request.user)
    return _detail_response(project.pk)


def project_access_note_reveal_handler(request, project_id, note_id):
    project = _get_project(project_id)
    note = get_object_or_404(ProjectAccessNote, pk=note_id, project=project)
    try:
        secret = reveal_note_content(note)
    except ProjectAccessSecretMissing as exc:
        return error_response(
            str(exc),
            code='project_access_secret_missing',
            status=status.HTTP_404_NOT_FOUND,
        )
    return _secret_response(secret)


def project_access_legacy_classify_handler(request, project_id):
    project = _get_project(project_id)
    serializer = ProjectLegacyAccessClassifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        classify_legacy_access(
            project,
            serializer.validated_data['environment'],
            request.user,
        )
    except ProjectAccessConflict as exc:
        return error_response(
            str(exc),
            code='project_access_classification_conflict',
            hint='Vacía los campos del ambiente destino o elige el otro ambiente.',
            status=status.HTTP_409_CONFLICT,
        )
    except ProjectAccessSecretMissing as exc:
        return error_response(
            str(exc),
            code='project_access_legacy_missing',
            status=status.HTTP_409_CONFLICT,
        )
    return _detail_response(project.pk)
