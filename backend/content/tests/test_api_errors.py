"""Tests for content/api_errors.py — the structured error helpers."""
from rest_framework import status as http_status

from content.api_errors import (
    ProposalActionError,
    error_response,
    error_response_from_exc,
)
from content.models import BusinessProposal


class TestErrorResponse:
    def test_message_only(self):
        resp = error_response('Algo salió mal.')
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST
        assert resp.data == {'error': 'Algo salió mal.'}

    def test_includes_code_and_hint_when_given(self):
        resp = error_response('Falta el correo.', code='missing_client_email', hint='Agrégalo.')
        assert resp.data == {
            'error': 'Falta el correo.',
            'code': 'missing_client_email',
            'hint': 'Agrégalo.',
        }

    def test_respects_custom_status(self):
        resp = error_response('No encontrado.', status=http_status.HTTP_404_NOT_FOUND)
        assert resp.status_code == http_status.HTTP_404_NOT_FOUND

    def test_omits_falsy_code_and_hint(self):
        resp = error_response('x', code=None, hint='')
        assert 'code' not in resp.data
        assert 'hint' not in resp.data


class TestProposalActionError:
    def test_is_value_error_subclass(self):
        assert issubclass(ProposalActionError, ValueError)

    def test_carries_code_and_hint(self):
        exc = ProposalActionError('msg', code='c', hint='h')
        assert str(exc) == 'msg'
        assert exc.code == 'c'
        assert exc.hint == 'h'

    def test_defaults_none(self):
        exc = ProposalActionError('msg')
        assert exc.code is None
        assert exc.hint is None


class TestErrorResponseFromExc:
    def test_forwards_code_and_hint_from_proposal_action_error(self):
        exc = ProposalActionError('Falta el correo.', code='missing_client_email', hint='Agrégalo.')
        resp = error_response_from_exc(exc)
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST
        assert resp.data == {
            'error': 'Falta el correo.',
            'code': 'missing_client_email',
            'hint': 'Agrégalo.',
        }

    def test_plain_value_error_has_message_only(self):
        resp = error_response_from_exc(ValueError('boom'))
        assert resp.data == {'error': 'boom'}
        assert 'code' not in resp.data
        assert 'hint' not in resp.data


class TestStatusLabelsEs:
    def test_known_labels(self):
        assert BusinessProposal.status_label_es('draft') == 'Borrador'
        assert BusinessProposal.status_label_es('sent') == 'Enviada'
        assert BusinessProposal.status_label_es('accepted') == 'Aceptada'
        assert BusinessProposal.status_label_es('finished') == 'Finalizada'

    def test_every_status_choice_has_a_spanish_label(self):
        for value, _label in BusinessProposal.Status.choices:
            assert value in BusinessProposal.STATUS_LABELS_ES

    def test_unknown_value_falls_back_to_raw(self):
        assert BusinessProposal.status_label_es('nope') == 'nope'
