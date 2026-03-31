import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import Deliverable, Project, Requirement, UserProfile
from accounts.services.technical_requirements_sync import sync_technical_requirements_for_project
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
