"""View-level contracts for compact, bounded entity-history listings."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from content.models import EntityHistory, EntityRevision


pytestmark = pytest.mark.django_db


def test_history_listing_paginates_summaries_with_fixed_query_budget(django_assert_num_queries):
    """Fails if a long history loads encrypted snapshots or adds a query per revision."""
    user = get_user_model().objects.create_user(username='staff', is_staff=True)
    client = APIClient()
    client.force_authenticate(user)
    history = EntityHistory.objects.create(
        entity_type='document', object_id=9001, object_label='Documento eliminado',
    )
    EntityRevision.objects.bulk_create([
        EntityRevision(
            history=history, number=number, action='updated',
            snapshot={'content_markdown': f'Versión {number}'},
            secrets={'password': 'encrypted-token'},
            changes=[{'field': 'title', 'label': 'Título', 'old': 'Antes', 'new': 'Después'}],
            changed_fields=[{'field': 'title', 'label': 'Título'}],
        )
        for number in range(1, 22)
    ])

    with django_assert_num_queries(4):
        response = client.get('/api/entity-history/document/9001/', {'page': 2})

    assert response.status_code == 200
    assert response.data['count'] == 21
    assert response.data['num_pages'] == 2
    assert response.data['page'] == 2
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['number'] == 1
    assert set(response.data['results'][0]) == {
        'id', 'number', 'occurred_at', 'action', 'actor', 'source',
        'complete', 'fields', 'evidence',
    }


@pytest.mark.parametrize(
    'is_superuser,expected_status', [(False, 403), (True, 200)],
    ids=['staff', 'superuser'],
)
def test_accounting_history_requires_superuser(is_superuser, expected_status):
    """Fails if a staff account can read the stronger per-record accounting audit trail."""
    user = get_user_model().objects.create_user(
        username=f'accounting-{is_superuser}', is_staff=True, is_superuser=is_superuser,
    )
    client = APIClient()
    client.force_authenticate(user)
    history = EntityHistory.objects.create(
        entity_type='card_snapshot', object_id=7001, object_label='Saldo tarjeta', revision=1,
    )
    EntityRevision.objects.create(
        history=history, number=1, action='created', snapshot={'card_name': 'Tarjeta'},
    )

    response = client.get('/api/entity-history/card_snapshot/7001/')

    assert response.status_code == expected_status
