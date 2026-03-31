"""Tests for collection account serializers validation."""

import pytest

from accounts.models import Deliverable, Project
from accounts.serializers_collection_accounts import (
    CollectionAccountCreateSerializer,
    CollectionAccountDetailSerializer,
)
from content.models import Document
from content.services.document_type_utils import get_collection_account_document_type

pytestmark = pytest.mark.django_db


def test_collection_account_create_serializer_requires_project_or_client_user():
    ser = CollectionAccountCreateSerializer(data={'title': 'Orphan'})

    assert ser.is_valid() is False
    assert 'non_field_errors' in ser.errors


def test_collection_account_create_serializer_rejects_deliverable_id_without_project_id(
    client_user,
):
    ser = CollectionAccountCreateSerializer(
        data={
            'title': 'Scoped',
            'client_user_id': client_user.id,
            'deliverable_id': 1,
        },
    )

    assert ser.is_valid() is False
    assert 'deliverable_id' in ser.errors


def test_collection_account_create_serializer_rejects_deliverable_not_belonging_to_project(
    admin_user, project, client_user,
):
    other_project = Project.objects.create(
        name='Other ser project',
        client=client_user,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )
    foreign_deliverable = Deliverable.objects.create(
        project=other_project,
        title='Foreign',
        uploaded_by=admin_user,
        category=Deliverable.CATEGORY_OTHER,
    )

    ser = CollectionAccountCreateSerializer(
        data={
            'title': 'Mismatch',
            'project_id': project.id,
            'deliverable_id': foreign_deliverable.id,
        },
    )

    assert ser.is_valid() is False
    assert 'deliverable_id' in ser.errors


def test_collection_account_detail_serializer_sets_collection_account_to_null_without_row():
    dt = get_collection_account_document_type()
    doc = Document.objects.create(title='Bare doc', document_type=dt)

    data = CollectionAccountDetailSerializer(doc).data

    assert data['collection_account'] is None
