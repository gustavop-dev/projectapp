"""Markdown export of the same curated blocks used by the formal PDFs."""
from content.services.formalization_content import formal_document_blocks, formal_document_title
from content.services.markdown_export import MarkdownBuffer, export_payload, formal_text, table


def generate_formal_markdown(content, kind, issued_at, reference):
    title = formal_document_title(content, kind)
    output = MarkdownBuffer()
    output.append('# ' + title)
    output.append(formal_text(content.proposal.title))
    output.append(formal_text(content.proposal.client_name))
    output.append(content.label('Referencia: ', 'Reference: ') + formal_text(reference))
    output.append(content.label('Emisión: ', 'Issued: ') + issued_at.strftime('%Y-%m-%d %H:%M UTC'))
    for number, block in enumerate(formal_document_blocks(content, kind), 1):
        output.append(f'## {number:02d}. {formal_text(block["title"])}')
        for paragraph in block['paragraphs']:
            output.append(formal_text(paragraph))
        if block['rows']:
            output.append(table(
                [formal_text(value) for value in block['headers']],
                [[formal_text(value) for value in row] for row in block['rows']],
            ))
    return export_payload(title, output.render())
