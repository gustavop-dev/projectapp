"""Forward-progress regression tests for the documents markdown parser.

Lines that match a block prefix but fail that block's strict pattern used
to leave the main loop without consuming anything, hanging the gunicorn
worker (30s timeout -> SIGKILL -> nginx 502) on every create/update that
carried them. Every case below must terminate and keep the line's content.
"""
from content.services.markdown_parser import markdown_to_blocks


class TestBoldNumberedStubs:
    def test_bold_number_alone_becomes_sub_section(self):
        blocks = markdown_to_blocks('**2.1**')
        assert blocks == [{'type': 'sub_section', 'index': '2.1', 'title': ''}]

    def test_bold_number_with_trailing_dot(self):
        blocks = markdown_to_blocks('**2.1.**')
        assert blocks == [{'type': 'sub_section', 'index': '2.1', 'title': ''}]

    def test_bold_number_with_colon_and_text(self):
        blocks = markdown_to_blocks('**2.1:** texto que sigue')
        assert blocks == [{
            'type': 'sub_section', 'index': '2.1', 'title': 'texto que sigue',
        }]

    def test_unterminated_bold_number_falls_back_to_paragraph(self):
        blocks = markdown_to_blocks('**2.1 — CONFIRMADO.** La ventana queda fija.')
        assert len(blocks) == 1
        assert blocks[0]['type'] == 'paragraph'
        assert 'CONFIRMADO' in blocks[0]['text']

    def test_strict_sub_section_still_parses(self):
        blocks = markdown_to_blocks('**2.1 Título de la subsección**')
        assert blocks == [{
            'type': 'sub_section', 'index': '2.1',
            'title': 'Título de la subsección',
        }]


class TestBlockquoteWithoutSpace:
    def test_quote_without_space_is_consumed(self):
        blocks = markdown_to_blocks('>cita sin espacio')
        assert blocks == [{'type': 'blockquote', 'text': 'cita sin espacio'}]

    def test_quote_with_space_unchanged(self):
        blocks = markdown_to_blocks('> cita normal')
        assert blocks == [{'type': 'blockquote', 'text': 'cita normal'}]


class TestHashWithoutSpace:
    def test_hash_without_space_becomes_paragraph(self):
        blocks = markdown_to_blocks('#hashtag')
        assert blocks == [{'type': 'paragraph', 'text': '#hashtag'}]


class TestMixedDocumentTerminates:
    def test_document_with_every_pathological_line_keeps_all_content(self):
        md = (
            '# Informe\n'
            '\n'
            'Párrafo normal.\n'
            '\n'
            '**2.1**\n'
            '\n'
            '**2.2 — CONFIRMADO.** Acuerdo por escrito.\n'
            '\n'
            '>cita pegada\n'
            '\n'
            '**2.3:** con dos puntos\n'
        )
        blocks = markdown_to_blocks(md)
        types = [b['type'] for b in blocks]
        assert types == [
            'heading', 'paragraph', 'sub_section', 'paragraph',
            'blockquote', 'sub_section',
        ]
        assert blocks[3]['text'].startswith('**2.2 — CONFIRMADO.**')
        assert blocks[5]['title'] == 'con dos puntos'
