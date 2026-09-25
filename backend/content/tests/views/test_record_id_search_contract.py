"""Document-manager contract for exact and free-text numeric record searches."""
import pytest
from django.urls import reverse

from content.models import Document, DocumentType


pytestmark = pytest.mark.django_db


def test_document_number_search_unites_text_and_id_while_hash_is_exact(admin_client):
    """Falla si buscar un número deja de encontrar el ID y las referencias del documento."""
    document_type = DocumentType.objects.create(code='record-id', name='Record ID')
    document_by_id = Document.objects.create(
        title='Documento identificado', document_type=document_type,
    )
    document_by_text = Document.objects.create(
        title=f'Referencia {document_by_id.id}', document_type=document_type,
    )

    exact = admin_client.get(
        reverse('browse-documents'), {'search': f'#{document_by_id.id}'},
    )
    numeric = admin_client.get(
        reverse('browse-documents'), {'search': str(document_by_id.id)},
    )

    assert [row['id'] for row in exact.data['results']] == [document_by_id.id]
    assert {row['id'] for row in numeric.data['results']} == {
        document_by_id.id, document_by_text.id,
    }


def test_document_id_search_excludes_archived_records_from_the_default_scope(admin_client):
    """Falla si una búsqueda por ID vuelve a exponer documentos archivados por defecto."""
    document_type = DocumentType.objects.create(
        code='record-id-archived', name='Record ID archived',
    )
    document = Document.objects.create(
        title='Documento archivado', document_type=document_type,
    )
    Document.objects.filter(pk=document.id).update(is_archived=True)

    response = admin_client.get(
        reverse('browse-documents'), {'search': f'#{document.id}'},
    )

    assert response.data['results'] == []
