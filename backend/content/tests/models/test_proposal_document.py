"""Tests for the ProposalDocument model."""
import pytest

from content.models import ProposalDocument

pytestmark = pytest.mark.django_db


class TestProposalDocumentCreation:
    def test_str_includes_type_and_title(self, proposal_document):
        result = str(proposal_document)
        assert result  # should not be empty

    def test_default_document_type_is_other(self, negotiating_proposal):
        doc = ProposalDocument.objects.create(
            proposal=negotiating_proposal, title='Untitled',
        )
        assert doc.document_type == 'other'

    def test_ordering_by_created_at_descending(self, negotiating_proposal):
        doc1 = ProposalDocument.objects.create(
            proposal=negotiating_proposal, title='First',
        )
        doc2 = ProposalDocument.objects.create(
            proposal=negotiating_proposal, title='Second',
        )
        docs = list(negotiating_proposal.proposal_documents.all())
        assert docs[0].pk == doc2.pk
        assert docs[1].pk == doc1.pk


class TestProposalDocumentCascadeDelete:
    def test_documents_deleted_when_proposal_is_deleted(self, negotiating_proposal):
        """ProposalDocument rows are removed when the parent proposal is deleted."""
        doc = ProposalDocument.objects.create(
            proposal=negotiating_proposal,
            document_type=ProposalDocument.DOC_TYPE_LEGAL_ANNEX,
            title='To be deleted',
        )
        doc_pk = doc.pk

        negotiating_proposal.delete()

        assert not ProposalDocument.objects.filter(pk=doc_pk).exists()
