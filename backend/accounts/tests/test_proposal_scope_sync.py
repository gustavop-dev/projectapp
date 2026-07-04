"""
Tests for the rebuilt proposal→platform sync:
  * ProjectScopeItem mirror from functional_requirements (vistas/componentes/funcionalidades)
  * Requirement Kanban cards from technical_document, linked to their scope item
  * re-sync idempotency + preservation of client-owned Kanban state
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from accounts.models import (
    Deliverable,
    Project,
    ProjectPhase,
    ProjectScopeItem,
    Requirement,
    RequirementComment,
    UserProfile,
)
from accounts.services.technical_requirements_sync import (
    sync_technical_requirements_for_project,
)
from content.models import BusinessProposal, ProposalSection

User = get_user_model()


def _default_fr():
    return {
        'groups': [
            {
                'id': 'views', 'icon': '🖥️', 'title': 'Vistas', 'is_visible': True,
                'items': [
                    {'id': 'item-views-login', 'icon': '🏠', 'name': 'Login', 'description': 'Pantalla de acceso'},
                    {'id': 'item-views-home', 'name': 'Home', 'description': ''},
                ],
            },
            {
                'id': 'components', 'icon': '🧩', 'title': 'Componentes', 'is_visible': False,
                'items': [
                    {'id': 'item-components-navbar', 'name': 'Navbar', 'description': ''},
                ],
            },
        ],
        'additionalModules': [
            {
                'id': 'chat', 'icon': '💬', 'title': 'Chat',
                'items': [
                    {'id': 'item-chat-inbox', 'name': 'Inbox', 'description': ''},
                ],
            },
        ],
    }


def _default_epics():
    return [
        {
            'epicKey': 'auth', 'title': 'Autenticación',
            'requirements': [
                {
                    'flowKey': 'login-flow', 'title': 'Flujo de login',
                    'description': 'desc', 'usageFlow': 'flow', 'configuration': 'conf',
                    'priority': 'high', 'linked_item_ids': ['item-views-login'],
                },
                {
                    'flowKey': 'orphan-flow', 'title': 'Sin grupo',
                    'linked_item_ids': [],
                },
            ],
        },
    ]


def _setup(prefix, *, epics=None, fr=None):
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
    ProposalSection.objects.create(
        proposal=bp, section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
        title='Técnico', order=1, content_json={'epics': epics if epics is not None else _default_epics()},
    )
    if fr is not False:
        ProposalSection.objects.create(
            proposal=bp, section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
            title='Funcionales', order=2, content_json=fr if fr is not None else _default_fr(),
        )
    return project, admin, bp


def _section(bp, section_type):
    return ProposalSection.objects.get(proposal=bp, section_type=section_type)


@pytest.mark.django_db
def test_sync_creates_scope_items_from_functional_requirements():
    project, admin, _ = _setup('sc1')

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['scope_items_created'] == 4  # login, home, navbar, inbox
    login = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-views-login')
    assert login.name == 'Login'
    assert login.group_id == 'views'
    assert login.origin == ProjectScopeItem.ORIGIN_GROUP
    assert login.group_is_visible is True
    # hidden group is still mirrored, flagged not visible
    navbar = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-components-navbar')
    assert navbar.group_is_visible is False
    # additionalModules mirror with the ADDITIONAL origin
    inbox = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-chat-inbox')
    assert inbox.origin == ProjectScopeItem.ORIGIN_ADDITIONAL
    assert inbox.group_id == 'chat'


@pytest.mark.django_db
def test_sync_links_requirement_card_to_primary_scope_item():
    project, admin, _ = _setup('sc2')

    sync_technical_requirements_for_project(project, admin)

    linked = Requirement.objects.get(phase__project=project, source_flow_key='login-flow')
    assert linked.scope_item is not None
    assert linked.scope_item.source_item_id == 'item-views-login'
    assert linked.priority == 'high'
    # a requirement without linked_item_ids stays ungrouped
    orphan = Requirement.objects.get(phase__project=project, source_flow_key='orphan-flow')
    assert orphan.scope_item is None


@pytest.mark.django_db
def test_sync_ensures_phase_when_project_has_none():
    project, admin, bp = _setup('sc3')
    assert project.phases.count() == 0

    sync_technical_requirements_for_project(project, admin)

    assert project.phases.count() == 1
    phase = project.phases.first()
    assert phase.business_proposal_id == bp.id
    assert phase.order == 1


@pytest.mark.django_db
def test_resync_preserves_status_order_and_comments_but_updates_content():
    project, admin, bp = _setup('sc4')
    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='login-flow')
    req.status = Requirement.STATUS_IN_PROGRESS
    req.order = 99
    req.save(update_fields=['status', 'order'])
    RequirementComment.objects.create(requirement=req, user=admin, content='nota del equipo')

    # change proposal-authored content and re-sync
    tech = _section(bp, ProposalSection.SectionType.TECHNICAL_DOCUMENT)
    tech.content_json['epics'][0]['requirements'][0]['title'] = 'Login renombrado'
    tech.save(update_fields=['content_json'])

    result = sync_technical_requirements_for_project(project, admin)

    req.refresh_from_db()
    assert result['requirements_updated'] == 1
    assert req.title == 'Login renombrado'          # content overwritten
    assert req.status == Requirement.STATUS_IN_PROGRESS  # workflow preserved
    assert req.order == 99                           # order preserved
    assert req.comments.count() == 1                 # comments untouched


@pytest.mark.django_db
def test_resync_respects_content_overridden():
    project, admin, bp = _setup('sc5')
    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='login-flow')
    req.description = 'edición manual del admin'
    req.content_overridden = True
    req.save(update_fields=['description', 'content_overridden'])

    tech = _section(bp, ProposalSection.SectionType.TECHNICAL_DOCUMENT)
    tech.content_json['epics'][0]['requirements'][0]['description'] = 'nuevo desde propuesta'
    tech.save(update_fields=['content_json'])

    sync_technical_requirements_for_project(project, admin)

    req.refresh_from_db()
    assert req.description == 'edición manual del admin'  # preserved


@pytest.mark.django_db
def test_resync_archives_removed_scope_item_and_resurrects_readded():
    project, admin, bp = _setup('sc6')
    sync_technical_requirements_for_project(project, admin)

    import copy

    fr = _section(bp, ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS)
    original_groups = copy.deepcopy(fr.content_json['groups'])
    # remove the 'home' item from the views group
    fr.content_json['groups'][0]['items'] = [
        it for it in fr.content_json['groups'][0]['items'] if it['id'] != 'item-views-home'
    ]
    fr.save(update_fields=['content_json'])
    sync_technical_requirements_for_project(project, admin)

    home = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-views-home')
    assert home.is_archived is True

    # re-add it → resurrected
    fr.content_json['groups'] = original_groups
    fr.save(update_fields=['content_json'])
    result = sync_technical_requirements_for_project(project, admin)

    home.refresh_from_db()
    assert home.is_archived is False
    assert result['scope_items_unarchived'] == 1


@pytest.mark.django_db
def test_sync_is_idempotent_no_duplicates():
    project, admin, _ = _setup('sc7')
    sync_technical_requirements_for_project(project, admin)
    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['scope_items_created'] == 0
    assert result['requirements_created'] == 0
    assert ProjectScopeItem.objects.filter(phase__project=project).count() == 4
    assert Requirement.objects.filter(phase__project=project).count() == 2


@pytest.mark.django_db
def test_priority_mapping_defaults_to_medium_for_unknown():
    epics = [
        {
            'epicKey': 'e', 'title': 'E',
            'requirements': [
                {'flowKey': 'f1', 'title': 'R1', 'priority': 'urgent'},   # invalid → medium
                {'flowKey': 'f2', 'title': 'R2'},                          # missing → medium
                {'flowKey': 'f3', 'title': 'R3', 'priority': 'critical'},  # valid
            ],
        },
    ]
    project, admin, _ = _setup('sc8', epics=epics, fr=False)
    sync_technical_requirements_for_project(project, admin)

    assert Requirement.objects.get(phase__project=project, source_flow_key='f1').priority == 'medium'
    assert Requirement.objects.get(phase__project=project, source_flow_key='f2').priority == 'medium'
    assert Requirement.objects.get(phase__project=project, source_flow_key='f3').priority == 'critical'


@pytest.mark.django_db
def test_sync_without_functional_requirements_section_leaves_cards_ungrouped():
    project, admin, _ = _setup('sc9', fr=False)

    result = sync_technical_requirements_for_project(project, admin)

    assert result['ok'] is True
    assert result['scope_items_created'] == 0
    assert Requirement.objects.filter(phase__project=project, scope_item__isnull=False).count() == 0
    assert Requirement.objects.filter(phase__project=project).count() == 2
