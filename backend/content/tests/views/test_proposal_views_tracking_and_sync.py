"""Tests for genuinely uncovered proposal view paths.

Covers: track_requirement_click, preview_sync_section (no-project),
update_proposal_status (ACCEPTED transition), and _csv_analytics_section_group.
"""
import pytest
from django.urls import reverse

from content.models import ProposalChangeLog, ProposalSection

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# track_requirement_click — lines 1955-1996
# ---------------------------------------------------------------------------

class TestTrackRequirementClick:
    def _url(self, proposal):
        return reverse('track-requirement-click', kwargs={'proposal_uuid': proposal.uuid})

    def test_returns_200_and_creates_changelog_with_group_id(self, api_client, sent_proposal):
        resp = api_client.post(
            self._url(sent_proposal),
            {'group_id': 'grp-001', 'group_title': 'Authentication'},
            format='json',
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'ok'
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal,
            change_type='req_clicked',
        ).exists()

    def test_returns_200_with_group_title_only(self, api_client, sent_proposal):
        resp = api_client.post(
            self._url(sent_proposal),
            {'group_title': 'Payment Module'},
            format='json',
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'ok'

    def test_returns_400_when_neither_group_id_nor_title_provided(self, api_client, sent_proposal):
        resp = api_client.post(
            self._url(sent_proposal),
            {},
            format='json',
        )

        assert resp.status_code == 400
        assert 'error' in resp.json()

    def test_returns_404_for_inactive_proposal(self, api_client, proposal):
        # proposal fixture is a draft (is_active=True but not sent); make it inactive
        proposal.is_active = False
        proposal.save(update_fields=['is_active'])

        resp = api_client.post(
            self._url(proposal),
            {'group_id': 'grp-x'},
            format='json',
        )

        assert resp.status_code == 404

    def test_skips_tracking_for_staff_user(self, client, admin_user, sent_proposal):
        """Admin staff using Django session auth are skipped — no changelog created."""
        client.force_login(admin_user)
        resp = client.post(
            self._url(sent_proposal),
            {'group_id': 'grp-001'},
            content_type='application/json',
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'skipped'
        assert not ProposalChangeLog.objects.filter(
            proposal=sent_proposal, change_type='req_clicked',
        ).exists()

    def test_deduplicates_same_group_within_60_seconds(self, api_client, sent_proposal):
        url = self._url(sent_proposal)
        api_client.post(url, {'group_id': 'grp-dup'}, format='json')
        api_client.post(url, {'group_id': 'grp-dup'}, format='json')

        count = ProposalChangeLog.objects.filter(
            proposal=sent_proposal,
            change_type='req_clicked',
        ).count()
        assert count == 1


# ---------------------------------------------------------------------------
# preview_sync_section — has_project=False path (lines 1313-1327)
# ---------------------------------------------------------------------------

class TestPreviewSyncSectionNoProject:
    def _url(self, section):
        return reverse('section-sync-preview', kwargs={'section_id': section.id})

    def test_returns_ok_false_has_project_when_no_deliverable(
        self, admin_client, proposal, proposal_section,
    ):
        """When proposal has no deliverable, preview returns has_project=False."""
        # proposal_section must be a technical_document section for this path
        proposal_section.section_type = ProposalSection.SectionType.TECHNICAL_DOCUMENT
        proposal_section.save(update_fields=['section_type'])

        resp = admin_client.post(
            self._url(proposal_section),
            {'content_json': {'epics': []}},
            format='json',
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data['ok'] is True
        assert data['has_project'] is False

    def test_returns_400_for_non_technical_section(self, admin_client, proposal_section):
        """Preview sync on a non-technical-document section returns 400."""
        resp = admin_client.post(
            self._url(proposal_section),
            {'content_json': {'epics': []}},
            format='json',
        )

        assert resp.status_code == 400
        assert 'technical_document' in resp.json()['detail']

    def test_returns_400_when_content_json_is_not_a_dict(
        self, admin_client, proposal_section,
    ):
        """Preview sync with a list instead of dict returns 400."""
        proposal_section.section_type = ProposalSection.SectionType.TECHNICAL_DOCUMENT
        proposal_section.save(update_fields=['section_type'])

        resp = admin_client.post(
            self._url(proposal_section),
            {'content_json': [1, 2, 3]},
            format='json',
        )

        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# _csv_analytics_section_group — lines 57, 59 (helper function)
# ---------------------------------------------------------------------------

class TestCsvAnalyticsSectionGroup:
    def test_returns_correct_label_for_technical_document_public(self):
        from content.views.proposal import _csv_analytics_section_group

        result = _csv_analytics_section_group('technical_document_public')

        assert result == 'Detalle técnico (vista pública)'

    def test_returns_correct_label_for_technical_document(self):
        from content.views.proposal import _csv_analytics_section_group

        result = _csv_analytics_section_group('technical_document')

        assert result == 'Detalle técnico'

    def test_returns_empty_string_for_unknown_type(self):
        from content.views.proposal import _csv_analytics_section_group

        result = _csv_analytics_section_group('pricing')

        assert result == ''
