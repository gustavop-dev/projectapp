"""Tests for update_proposal_status (ACCEPTED branch) and _generate_and_save_contract_pdf."""
from unittest.mock import patch

import pytest
from django.urls import reverse

from content.models import ProposalChangeLog, ProposalDocument

pytestmark = pytest.mark.django_db


class TestUpdateProposalStatusAccepted:
    def _url(self, proposal):
        return reverse('update-proposal-status', kwargs={'proposal_id': proposal.id})

    def test_returns_400_for_invalid_status(self, admin_client, proposal):
        resp = admin_client.patch(self._url(proposal), {'status': 'invalid'}, format='json')

        assert resp.status_code == 400
        assert 'Invalid status' in resp.json()['error']

    def test_returns_400_for_disallowed_transition(self, admin_client, proposal):
        # proposal fixture is 'draft' — cannot go to 'accepted' directly
        resp = admin_client.patch(self._url(proposal), {'status': 'accepted'}, format='json')

        assert resp.status_code == 400
        assert 'Cannot transition' in resp.json()['error']

    def test_creates_changelog_on_valid_transition(self, admin_client, sent_proposal):
        # sent → negotiating is an allowed transition
        resp = admin_client.patch(self._url(sent_proposal), {'status': 'negotiating'}, format='json')

        assert resp.status_code == 200
        assert ProposalChangeLog.objects.filter(
            proposal=sent_proposal,
            change_type='status_change',
            new_value='negotiating',
        ).exists()

    def test_accepted_transition_does_not_trigger_platform_onboarding(self, admin_client, negotiating_proposal):
        resp = admin_client.patch(
            self._url(negotiating_proposal), {'status': 'accepted'}, format='json'
        )

        assert resp.status_code == 200
        negotiating_proposal.refresh_from_db()
        assert negotiating_proposal.status == 'accepted'
        assert negotiating_proposal.platform_onboarding_completed_at is None

    def test_non_accepted_transition_does_not_call_platform_onboarding(
        self, admin_client, sent_proposal
    ):
        with patch(
            'accounts.services.proposal_platform_onboarding.handle_proposal_accepted_for_platform'
        ) as mock_accept:
            resp = admin_client.patch(
                self._url(sent_proposal), {'status': 'negotiating'}, format='json'
            )

        assert resp.status_code == 200
        mock_accept.assert_not_called()

    def test_returns_401_for_unauthenticated(self, api_client, sent_proposal):
        resp = api_client.patch(self._url(sent_proposal), {'status': 'negotiating'}, format='json')

        assert resp.status_code == 401


class TestUpdateProposalStatusFinished:
    """Tests for transitioning an accepted proposal to the finished state."""

    def _url(self, proposal):
        return reverse('update-proposal-status', kwargs={'proposal_id': proposal.id})

    def test_finished_transition_from_accepted_succeeds(self, admin_client, accepted_proposal):
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_finished_confirmation'
        ):
            resp = admin_client.patch(
                self._url(accepted_proposal), {'status': 'finished'}, format='json'
            )

        assert resp.status_code == 200
        accepted_proposal.refresh_from_db()
        assert accepted_proposal.status == 'finished'

    def test_finished_transition_creates_changelog(self, admin_client, accepted_proposal):
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_finished_confirmation'
        ):
            admin_client.patch(
                self._url(accepted_proposal), {'status': 'finished'}, format='json'
            )

        assert ProposalChangeLog.objects.filter(
            proposal=accepted_proposal,
            change_type='status_change',
            old_value='accepted',
            new_value='finished',
        ).exists()

    def test_finished_transition_triggers_finished_email(self, admin_client, accepted_proposal):
        with patch(
            'content.services.proposal_email_service.ProposalEmailService.send_finished_confirmation'
        ) as mock_send:
            admin_client.patch(
                self._url(accepted_proposal), {'status': 'finished'}, format='json'
            )

        mock_send.assert_called_once()
        called_with = mock_send.call_args[0][0]
        assert called_with.id == accepted_proposal.id

    def test_finished_transition_from_sent_returns_400(self, admin_client, sent_proposal):
        resp = admin_client.patch(
            self._url(sent_proposal), {'status': 'finished'}, format='json'
        )

        assert resp.status_code == 400
        assert 'Cannot transition' in resp.json()['error']

    def test_finished_transition_from_negotiating_returns_400(self, admin_client, negotiating_proposal):
        resp = admin_client.patch(
            self._url(negotiating_proposal), {'status': 'finished'}, format='json'
        )

        assert resp.status_code == 400
        assert 'Cannot transition' in resp.json()['error']


class TestLaunchToPlatform:
    """Tests for the launch_to_platform view.

    The view queues a Huey task (run_platform_onboarding) for the heavy
    lifting.  We mock the task itself so we only test view logic here:
    validation, teardown, status flags, and changelog creation.
    """

    def _url(self, proposal):
        return reverse('launch-to-platform', kwargs={'proposal_id': proposal.id})

    def test_launch_to_platform_first_time(self, admin_client, accepted_proposal):
        with patch('content.tasks.run_platform_onboarding') as mock_task:
            resp = admin_client.post(self._url(accepted_proposal), format='json')

        assert resp.status_code == 200
        assert resp.json()['platform_onboarding_status'] == 'pending'
        mock_task.assert_called_once_with(
            accepted_proposal.id,
            acting_user_id=resp.wsgi_request.user.id,
            is_relaunch=False,
        )

    def test_launch_to_platform_not_accepted_returns_400(self, admin_client, sent_proposal):
        resp = admin_client.post(self._url(sent_proposal), format='json')

        assert resp.status_code == 400
        assert 'aceptada' in resp.json()['error']

    def test_launch_to_platform_already_onboarded_no_force_returns_409(self, admin_client, accepted_proposal):
        accepted_proposal.platform_onboarding_completed_at = '2026-04-01T10:00:00Z'
        accepted_proposal.save(update_fields=['platform_onboarding_completed_at'])

        resp = admin_client.post(self._url(accepted_proposal), format='json')

        assert resp.status_code == 409
        assert resp.json()['warning'] == 'already_onboarded'

    def test_launch_to_platform_already_onboarded_with_force_calls_teardown(
        self, admin_client, accepted_proposal
    ):
        accepted_proposal.platform_onboarding_completed_at = '2026-04-01T10:00:00Z'
        accepted_proposal.save(update_fields=['platform_onboarding_completed_at'])

        with patch(
            'accounts.services.proposal_platform_onboarding.teardown_platform_for_proposal'
        ) as mock_teardown, patch(
            'content.tasks.run_platform_onboarding'
        ) as mock_task:
            resp = admin_client.post(
                self._url(accepted_proposal), {'force': True}, format='json'
            )

        assert resp.status_code == 200
        mock_teardown.assert_called_once()
        mock_task.assert_called_once()
        _, kwargs = mock_task.call_args
        assert kwargs['is_relaunch'] is True

    def test_launch_to_platform_creates_changelog(self, admin_client, accepted_proposal):
        with patch('content.tasks.run_platform_onboarding'):
            admin_client.post(self._url(accepted_proposal), format='json')

        assert ProposalChangeLog.objects.filter(
            proposal=accepted_proposal,
            change_type='platform_launch',
        ).exists()

    def test_launch_to_platform_requires_admin(self, api_client, accepted_proposal):
        resp = api_client.post(self._url(accepted_proposal), format='json')

        assert resp.status_code == 401


class TestRunPlatformOnboardingTask:
    """Tests for the run_platform_onboarding Huey task logic."""

    def test_task_sets_completed_on_success(self, accepted_proposal):
        accepted_proposal.platform_onboarding_status = 'pending'
        accepted_proposal.save(update_fields=['platform_onboarding_status'])

        with patch(
            'accounts.services.proposal_platform_onboarding.handle_proposal_accepted_for_platform'
        ) as mock_onboard:
            mock_onboard.return_value = {'skipped': False, 'deliverable_id': None, 'sync': {}}
            from content.tasks import run_platform_onboarding
            run_platform_onboarding.call_local(accepted_proposal.id, is_relaunch=False)

        accepted_proposal.refresh_from_db()
        assert accepted_proposal.platform_onboarding_status == 'completed'
        mock_onboard.assert_called_once()
        _, kwargs = mock_onboard.call_args
        assert kwargs['send_email'] is True

    def test_task_sets_failed_on_exception(self, accepted_proposal):
        accepted_proposal.platform_onboarding_status = 'pending'
        accepted_proposal.save(update_fields=['platform_onboarding_status'])

        with patch(
            'accounts.services.proposal_platform_onboarding.handle_proposal_accepted_for_platform'
        ) as mock_onboard:
            mock_onboard.side_effect = RuntimeError('sync failed')
            from content.tasks import run_platform_onboarding
            run_platform_onboarding.call_local(accepted_proposal.id, is_relaunch=False)

        accepted_proposal.refresh_from_db()
        assert accepted_proposal.platform_onboarding_status == 'failed'

    def test_task_skips_email_on_relaunch(self, accepted_proposal):
        accepted_proposal.platform_onboarding_status = 'pending'
        accepted_proposal.save(update_fields=['platform_onboarding_status'])

        with patch(
            'accounts.services.proposal_platform_onboarding.handle_proposal_accepted_for_platform'
        ) as mock_onboard:
            mock_onboard.return_value = {'skipped': False, 'deliverable_id': None, 'sync': {}}
            from content.tasks import run_platform_onboarding
            run_platform_onboarding.call_local(accepted_proposal.id, is_relaunch=True)

        _, kwargs = mock_onboard.call_args
        assert kwargs['send_email'] is False


class TestGenerateAndSaveContractPdf:
    def test_saves_contract_document_when_pdf_generated(self, proposal):
        with patch('content.services.contract_pdf_service.generate_contract_pdf') as mock_gen:
            mock_gen.return_value = b'%PDF-1.4 fake pdf content'
            from content.views.proposal import _generate_and_save_contract_pdf
            _generate_and_save_contract_pdf(proposal)

        assert ProposalDocument.objects.filter(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        ).exists()

    def test_returns_early_when_pdf_generation_returns_none(self, proposal):
        with patch('content.services.contract_pdf_service.generate_contract_pdf') as mock_gen:
            mock_gen.return_value = None
            from content.views.proposal import _generate_and_save_contract_pdf
            _generate_and_save_contract_pdf(proposal)

        assert not ProposalDocument.objects.filter(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        ).exists()

    def test_get_or_create_prevents_duplicate_contract_documents(self, proposal):
        with patch('content.services.contract_pdf_service.generate_contract_pdf') as mock_gen:
            mock_gen.return_value = b'%PDF-1.4 fake pdf content'
            from content.views.proposal import _generate_and_save_contract_pdf
            _generate_and_save_contract_pdf(proposal)
            _generate_and_save_contract_pdf(proposal)

        assert ProposalDocument.objects.filter(
            proposal=proposal,
            document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        ).count() == 1
