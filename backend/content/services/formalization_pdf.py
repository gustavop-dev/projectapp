"""Sober, paginated formal annexes; independent of the public sales PDF."""
from html import escape, unescape
from io import BytesIO

from django.utils.html import strip_tags
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

from content.services.formalization_content import formal_document_blocks, formal_document_title
from content.services.pdf_utils import _font, _register_fonts, _strip_emoji


class AnnexDocument(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'AnnexHeading':
            key = f'section-{self.seq.nextf("heading")}'
            self.canv.bookmarkPage(key)
            self.notify('TOCEntry', (0, flowable.getPlainText(), self.page, key))


def generate_formal_pdf(content, kind, issued_at, reference):
    blocks = formal_document_blocks(content, kind)
    _register_fonts()
    title = formal_document_title(content, kind)
    normal = ParagraphStyle('AnnexBody', fontName=_font('regular'), fontSize=9, leading=13, spaceAfter=8, splitLongWords=True)
    heading = ParagraphStyle('AnnexHeading', parent=normal, fontName=_font('bold'), fontSize=14, leading=19, spaceBefore=18, spaceAfter=10, keepWithNext=True)
    cover = ParagraphStyle('AnnexCover', parent=heading, fontSize=24, leading=30)
    cover_label = ParagraphStyle('AnnexCoverLabel', parent=heading)
    small = ParagraphStyle('AnnexSmall', parent=normal, fontSize=8, leading=11)

    def paragraph(value, style=normal):
        plain = _strip_emoji(unescape(strip_tags(str(value or ''))))
        return Paragraph(escape(plain).replace('\n', '<br/>'), style)

    stream = BytesIO()
    doc = AnnexDocument(stream, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=50, bottomMargin=48, title=title, author='Project App')
    story = [Spacer(1, 55), paragraph('Project App', cover_label), paragraph(title, cover), Spacer(1, 25), paragraph(content.proposal.title, cover_label), paragraph(content.proposal.client_name), paragraph(content.label('Referencia: ', 'Reference: ') + reference), paragraph(content.label('Emisión: ', 'Issued: ') + issued_at.strftime('%Y-%m-%d %H:%M UTC')), PageBreak()]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('AnnexTOC', parent=normal, spaceBefore=8)]
    story.extend([paragraph(content.label('Índice', 'Contents'), cover), toc, PageBreak()])
    for number, block in enumerate(blocks, 1):
        story.append(paragraph(f'{number:02d}. {block["title"]}', heading))
        story.extend(paragraph(value) for value in block['paragraphs'])
        if not block['rows']:
            continue
        # Wide requirements become readable labeled records instead of tiny columns.
        if len(block['headers']) > 4:
            for row in block['rows']:
                for label, value in zip(block['headers'], row):
                    if value:
                        story.append(paragraph(f'{label}: {value}'))
                story.append(Spacer(1, 8))
        else:
            cells = [[paragraph(value, small) for value in block['headers']]]
            cells += [[paragraph(value, small) for value in row] for row in block['rows']]
            table = LongTable(cells, colWidths=[doc.width / len(block['headers'])] * len(block['headers']), repeatRows=1, splitInRow=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6efef')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#d9e1df')),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            story.append(table)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(_font('regular'), 7)
        canvas.drawString(42, 28, reference)
        canvas.drawRightString(A4[0] - 42, 28, str(document.page))
        canvas.restoreState()

    doc.multiBuild(story, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()
