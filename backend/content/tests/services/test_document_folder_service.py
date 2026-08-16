"""La cascada de cambio de cliente de una carpeta: preview, modos y auditoría.

Las reglas fijadas acá son el punto 7 del ticket, con el criterio de PA-55:
la carpeta dice a qué afecta ANTES de confirmar, las cuentas emitidas nunca se
reescriben, lo que alguien asignó a mano a otro cliente se respeta, y cada
registro tocado deja su fila de auditoría.
"""
import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model

from content.models import (
    AccountingChangeLog,
    Document,
    DocumentCollectionAccount,
    DocumentFolder,
)
from content.services import document_folder_service
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

pytestmark = pytest.mark.django_db

EntityType = AccountingChangeLog.EntityType


def make_client(email, *, first='Ana', last='Pérez'):
    user = get_user_model().objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first, last_name=last,
    )
    return UserProfile.objects.create(user=user, cedula='1049654583')


def make_cuenta(folder, profile, *, status, title='CC'):
    document = Document.objects.create(
        title=title,
        folder=folder,
        document_type=get_collection_account_document_type(),
        commercial_status=status,
        client_user=profile.user,
    )
    DocumentCollectionAccount.objects.create(
        document=document, customer_name='Cliente Viejo',
    )
    return document


@pytest.fixture
def kore(db):
    return make_client('kore@example.com', first='Kore', last='SAS')


@pytest.fixture
def ana(db):
    return make_client('ana@example.com')


@pytest.fixture
def nestor(db):
    return make_client('nestor@example.com', first='Néstor')


@pytest.fixture
def folder(kore):
    return DocumentFolder.objects.create(name='Kore', client_user=kore.user)


class TestChangeClientPreview:
    def test_reports_the_whole_branch_that_would_move(self, folder, kore, ana):
        Document.objects.create(title='A', folder=folder, client_user=kore.user)
        sub = DocumentFolder.objects.create(
            name='Kore - Diseño', parent=folder, client_user=kore.user,
        )
        Document.objects.create(title='B', folder=sub, client_user=kore.user)

        preview = document_folder_service.change_client_preview(folder, ana)

        assert preview['totals']['documents'] == 2
        assert preview['totals']['folders'] == 1
        assert preview['new_client']['profile_id'] == ana.pk

    def test_an_issued_collection_account_is_blocked(self, folder, kore, ana):
        issued = make_cuenta(
            folder, kore, status=Document.CommercialStatus.ISSUED,
        )

        preview = document_folder_service.change_client_preview(folder, ana)

        assert preview['totals']['blocked'] == 1
        assert issued.pk not in [row['id'] for row in preview['documents_move']]

    def test_a_draft_collection_account_still_moves(self, folder, kore, ana):
        draft = make_cuenta(folder, kore, status=Document.CommercialStatus.DRAFT)

        preview = document_folder_service.change_client_preview(folder, ana)

        assert draft.pk in [row['id'] for row in preview['documents_move']]

    def test_a_document_of_a_third_client_is_left_alone(
        self, folder, kore, ana, nestor,
    ):
        foreign = Document.objects.create(
            title='De Néstor', folder=folder, client_user=nestor.user,
        )

        preview = document_folder_service.change_client_preview(folder, ana)

        assert preview['totals']['foreign'] == 1
        assert foreign.pk not in [row['id'] for row in preview['documents_move']]

    def test_a_subfolder_of_another_client_prunes_its_whole_branch(
        self, folder, kore, ana, nestor,
    ):
        """Cambiar Kore por Ana no puede meterse en la rama de Néstor."""
        foreign_sub = DocumentFolder.objects.create(
            name='Néstor', parent=folder, client_user=nestor.user,
        )
        buried = Document.objects.create(
            title='Enterrado', folder=foreign_sub, client_user=kore.user,
        )

        preview = document_folder_service.change_client_preview(folder, ana)

        assert preview['totals']['foreign_folders'] == 1
        assert buried.pk not in [row['id'] for row in preview['documents_move']]

    def test_a_first_assignment_only_reaches_what_has_no_client(
        self, ana, nestor,
    ):
        orphan_folder = DocumentFolder.objects.create(name='Sin dueño')
        loose = Document.objects.create(title='Suelto', folder=orphan_folder)
        taken = Document.objects.create(
            title='De Néstor', folder=orphan_folder, client_user=nestor.user,
        )

        preview = document_folder_service.change_client_preview(
            orphan_folder, ana,
        )

        moving = [row['id'] for row in preview['documents_move']]
        assert loose.pk in moving
        assert taken.pk not in moving


class TestChangeClientApply:
    def test_propagate_moves_the_branch(self, folder, kore, ana, admin_user):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )
        sub = DocumentFolder.objects.create(
            name='Sub', parent=folder, client_user=kore.user,
        )

        document_folder_service.change_client_apply(
            folder, ana, document_folder_service.MODE_PROPAGATE, admin_user,
        )

        folder.refresh_from_db()
        document.refresh_from_db()
        sub.refresh_from_db()
        assert folder.client_user == ana.user
        assert document.client_user == ana.user
        assert sub.client_user == ana.user

    def test_folder_only_leaves_the_content_where_it_was(
        self, folder, kore, ana, admin_user,
    ):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )

        document_folder_service.change_client_apply(
            folder, ana, document_folder_service.MODE_FOLDER_ONLY, admin_user,
        )

        folder.refresh_from_db()
        document.refresh_from_db()
        assert folder.client_user == ana.user
        assert document.client_user == kore.user

    def test_an_issued_account_is_never_rewritten(
        self, folder, kore, ana, admin_user,
    ):
        issued = make_cuenta(
            folder, kore, status=Document.CommercialStatus.ISSUED,
        )

        result = document_folder_service.change_client_apply(
            folder, ana, document_folder_service.MODE_PROPAGATE, admin_user,
        )

        issued.refresh_from_db()
        assert issued.client_user == kore.user
        assert result['skipped']['blocked'] == 1

    def test_a_project_of_the_old_client_is_unlinked(
        self, folder, kore, ana, admin_user,
    ):
        """Un proyecto de Kore no se sostiene bajo un documento de Ana."""
        project = Project.objects.create(name='Kore - Diseño', client=kore.user)
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user, project=project,
        )

        document_folder_service.change_client_apply(
            folder, ana, document_folder_service.MODE_PROPAGATE, admin_user,
        )

        document.refresh_from_db()
        assert document.client_user == ana.user
        assert document.project is None

    def test_every_touched_record_leaves_an_audit_row(
        self, folder, kore, ana, admin_user,
    ):
        document = Document.objects.create(
            title='A', folder=folder, client_user=kore.user,
        )

        document_folder_service.change_client_apply(
            folder, ana, document_folder_service.MODE_PROPAGATE, admin_user,
        )

        assert AccountingChangeLog.objects.filter(
            entity_type=EntityType.DOCUMENT_FOLDER, object_id=folder.pk,
        ).count() == 1
        assert AccountingChangeLog.objects.filter(
            entity_type=EntityType.DOCUMENT, object_id=document.pk,
        ).count() == 1

    def test_a_foreign_document_keeps_its_client(
        self, folder, kore, ana, nestor, admin_user,
    ):
        foreign = Document.objects.create(
            title='De Néstor', folder=folder, client_user=nestor.user,
        )

        document_folder_service.change_client_apply(
            folder, ana, document_folder_service.MODE_PROPAGATE, admin_user,
        )

        foreign.refresh_from_db()
        assert foreign.client_user == nestor.user
