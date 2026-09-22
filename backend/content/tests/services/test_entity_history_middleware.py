import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import path

from content.models import Document, EntityHistory
from content.services.entity_history import EntityHistoryMiddleware


pytestmark = pytest.mark.django_db


def update_then_reject(_request, document_id):
    document = Document.objects.get(pk=document_id)
    document.title = 'Rechazado'
    document.save(update_fields=['title'])
    return HttpResponse(status=400)


def update_then_raise(_request, document_id):
    document = Document.objects.get(pk=document_id)
    document.title = 'Interrumpido'
    document.save(update_fields=['title'])
    raise RuntimeError('unexpected failure')


urlpatterns = [
    path('api/history-controlled/<int:document_id>/', update_then_reject),
    path('api/history-exception/<int:document_id>/', update_then_raise),
]


def test_api_post_attributes_revision_to_request_user(rf):
    user = get_user_model().objects.create_user(username='history-editor')
    request = rf.post('/api/documents/')
    request.user = user

    def create_document(_request):
        document = Document.objects.create(title='Contrato')
        return HttpResponse(str(document.pk), status=201)

    response = EntityHistoryMiddleware(create_document)(request)
    revision = EntityHistory.objects.get(
        entity_type='document', object_id=int(response.content),
    ).entries.get()

    assert revision.actor_label == 'history-editor'
    assert revision.source == 'http'


@override_settings(ROOT_URLCONF=__name__)
def test_api_post_preserves_tracked_write_on_error_response():
    document = Document.objects.create(title='Original')
    history = EntityHistory.objects.get(entity_type='document', object_id=document.pk)
    revision_count = history.entries.count()

    response = Client().post(f'/api/history-controlled/{document.pk}/')
    document.refresh_from_db()

    assert response.status_code == 400
    assert document.title == 'Rechazado'
    assert history.entries.count() == revision_count + 1


@override_settings(ROOT_URLCONF=__name__)
def test_api_post_rolls_back_tracked_write_on_exception():
    document = Document.objects.create(title='Original')
    history = EntityHistory.objects.get(entity_type='document', object_id=document.pk)
    revision_count = history.entries.count()

    response = Client(raise_request_exception=False).post(
        f'/api/history-exception/{document.pk}/',
    )
    document.refresh_from_db()

    assert response.status_code == 500
    assert document.title == 'Original'
    assert history.entries.count() == revision_count
