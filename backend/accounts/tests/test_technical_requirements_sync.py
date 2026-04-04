import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import DataModelEntity, Deliverable, Project, Requirement, UserProfile
from accounts.services.technical_requirements_sync import (
    compute_sync_diff,
    sync_technical_requirements_for_deliverable,
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


# =========================================================================
# compute_sync_diff — epic and requirement diff
# =========================================================================


def _make_project_with_deliverable(prefix):
    admin = User.objects.create_user(username=f'{prefix}adm@sync.com', email=f'{prefix}adm@sync.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username=f'{prefix}cli@sync.com', email=f'{prefix}cli@sync.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name=f'{prefix}P', client=client)
    return project, admin, client


@pytest.mark.django_db
def test_compute_sync_diff_reports_epic_to_create_when_no_deliverable_exists():
    """Epics not in DB appear in to_create."""
    project, _, _ = _make_project_with_deliverable('e1')
    new_json = {'epics': [{'epicKey': 'epic-new', 'title': 'New Epic', 'requirements': []}]}

    diff = compute_sync_diff(project, new_json)

    assert any(e['epicKey'] == 'epic-new' for e in diff['epics']['to_create'])
    assert diff['epics']['to_update'] == []
    assert diff['epics']['to_delete'] == []


@pytest.mark.django_db
def test_compute_sync_diff_reports_epic_to_update_when_title_changed():
    """Existing deliverable with changed title appears in to_update."""
    project, admin, client = _make_project_with_deliverable('e2')
    Deliverable.objects.create(
        project=project, title='Old Title', source_epic_key='epic-x',
        category=Deliverable.CATEGORY_DOCUMENTS, file=None, uploaded_by=admin,
    )
    new_json = {'epics': [{'epicKey': 'epic-x', 'title': 'New Title', 'requirements': []}]}

    diff = compute_sync_diff(project, new_json)

    assert diff['epics']['to_create'] == []
    assert any(e['epicKey'] == 'epic-x' for e in diff['epics']['to_update'])


@pytest.mark.django_db
def test_compute_sync_diff_reports_epics_to_delete_when_removed():
    """Deliverables in DB but absent from JSON appear in to_delete."""
    project, admin, client = _make_project_with_deliverable('e3')
    Deliverable.objects.create(
        project=project, title='Stale', source_epic_key='epic-stale',
        category=Deliverable.CATEGORY_DOCUMENTS, file=None, uploaded_by=admin,
    )
    new_json = {'epics': []}

    diff = compute_sync_diff(project, new_json)

    assert any(e['epicKey'] == 'epic-stale' for e in diff['epics']['to_delete'])


@pytest.mark.django_db
def test_compute_sync_diff_reports_requirement_to_create():
    """Requirements not in DB appear in requirements.to_create."""
    project, _, _ = _make_project_with_deliverable('e4')
    new_json = {'epics': [
        {'epicKey': 'epic-r', 'title': 'E', 'requirements': [
            {'flowKey': 'flow-r', 'title': 'New Req', 'description': ''},
        ]},
    ]}

    diff = compute_sync_diff(project, new_json)

    assert any(r['flowKey'] == 'flow-r' for r in diff['requirements']['to_create'])


@pytest.mark.django_db
def test_compute_sync_diff_reports_requirement_to_update_when_title_changed():
    """Existing requirement with changed title appears in requirements.to_update."""
    project, admin, _ = _make_project_with_deliverable('e5')
    d = Deliverable.objects.create(
        project=project, title='E', source_epic_key='epic-q',
        category=Deliverable.CATEGORY_DOCUMENTS, file=None, uploaded_by=admin,
    )
    Requirement.objects.create(
        deliverable=d, title='Old Req', source_flow_key='flow-q',
        status=Requirement.STATUS_BACKLOG, priority=Requirement.PRIORITY_MEDIUM,
    )
    new_json = {'epics': [
        {'epicKey': 'epic-q', 'title': 'E', 'requirements': [
            {'flowKey': 'flow-q', 'title': 'Changed Req'},
        ]},
    ]}

    diff = compute_sync_diff(project, new_json)

    assert diff['requirements']['to_create'] == []
    assert any(r['flowKey'] == 'flow-q' for r in diff['requirements']['to_update'])


@pytest.mark.django_db
def test_compute_sync_diff_reports_requirement_to_delete():
    """Requirements in DB absent from JSON appear in requirements.to_delete."""
    project, admin, _ = _make_project_with_deliverable('e6')
    d = Deliverable.objects.create(
        project=project, title='E', source_epic_key='epic-s',
        category=Deliverable.CATEGORY_DOCUMENTS, file=None, uploaded_by=admin,
    )
    Requirement.objects.create(
        deliverable=d, title='Old', source_flow_key='flow-s',
        status=Requirement.STATUS_BACKLOG, priority=Requirement.PRIORITY_MEDIUM,
    )
    new_json = {'epics': [{'epicKey': 'epic-s', 'title': 'E', 'requirements': []}]}

    diff = compute_sync_diff(project, new_json)

    assert any(r['flowKey'] == 'flow-s' for r in diff['requirements']['to_delete'])


@pytest.mark.django_db
def test_compute_sync_diff_skips_non_dict_epic():
    """Non-dict items in the epics list are silently skipped."""
    project, _, _ = _make_project_with_deliverable('e7')
    new_json = {'epics': ['not-a-dict', 42, {'epicKey': 'ok-key', 'title': 'OK', 'requirements': []}]}

    diff = compute_sync_diff(project, new_json)

    assert len(diff['epics']['to_create']) == 1
    assert diff['epics']['to_create'][0]['epicKey'] == 'ok-key'


@pytest.mark.django_db
def test_compute_sync_diff_assigns_synthetic_key_to_keyless_epic_with_reqs():
    """Epic without epicKey but with requirements gets a synthetic _sync_epic_N key."""
    project, _, _ = _make_project_with_deliverable('e8')
    new_json = {'epics': [
        {'title': 'No Key', 'requirements': [
            {'flowKey': 'flow-nk', 'title': 'A Req'},
        ]},
    ]}

    diff = compute_sync_diff(project, new_json)

    # Should create an epic with synthetic key (not to_delete or empty)
    created_keys = [e['epicKey'] for e in diff['epics']['to_create']]
    assert any(k.startswith('_sync_epic_') for k in created_keys)


@pytest.mark.django_db
def test_compute_sync_diff_entity_key_fields_change_reported():
    """When only key_fields changes on an entity, it appears in to_update."""
    project, admin, _ = _make_project_with_deliverable('e9')
    d = Deliverable.objects.create(
        project=project, title='D', category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=admin,
    )
    DataModelEntity.objects.create(
        deliverable=d, name='E', description='', key_fields='id',
        source_entity_name='E',
    )
    new_json = {'dataModel': {'entities': [{'name': 'E', 'description': '', 'keyFields': 'id, name'}]}}

    diff = compute_sync_diff(project, new_json)

    updates = diff['data_model_entities']['to_update']
    assert len(updates) == 1
    assert 'key_fields' in updates[0]['changed_fields']


# =========================================================================
# _sync_technical_requirements_core — update and delete paths
# =========================================================================


def _make_full_sync_setup(prefix, epics=None, entities=None):
    """Create full project+BP+ProposalSection fixture for sync tests."""
    admin = User.objects.create_user(username=f'{prefix}adm@s.com', email=f'{prefix}adm@s.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username=f'{prefix}cli@s.com', email=f'{prefix}cli@s.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name=f'{prefix}P', client=client)
    bp = BusinessProposal.objects.create(
        title='BP', client_name='C', total_investment=Decimal('1'),
        hosting_percent=30, status='accepted',
    )
    prop_d = Deliverable.objects.create(
        project=project, title='Prop', category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=client,
    )
    bp.deliverable = prop_d
    bp.save(update_fields=['deliverable_id'])
    content_json = {'epics': epics or []}
    if entities is not None:
        content_json['dataModel'] = {'entities': entities}
    ProposalSection.objects.create(
        proposal=bp, section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
        title='Técnico', order=1, content_json=content_json,
    )
    return project, admin, bp, prop_d


@pytest.mark.django_db
def test_sync_updates_deliverable_title_when_changed():
    """When epic title changes on second sync, deliverable title is updated."""
    project, admin, _, _ = _make_full_sync_setup('u1', epics=[
        {'epicKey': 'eup1', 'title': 'Original', 'requirements': []},
    ])
    sync_technical_requirements_for_project(project, admin)

    # Update epic title in the section
    section = ProposalSection.objects.get(
        proposal__deliverable__project=project,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['epics'][0]['title'] = 'Updated Title'
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin)

    assert result['deliverables_updated'] == 1
    d = Deliverable.objects.get(project=project, source_epic_key='eup1')
    assert d.title == 'Updated Title'


@pytest.mark.django_db
def test_sync_updates_existing_requirement_on_second_sync():
    """When a requirement already exists, its title and flow are updated."""
    project, admin, _, _ = _make_full_sync_setup('u2', epics=[
        {'epicKey': 'eup2', 'title': 'E', 'requirements': [
            {'flowKey': 'flow-upd', 'title': 'Original Req', 'usageFlow': 'v1'},
        ]},
    ])
    sync_technical_requirements_for_project(project, admin)

    section = ProposalSection.objects.get(
        proposal__deliverable__project=project,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['epics'][0]['requirements'][0]['title'] = 'Updated Req'
    section.content_json['epics'][0]['requirements'][0]['usageFlow'] = 'v2'
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin)

    assert result['requirements_updated'] == 1
    req = Requirement.objects.get(deliverable__project=project, source_flow_key='flow-upd')
    assert req.title == 'Updated Req'


@pytest.mark.django_db
def test_sync_skips_requirement_without_title_or_flow_key():
    """Requirements missing title or flowKey increment requirements_skipped counter."""
    project, admin, _, _ = _make_full_sync_setup('u3', epics=[
        {'epicKey': 'eup3', 'title': 'E', 'requirements': [
            {'flowKey': 'flow-ok', 'title': 'Valid Req'},
            {'flowKey': '', 'title': 'No Flow Key'},
            {'flowKey': 'flow-notitle', 'title': ''},
            'not-a-dict',
        ]},
    ])

    result = sync_technical_requirements_for_project(project, admin)

    assert result['requirements_skipped'] >= 3
    assert result['requirements_created'] == 1


@pytest.mark.django_db
def test_sync_archives_removed_deliverables_when_delete_removed_true():
    """With delete_removed=True, deliverables absent from JSON are archived."""
    project, admin, _, _ = _make_full_sync_setup('u4', epics=[
        {'epicKey': 'eup4', 'title': 'Keep', 'requirements': []},
        {'epicKey': 'eup4-gone', 'title': 'Gone', 'requirements': []},
    ])
    sync_technical_requirements_for_project(project, admin, delete_removed=False)

    # Remove 'Gone' from the section
    section = ProposalSection.objects.get(
        proposal__deliverable__project=project,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['epics'] = [{'epicKey': 'eup4', 'title': 'Keep', 'requirements': []}]
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin, delete_removed=True)

    assert result['deliverables_deleted'] >= 1
    gone = Deliverable.objects.get(project=project, source_epic_key='eup4-gone')
    assert gone.is_archived is True


@pytest.mark.django_db
def test_sync_archives_removed_requirements_when_delete_removed_true():
    """With delete_removed=True, requirements absent from JSON are archived."""
    project, admin, _, _ = _make_full_sync_setup('u5', epics=[
        {'epicKey': 'eup5', 'title': 'E', 'requirements': [
            {'flowKey': 'flow-keep', 'title': 'Keep'},
            {'flowKey': 'flow-gone', 'title': 'Gone'},
        ]},
    ])
    sync_technical_requirements_for_project(project, admin, delete_removed=False)

    section = ProposalSection.objects.get(
        proposal__deliverable__project=project,
        section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
    )
    section.content_json['epics'][0]['requirements'] = [
        {'flowKey': 'flow-keep', 'title': 'Keep'},
    ]
    section.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin, delete_removed=True)

    assert result['requirements_deleted'] == 1


@pytest.mark.django_db
def test_sync_sets_project_progress_to_zero_when_no_requirements():
    """project.progress is set to 0 when there are no requirements."""
    project, admin, _, _ = _make_full_sync_setup('u6', epics=[
        {'epicKey': 'eup6', 'title': 'E', 'requirements': []},
    ])

    result = sync_technical_requirements_for_project(project, admin)

    project.refresh_from_db()
    assert result['ok'] is True
    assert project.progress == 0


# =========================================================================
# sync_technical_requirements_for_deliverable
# =========================================================================


@pytest.mark.django_db
def test_sync_for_deliverable_returns_ok_when_bp_exists():
    """sync_technical_requirements_for_deliverable succeeds when deliverable has a BP."""
    project, admin, bp, prop_d = _make_full_sync_setup('del1', epics=[
        {'epicKey': 'del-epic', 'title': 'E', 'requirements': []},
    ])

    result = sync_technical_requirements_for_deliverable(prop_d, admin)

    assert result['ok'] is True


@pytest.mark.django_db
def test_sync_for_deliverable_returns_error_when_no_bp():
    """sync_technical_requirements_for_deliverable returns error when no BusinessProposal."""
    admin = User.objects.create_user(username='del2adm@s.com', email='del2adm@s.com', password='p')
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(username='del2cli@s.com', email='del2cli@s.com', password='p')
    UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    project = Project.objects.create(name='del2P', client=client)
    plain_d = Deliverable.objects.create(
        project=project, title='No BP', category=Deliverable.CATEGORY_DOCUMENTS,
        file=None, uploaded_by=admin,
    )

    result = sync_technical_requirements_for_deliverable(plain_d, admin)

    assert result['ok'] is False
    assert result['error'] == 'no_business_proposal'
