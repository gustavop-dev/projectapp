"""Tests for ProjectScopeItem sync + requirement linking + admin-override guard.

Covers the `functional_requirements` → `ProjectScopeItem` mirror and the
`Requirement.scope_item` / `content_overridden` behavior added to
``accounts/services/technical_requirements_sync.py``. These paths had no active
coverage: the descriptive scope-item mirror, the primary-scope-item linking via
``linked_item_ids``, the admin-override guard that preserves manually-edited
requirement fields, and client-owned Kanban state preservation on re-sync.
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
    UserProfile,
)
from accounts.services.technical_requirements_sync import (
    sync_technical_requirements_for_project,
)
from content.models import BusinessProposal, ProposalSection

pytestmark = pytest.mark.django_db

User = get_user_model()


def _make_fr_sync_setup(prefix, *, groups=None, additional=None, epics=None):
    """Project + accepted proposal with functional_requirements + technical_document sections.

    Returns (project, admin, functional_section, technical_section) so tests can
    mutate the proposal content in place and re-sync.
    """
    admin = User.objects.create_user(
        username=f'{prefix}adm@fr.com', email=f'{prefix}adm@fr.com', password='p',
    )
    UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    client = User.objects.create_user(
        username=f'{prefix}cli@fr.com', email=f'{prefix}cli@fr.com', password='p',
    )
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

    functional = ProposalSection.objects.create(
        proposal=bp, section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
        title='Funcional', order=1,
        content_json={'groups': groups or [], 'additionalModules': additional or []},
    )
    technical = ProposalSection.objects.create(
        proposal=bp, section_type=ProposalSection.SectionType.TECHNICAL_DOCUMENT,
        title='Técnico', order=2, content_json={'epics': epics or []},
    )
    return project, admin, functional, technical


# ---------------------------------------------------------------------------
# Scope-item mirror
# ---------------------------------------------------------------------------

def test_sync_creates_scope_item_from_functional_requirement_group():
    groups = [{'id': 'views', 'title': 'Vistas', 'icon': '🖥️', 'items': [
        {'id': 'item-views-home', 'name': 'Home', 'description': 'Landing'},
    ]}]
    project, admin, _, _ = _make_fr_sync_setup('sc1', groups=groups)

    result = sync_technical_requirements_for_project(project, admin)

    assert result['scope_items_created'] == 1
    si = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-views-home')
    assert si.origin == ProjectScopeItem.ORIGIN_GROUP
    assert si.group_id == 'views'
    assert si.name == 'Home'


def test_sync_marks_additional_module_scope_item_with_additional_origin():
    additional = [{'id': 'extra', 'title': 'Extras', 'items': [
        {'id': 'item-extra-chat', 'name': 'Chat'},
    ]}]
    project, admin, _, _ = _make_fr_sync_setup('sc2', additional=additional)

    sync_technical_requirements_for_project(project, admin)

    si = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-extra-chat')
    assert si.origin == ProjectScopeItem.ORIGIN_ADDITIONAL


def test_sync_mirrors_hidden_group_with_group_is_visible_false():
    groups = [{'id': 'secret', 'title': 'Oculto', 'is_visible': False, 'items': [
        {'id': 'item-secret-x', 'name': 'X'},
    ]}]
    project, admin, _, _ = _make_fr_sync_setup('sc3', groups=groups)

    sync_technical_requirements_for_project(project, admin)

    si = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-secret-x')
    assert si.group_is_visible is False


def test_resync_updates_scope_item_when_name_changes():
    groups = [{'id': 'g', 'title': 'G', 'items': [{'id': 'item-g-a', 'name': 'Original'}]}]
    project, admin, functional, _ = _make_fr_sync_setup('sc4', groups=groups)
    sync_technical_requirements_for_project(project, admin)

    functional.content_json['groups'][0]['items'][0]['name'] = 'Renamed'
    functional.save(update_fields=['content_json'])
    result = sync_technical_requirements_for_project(project, admin)

    assert result['scope_items_updated'] == 1
    si = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-g-a')
    assert si.name == 'Renamed'


def test_resync_archives_scope_item_removed_from_proposal():
    groups = [{'id': 'g', 'title': 'G', 'items': [
        {'id': 'item-g-keep', 'name': 'Keep'},
        {'id': 'item-g-drop', 'name': 'Drop'},
    ]}]
    project, admin, functional, _ = _make_fr_sync_setup('sc5', groups=groups)
    sync_technical_requirements_for_project(project, admin)

    functional.content_json['groups'][0]['items'] = [{'id': 'item-g-keep', 'name': 'Keep'}]
    functional.save(update_fields=['content_json'])
    result = sync_technical_requirements_for_project(project, admin)

    assert result['scope_items_archived'] == 1
    dropped = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-g-drop')
    assert dropped.is_archived is True


def test_resync_unarchives_scope_item_when_readded():
    groups = [{'id': 'g', 'title': 'G', 'items': [
        {'id': 'item-g-keep', 'name': 'Keep'},
        {'id': 'item-g-back', 'name': 'Back'},
    ]}]
    project, admin, functional, _ = _make_fr_sync_setup('sc6', groups=groups)
    sync_technical_requirements_for_project(project, admin)

    functional.content_json['groups'][0]['items'] = [{'id': 'item-g-keep', 'name': 'Keep'}]
    functional.save(update_fields=['content_json'])
    sync_technical_requirements_for_project(project, admin)

    functional.content_json['groups'][0]['items'] = [
        {'id': 'item-g-keep', 'name': 'Keep'},
        {'id': 'item-g-back', 'name': 'Back'},
    ]
    functional.save(update_fields=['content_json'])
    result = sync_technical_requirements_for_project(project, admin)

    assert result['scope_items_unarchived'] == 1
    back = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-g-back')
    assert back.is_archived is False


# ---------------------------------------------------------------------------
# Requirement → scope-item linking
# ---------------------------------------------------------------------------

def test_sync_links_requirement_to_primary_scope_item():
    groups = [{'id': 'views', 'title': 'V', 'items': [{'id': 'item-views-home', 'name': 'Home'}]}]
    epics = [{'epicKey': 'epic-a', 'title': 'A', 'requirements': [
        {'flowKey': 'flow-1', 'title': 'Req', 'linked_item_ids': ['item-views-home']},
    ]}]
    project, admin, _, _ = _make_fr_sync_setup('sc7', groups=groups, epics=epics)

    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='flow-1')
    si = ProjectScopeItem.objects.get(phase__project=project, source_item_id='item-views-home')
    assert req.scope_item_id == si.id


def test_sync_leaves_requirement_scope_item_null_when_no_link_resolves():
    groups = [{'id': 'views', 'title': 'V', 'items': [{'id': 'item-views-home', 'name': 'Home'}]}]
    epics = [{'epicKey': 'epic-a', 'title': 'A', 'requirements': [
        {'flowKey': 'flow-2', 'title': 'Unlinked', 'linked_item_ids': ['item-does-not-exist']},
    ]}]
    project, admin, _, _ = _make_fr_sync_setup('sc8', groups=groups, epics=epics)

    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='flow-2')
    assert req.scope_item_id is None


# ---------------------------------------------------------------------------
# Admin-override guard + client-owned Kanban state
# ---------------------------------------------------------------------------

def test_resync_preserves_overridden_requirement_title():
    epics = [{'epicKey': 'epic-a', 'title': 'A', 'requirements': [
        {'flowKey': 'flow-1', 'title': 'Original'},
    ]}]
    project, admin, _, technical = _make_fr_sync_setup('sc9', epics=epics)
    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='flow-1')
    req.title = 'Admin edited'
    req.content_overridden = True
    req.save(update_fields=['title', 'content_overridden'])

    technical.content_json['epics'][0]['requirements'][0]['title'] = 'Proposal changed'
    technical.save(update_fields=['content_json'])
    sync_technical_requirements_for_project(project, admin)

    req.refresh_from_db()
    assert req.title == 'Admin edited'


def test_resync_overwrites_non_overridden_requirement_title():
    epics = [{'epicKey': 'epic-a', 'title': 'A', 'requirements': [
        {'flowKey': 'flow-1', 'title': 'Original'},
    ]}]
    project, admin, _, technical = _make_fr_sync_setup('sc10', epics=epics)
    sync_technical_requirements_for_project(project, admin)

    technical.content_json['epics'][0]['requirements'][0]['title'] = 'Proposal changed'
    technical.save(update_fields=['content_json'])
    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='flow-1')
    assert req.title == 'Proposal changed'


def test_resync_preserves_client_owned_kanban_status_and_order():
    epics = [{'epicKey': 'epic-a', 'title': 'A', 'requirements': [
        {'flowKey': 'flow-1', 'title': 'Req'},
    ]}]
    project, admin, _, technical = _make_fr_sync_setup('sc11', epics=epics)
    sync_technical_requirements_for_project(project, admin)

    req = Requirement.objects.get(phase__project=project, source_flow_key='flow-1')
    req.status = Requirement.STATUS_IN_PROGRESS
    req.order = 99
    req.save(update_fields=['status', 'order'])

    technical.content_json['epics'][0]['requirements'][0]['description'] = 'new details'
    technical.save(update_fields=['content_json'])
    sync_technical_requirements_for_project(project, admin)

    req.refresh_from_db()
    assert req.status == Requirement.STATUS_IN_PROGRESS
    assert req.order == 99


def test_resync_reuses_single_phase_per_project_and_proposal():
    epics = [{'epicKey': 'epic-a', 'title': 'A', 'requirements': []}]
    project, admin, _, _ = _make_fr_sync_setup('sc12', epics=epics)

    sync_technical_requirements_for_project(project, admin)
    sync_technical_requirements_for_project(project, admin)

    assert ProjectPhase.objects.filter(project=project).count() == 1
