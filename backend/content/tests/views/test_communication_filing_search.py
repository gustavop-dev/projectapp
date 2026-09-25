"""Filing and ID-search contracts shared by the communications and documents panels."""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.models import CommunicationFolder, CommunicationThread
from content.services import communication_service


pytestmark = pytest.mark.django_db
User = get_user_model()


def make_client(email):
    user = User.objects.create_user(
        username=email, email=email, password='testpass123',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def test_thread_creation_files_a_manual_thread_in_a_compatible_folder(admin_client, admin_user):
    """Falla si crear un hilo con carpeta válida no persiste su ubicación."""
    client = make_client('filing-create@example.com')
    folder = CommunicationFolder.objects.create(name='Actas', client=client)

    response = admin_client.post(reverse('communication-threads'), {
        'client': client.id, 'title': 'Acta de seguimiento', 'folder': folder.id,
    }, format='json')

    assert response.status_code == 201
    assert response.data['folder_id'] == folder.id
    assert CommunicationThread.objects.get(pk=response.data['id']).folder_id == folder.id


def test_thread_filing_rejects_a_foreign_folder_and_keeps_the_thread_unfiled(admin_client, admin_user):
    """Falla si un hilo puede guardarse dentro de la carpeta de otro cliente."""
    owner = make_client('filing-owner@example.com')
    foreign = make_client('filing-foreign@example.com')
    folder = CommunicationFolder.objects.create(name='Ajena', client=foreign)

    response = admin_client.post(reverse('communication-threads'), {
        'client': owner.id, 'title': 'No archivable', 'folder': folder.id,
    }, format='json')

    assert response.status_code == 400
    assert response.data['folder'] == 'La carpeta no corresponde al cliente o proyecto del hilo.'
    assert CommunicationThread.objects.filter(
        client=owner, title='No archivable',
    ).exists() is False


def test_managed_root_cannot_be_filed_in_a_folder(admin_client):
    """Falla si la comunicación madre deja de permanecer fija en la raíz."""
    client = make_client('filing-root@example.com')
    project = Project.objects.create(name='Proyecto raíz', client=client.user)
    folder = CommunicationFolder.objects.create(name='Manual', client=client, project=project)

    response = admin_client.patch(
        reverse('communication-thread-detail', args=[project.communication_root_thread.id]),
        {'folder': folder.id}, format='json',
    )

    assert response.status_code == 400
    assert response.data['folder'] == 'La comunicación madre permanece en la raíz.'
    project.communication_root_thread.refresh_from_db()
    assert project.communication_root_thread.folder_id is None


def test_closed_thread_accepts_only_a_folder_reassignment(admin_client, admin_user):
    """Falla si cerrar un hilo impide organizarlo después de cerrar la conversación."""
    client = make_client('filing-closed@example.com')
    folder = CommunicationFolder.objects.create(name='Cerrados', client=client)
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Cerrado y archivado',
    )
    communication_service.close_thread(thread, actor=admin_user)

    response = admin_client.patch(
        reverse('communication-thread-detail', args=[thread.id]), {'folder': folder.id}, format='json',
    )

    assert response.status_code == 200
    assert response.data['folder_id'] == folder.id


def test_project_reassignment_clears_an_incompatible_folder(admin_client, admin_user):
    """Falla si cambiar de proyecto deja un hilo en la carpeta del proyecto anterior."""
    client = make_client('filing-reassign@example.com')
    first = Project.objects.create(name='Inicial', client=client.user)
    second = Project.objects.create(name='Destino', client=client.user)
    old_folder = CommunicationFolder.objects.create(
        name='Iniciales', client=client, project=first,
    )
    thread = communication_service.create_thread(
        actor=admin_user, client=client, project=first, folder=old_folder, title='Mover',
    )

    response = admin_client.patch(
        reverse('communication-thread-detail', args=[thread.id]), {'project': second.id}, format='json',
    )

    assert response.status_code == 200
    assert (response.data['project_id'], response.data['folder_id']) == (second.id, None)


def test_folder_filter_and_without_folder_keep_distinct_thread_sets(admin_client, admin_user):
    """Falla si los filtros de carpeta mezclan hilos archivados y sin carpeta."""
    client = make_client('filing-filter@example.com')
    folder = CommunicationFolder.objects.create(name='Seguimiento', client=client)
    filed = communication_service.create_thread(
        actor=admin_user, client=client, folder=folder, title='En carpeta',
    )
    loose = communication_service.create_thread(
        actor=admin_user, client=client, title='Sin carpeta',
    )

    in_folder = admin_client.get(reverse('communication-threads'), {'folder': folder.id})
    without_folder = admin_client.get(reverse('communication-threads'), {'folder': 'none'})

    assert [row['id'] for row in in_folder.data['results']] == [filed.id]
    assert [row['id'] for row in without_folder.data['results']] == [loose.id]


def test_search_ignores_folder_but_keeps_the_client_and_project_scope(admin_client, admin_user):
    """Falla si una búsqueda global queda atrapada en la carpeta seleccionada."""
    client = make_client('filing-search@example.com')
    project = Project.objects.create(name='Motor', client=client.user)
    folder = CommunicationFolder.objects.create(name='Contratos', client=client, project=project)
    thread = communication_service.create_thread(
        actor=admin_user,
        client=client,
        project=project,
        folder=folder,
        title='Clave singular de búsqueda',
    )

    response = admin_client.get(reverse('communication-threads'), {
        'q': 'singular', 'folder': 'none', 'client': client.id, 'project': project.id,
    })

    assert response.status_code == 200
    assert [row['id'] for row in response.data['results']] == [thread.id]


def test_thread_number_search_unites_text_and_id_while_hash_is_exact(admin_client, admin_user):
    """Falla si buscar un número deja de encontrar el ID y las referencias del hilo."""
    client = make_client('filing-id@example.com')
    thread_by_id = communication_service.create_thread(
        actor=admin_user, client=client, title='Conversación identificada',
    )
    thread_by_text = communication_service.create_thread(
        actor=admin_user, client=client, title=f'Referencia {thread_by_id.id}',
    )
    thread_exact = admin_client.get(reverse('communication-threads'), {'q': f'#{thread_by_id.id}'})
    thread_numeric = admin_client.get(reverse('communication-threads'), {'q': str(thread_by_id.id)})

    assert [row['id'] for row in thread_exact.data['results']] == [thread_by_id.id]
    assert {row['id'] for row in thread_numeric.data['results']} == {
        thread_by_id.id, thread_by_text.id,
    }


def test_thread_id_search_excludes_archived_records_from_the_default_scope(admin_client, admin_user):
    """Falla si una búsqueda por ID vuelve a exponer hilos archivados por defecto."""
    client = make_client('filing-id-archive@example.com')
    thread = communication_service.create_thread(
        actor=admin_user, client=client, title='Hilo archivado',
    )
    communication_service.archive_thread(thread, actor=admin_user)
    thread_response = admin_client.get(reverse('communication-threads'), {'q': f'#{thread.id}'})

    assert thread_response.data['results'] == []
