"""Tests for the Proposals MCP connector HTTP endpoint."""
import pytest

from content.models import BusinessProposal, McpConnector


@pytest.fixture
def proposals_connector(db):
    connector, _ = McpConnector.objects.get_or_create(
        slug='proposals', defaults={'name': 'Gestor de Propuestas'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    return connector, connector.generate_token()


def _url(token):
    return f'/api/mcp/proposals/{token}/'


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


def _call(api_client, token, name, arguments):
    return api_client.post(
        _url(token), _rpc('tools/call', {'name': name, 'arguments': arguments}),
        format='json',
    )


@pytest.mark.django_db
class TestProposalsMcp:
    def test_tool_list(self, api_client, proposals_connector):
        _, token = proposals_connector
        response = api_client.post(_url(token), _rpc('tools/list'), format='json')
        names = [t['name'] for t in response.data['result']['tools']]
        for expected in (
            'get_proposal_template', 'list_proposals', 'create_proposal',
            'update_proposal', 'update_proposal_status', 'send_proposal',
            'delete_proposal', 'duplicate_proposal', 'create_share_link',
        ):
            assert expected in names

    def test_template_has_required_fields(self, api_client, proposals_connector):
        _, token = proposals_connector
        response = _call(api_client, token, 'get_proposal_template', {'lang': 'es'})
        text = response.data['result']['content'][0]['text']
        assert 'general.clientName' in text

    def test_create_requires_general_client_name(self, api_client, proposals_connector):
        _, token = proposals_connector
        response = _call(api_client, token, 'create_proposal', {
            'title': 'Propuesta X', 'client_name': 'ACME', 'sections': {},
        })
        # sections without a general.clientName is rejected by the serializer.
        assert response.data['result']['isError'] is True

    def test_create_and_list_and_get(self, api_client, proposals_connector):
        _, token = proposals_connector
        created = _call(api_client, token, 'create_proposal', {
            'title': 'Propuesta Kore',
            'client_name': 'Kore SAS',
            'client_email': 'kore@x.com',
            'sections': {'general': {'clientName': 'Kore SAS'}},
        })
        assert created.data['result']['isError'] is False
        proposal = BusinessProposal.objects.get(title='Propuesta Kore')
        # Sections were seeded from defaults.
        assert proposal.sections.exists()

        listed = _call(api_client, token, 'list_proposals', {})
        assert 'Propuesta Kore' in listed.data['result']['content'][0]['text']

        got = _call(api_client, token, 'get_proposal', {'proposal_id': proposal.id})
        assert got.data['result']['isError'] is False

    def test_duplicate_resets_to_draft(self, api_client, proposals_connector):
        original = BusinessProposal.objects.create(
            title='Base', client_name='C', status=BusinessProposal.Status.SENT,
        )
        _, token = proposals_connector
        response = _call(api_client, token, 'duplicate_proposal', {'proposal_id': original.id})
        assert response.data['result']['isError'] is False
        copy_obj = BusinessProposal.objects.get(title='Base (copia)')
        assert copy_obj.status == BusinessProposal.Status.DRAFT

    def test_invalid_status_transition_errors(self, api_client, proposals_connector):
        proposal = BusinessProposal.objects.create(
            title='T', client_name='C', status=BusinessProposal.Status.DRAFT,
        )
        _, token = proposals_connector
        # draft → accepted is not allowed.
        response = _call(api_client, token, 'update_proposal_status', {
            'proposal_id': proposal.id, 'status': 'accepted',
        })
        assert response.data['result']['isError'] is True

    def test_delete_proposal(self, api_client, proposals_connector):
        proposal = BusinessProposal.objects.create(title='Borrable', client_name='C')
        _, token = proposals_connector
        response = _call(api_client, token, 'delete_proposal', {'proposal_id': proposal.id})
        assert response.data['result']['isError'] is False
        assert not BusinessProposal.objects.filter(pk=proposal.id).exists()
