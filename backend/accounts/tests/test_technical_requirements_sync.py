import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import DataModelEntity, Deliverable, Project, Requirement, UserProfile
from accounts.services.technical_requirements_sync import (
    compute_sync_diff,
    sync_technical_requirements_for_project,
)
from content.models import BusinessProposal, ProposalSection

User = get_user_model()


@pytest.mark.django_db
def test_sync_creates_deliverable_and_requirements_from_technical_document():
    admin = User.objects.create_user(username='a@sync.com', email='a@sync.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username='c@sync.com', email='c@sync.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)

    project = Project.objects.create(name='P', client=client)
    bp = BusinessProposal.objects.create(
        title='BP', client_name='C', total_investment=Decimal('1'),
        hosting_percent=30, status='accepted',
    )
    d = Deliverable.objects.create(
        project=project, title='Prop', category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=client,
    )
    bp.deliverable = d
    bp.save(update_fields=['deliverable_id'])

    ProposalSection.objects.create(
        proposal=bp,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
        title='Técnico',
        order=1,
        content_json={
            'epics': [
                {
                    'epicKey': 'epic-a',
                    'title': 'Épica A',
                    'requirements': [
                        {
                            'flowKey': 'flow-1',
                            'title': 'Req uno',
                            'description': 'D',
                            'configuration': '',
                            'usageFlow': 'Flujo',
                        },
                    ],
                },
            ],
        },
    )

    result = sync_technical_requirements_for_project(project, admin)
    assert result['ok'] is True
    assert result['requirements_created'] >= 1

    epic_d = Deliverable.objects.get(project=project, source_epic_key='epic-a')
    assert epic_d.title == 'Épica A'
    req = Requirement.objects.get(deliverable=epic_d, source_flow_key='flow-1')
    assert req.title == 'Req uno'
    assert req.synced_from_proposal is True


@pytest.mark.django_db
def test_sync_returns_error_without_linked_proposal():
    admin = User.objects.create_user(username='a2@sync.com', email='a2@sync.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username='c2@sync.com', email='c2@sync.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name='P2', client=client)

    result = sync_technical_requirements_for_project(project, admin)
    assert result['ok'] is False
    assert result['error'] == 'no_linked_proposal'


# =========================================================================
# Helpers shared by data model entity sync tests
# =========================================================================


def _make_sync_setup(admin_email, client_email, project_name, entities=None):
    """
    Create the minimal DB objects required to run a sync with data model entities.

    The content_json always includes a minimal epic so the sync creates at least one
    synced_deliverable — entity sync only runs against deliverables derived from epics.
    """
    admin = User.objects.create_user(username=admin_email, email=admin_email, password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username=client_email, email=client_email, password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)

    project = Project.objects.create(name=project_name, client=client)
    bp = BusinessProposal.objects.create(
        title='BP', client_name='C', total_investment=Decimal('1'),
        hosting_percent=30, status='accepted',
    )
    d = Deliverable.objects.create(
        project=project, title='Prop',
        category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=client,
    )
    bp.deliverable = d
    bp.save(update_fields=['deliverable_id'])

    # Always include a minimal epic so synced_deliverables is populated.
    # Entity sync only runs against deliverables created from epics.
    content_json = {
        'epics': [
            {
                'epicKey': 'epic-test',
                'title': 'Test Epic',
                'requirements': [
                    {'flowKey': 'flow-test', 'title': 'Test Req', 'description': ''},
                ],
            },
        ],
    }
    if entities is not None:
        content_json['dataModel'] = {'entities': entities}

    ProposalSection.objects.create(
        proposal=bp,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
        title='Técnico',
        order=1,
        content_json=content_json,
    )

    return project, admin, d


# =========================================================================
# 1C — Data model entity sync tests
# =========================================================================


@pytest.mark.django_db
def test_sync_creates_data_model_entities_from_proposal():
    project, admin, _ = _make_sync_setup(
        'a3@sync.com', 'c3@sync.com', 'P3',
        entities=[
            {'name': 'User', 'description': 'A user', 'keyFields': 'id, email'},
            {'name': 'Order', 'description': 'An order', 'keyFields': 'id'},
        ],
    )

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['entities_created'] == 2
    # Entities are linked to the deliverable created from the epic, not the proposal deliverable
    assert DataModelEntity.objects.filter(
        deliverable__project=project, name='User',
    ).exists()
    assert DataModelEntity.objects.filter(
        deliverable__project=project, name='Order',
    ).exists()


@pytest.mark.django_db
def test_sync_sets_synced_from_proposal_flag_on_entities():
    project, admin, _ = _make_sync_setup(
        'a4@sync.com', 'c4@sync.com', 'P4',
        entities=[{'name': 'Product', 'keyFields': 'id, sku'}],
    )

    sync_technical_requirements_for_project(project, admin)

    entity = DataModelEntity.objects.get(
        deliverable__project=project, source_entity_name='Product',
    )
    assert entity.synced_from_proposal is True


@pytest.mark.django_db
def test_sync_is_idempotent_on_second_run_with_same_entities():
    project, admin, _ = _make_sync_setup(
        'a5@sync.com', 'c5@sync.com', 'P5',
        entities=[{'name': 'Invoice', 'description': 'v1', 'keyFields': 'id'}],
    )
    sync_technical_requirements_for_project(project, admin)

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    # No new entity created on second run (idempotent)
    assert DataModelEntity.objects.filter(
        deliverable__project=project, source_entity_name='Invoice',
    ).count() == 1


@pytest.mark.django_db
def test_sync_updates_entity_when_description_changes():
    project, admin, prop_deliverable = _make_sync_setup(
        'a6@sync.com', 'c6@sync.com', 'P6',
        entities=[{'name': 'Cart', 'description': 'original', 'keyFields': ''}],
    )
    sync_technical_requirements_for_project(project, admin)

    # Change the proposal section's content_json in-place (simulate updated proposal)
    section = ProposalSection.objects.get(
        proposal__deliverable=prop_deliverable,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['dataModel'] = {'entities': [
        {'name': 'Cart', 'description': 'updated description', 'keyFields': ''},
    ]}
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['entities_updated'] == 1
    entity = DataModelEntity.objects.get(
        deliverable__project=project, source_entity_name='Cart',
    )
    assert entity.description == 'updated description'


@pytest.mark.django_db
def test_sync_archives_removed_entities_when_delete_removed_is_true():
    project, admin, prop_deliverable = _make_sync_setup(
        'a7@sync.com', 'c7@sync.com', 'P7',
        entities=[
            {'name': 'Keep', 'description': '', 'keyFields': ''},
            {'name': 'Remove', 'description': '', 'keyFields': ''},
        ],
    )
    sync_technical_requirements_for_project(project, admin, delete_removed=False)

    # Now remove 'Remove' from the proposal
    section = ProposalSection.objects.get(
        proposal__deliverable=prop_deliverable,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['dataModel'] = {'entities': [
        {'name': 'Keep', 'description': '', 'keyFields': ''},
    ]}
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin, delete_removed=True)

    assert result['ok'] is True
    assert result['entities_deleted'] == 1
    removed = DataModelEntity.objects.get(
        deliverable__project=project, source_entity_name='Remove',
    )
    assert removed.is_archived is True


@pytest.mark.django_db
def test_sync_does_not_archive_entities_when_delete_removed_is_false():
    project, admin, prop_deliverable = _make_sync_setup(
        'a8@sync.com', 'c8@sync.com', 'P8',
        entities=[
            {'name': 'Keep2', 'description': '', 'keyFields': ''},
            {'name': 'Remove2', 'description': '', 'keyFields': ''},
        ],
    )
    sync_technical_requirements_for_project(project, admin, delete_removed=False)

    section = ProposalSection.objects.get(
        proposal__deliverable=prop_deliverable,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['dataModel'] = {'entities': [
        {'name': 'Keep2', 'description': '', 'keyFields': ''},
    ]}
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin, delete_removed=False)

    assert result['ok'] is True
    assert result['entities_deleted'] == 0
    removed = DataModelEntity.objects.get(
        deliverable__project=project, source_entity_name='Remove2',
    )
    assert removed.is_archived is False


@pytest.mark.django_db
def test_sync_handles_empty_entities_list_without_error():
    project, admin, _ = _make_sync_setup(
        'a9@sync.com', 'c9@sync.com', 'P9',
        entities=[],
    )

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['entities_created'] == 0


@pytest.mark.django_db
def test_sync_handles_missing_data_model_key_without_error():
    project, admin, _ = _make_sync_setup(
        'a10@sync.com', 'c10@sync.com', 'P10',
        entities=None,  # content_json has no 'dataModel' key
    )

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['entities_created'] == 0


# =========================================================================
# 1C — compute_sync_diff tests for data model entities
# =========================================================================


@pytest.mark.django_db
def test_compute_sync_diff_reports_entity_to_create():
    admin = User.objects.create_user(username='d1@sync.com', email='d1@sync.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username='dc1@sync.com', email='dc1@sync.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name='Diff1', client=client)

    new_json = {'dataModel': {'entities': [{'name': 'NewEntity', 'description': 'x'}]}}
    diff = compute_sync_diff(project, new_json)

    assert any(e['name'] == 'NewEntity' for e in diff['data_model_entities']['to_create'])
    assert diff['data_model_entities']['to_update'] == []
    assert diff['data_model_entities']['to_delete'] == []


@pytest.mark.django_db
def test_compute_sync_diff_reports_entity_to_update_when_description_changed():
    admin = User.objects.create_user(username='d2@sync.com', email='d2@sync.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username='dc2@sync.com', email='dc2@sync.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name='Diff2', client=client)

    d = Deliverable.objects.create(
        project=project, title='D',
        category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=admin,
    )
    DataModelEntity.objects.create(
        deliverable=d,
        name='Existing',
        description='old',
        key_fields='',
        source_entity_name='Existing',
    )

    new_json = {'dataModel': {'entities': [{'name': 'Existing', 'description': 'new'}]}}
    diff = compute_sync_diff(project, new_json)

    assert diff['data_model_entities']['to_create'] == []
    updates = diff['data_model_entities']['to_update']
    assert len(updates) == 1
    assert updates[0]['name'] == 'Existing'
    assert 'description' in updates[0]['changed_fields']


@pytest.mark.django_db
def test_compute_sync_diff_reports_entity_to_delete_when_removed():
    admin = User.objects.create_user(username='d3@sync.com', email='d3@sync.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username='dc3@sync.com', email='dc3@sync.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name='Diff3', client=client)

    d = Deliverable.objects.create(
        project=project, title='D',
        category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=admin,
    )
    DataModelEntity.objects.create(
        deliverable=d,
        name='GoneEntity',
        source_entity_name='GoneEntity',
    )

    new_json = {'dataModel': {'entities': []}}
    diff = compute_sync_diff(project, new_json)

    assert diff['data_model_entities']['to_create'] == []
    assert diff['data_model_entities']['to_update'] == []
    assert any(e['name'] == 'GoneEntity' for e in diff['data_model_entities']['to_delete'])
