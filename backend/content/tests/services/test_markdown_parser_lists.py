"""Nested-list parsing for the documents markdown parser."""
from content.services.markdown_parser import markdown_to_blocks


def _only_list(md):
    blocks = markdown_to_blocks(md)
    assert len(blocks) == 1 and blocks[0]['type'] == 'list'
    return blocks[0]


class TestNestedLists:
    def test_three_level_unordered_nesting(self):
        md = ('- nivel uno\n'
              '  - nivel dos\n'
              '    - nivel tres\n'
              '- otro nivel uno\n')
        block = _only_list(md)
        assert block['ordered'] is False
        assert [i['text'] for i in block['items']] == ['nivel uno',
                                                       'otro nivel uno']
        lvl2 = block['items'][0]['children']
        assert lvl2[0]['text'] == 'nivel dos'
        assert lvl2[0]['children'][0]['text'] == 'nivel tres'

    def test_ordered_list_with_unordered_children(self):
        md = ('1. primero\n'
              '   - detalle a\n'
              '   - detalle b\n'
              '2. segundo\n')
        block = _only_list(md)
        assert block['ordered'] is True
        assert [c['text'] for c in block['items'][0]['children']] == [
            'detalle a', 'detalle b']

    def test_continuation_line_appends_to_item_text(self):
        md = ('- item con texto\n'
              '  que continua abajo\n')
        block = _only_list(md)
        assert block['items'][0]['text'] == 'item con texto que continua abajo'

    def test_flat_list_unchanged_shape(self):
        block = _only_list('- a\n- b\n')
        assert [i['text'] for i in block['items']] == ['a', 'b']
        assert block['items'][0]['children'] == []
