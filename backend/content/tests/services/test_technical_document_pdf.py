"""Tests for technical-only PDF generation."""

from unittest.mock import patch

import pytest

from content.models import ProposalSection
from content.services.technical_document_pdf import generate_technical_document_pdf


@pytest.mark.django_db
def test_generate_invokes_module_filter_with_selected_modules(sent_proposal):
    """Technical PDF applies filter_technical_document_by_module_selection."""
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={'purpose': 'Purpose line for PDF.'},
    )
    with patch(
        'content.services.technical_document_filter.filter_technical_document_by_module_selection',
    ) as mock_filter:
        mock_filter.side_effect = lambda doc, sel: doc
        out = generate_technical_document_pdf(
            sent_proposal, selected_modules=['module-1', 'group-2'],
        )
        mock_filter.assert_called_once()
        assert mock_filter.call_args[0][1] == ['module-1', 'group-2']
        assert out is not None
        assert out[:5] == b'%PDF-'
