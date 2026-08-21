"""Build the public, masked contract preview for business proposals."""

import re

from content.services.contract_pdf_service import (
    render_default_contract_draft_markdown,
)


CLAUSE_HEADING_RE = re.compile(r'^##\s+(?P<title>.+?)\s*$', re.MULTILINE)


def build_contract_terms_payload():
    """Return the current global contract split into linkable clauses.

    ``None`` means no default template is configured. Placeholder substitution
    always uses draft masking and never accepts proposal-specific parameters.
    """
    rendered = render_default_contract_draft_markdown()
    if not rendered:
        return None

    template, markdown = rendered
    matches = list(CLAUSE_HEADING_RE.finditer(markdown))
    first_heading_start = matches[0].start() if matches else len(markdown)
    clauses = []

    for index, match in enumerate(matches, start=1):
        content_start = match.end()
        content_end = matches[index].start() if index < len(matches) else len(markdown)
        clauses.append({
            'id': f'clause-{index:02d}',
            'number': index,
            'title': match.group('title').strip(),
            'content_markdown': markdown[content_start:content_end].strip(),
        })

    return {
        'title': 'Contrato de prestación de servicios',
        'label': 'Borrador informativo',
        'template_updated_at': template.updated_at.isoformat(),
        'preamble_markdown': markdown[:first_heading_start].strip(),
        'clauses': clauses,
    }
