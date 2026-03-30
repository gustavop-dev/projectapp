"""
Tests for the markdown_to_blocks() parser in content/services/markdown_parser.py.

Each test verifies ONE specific parsing behaviour following the AAA pattern.
"""

import pytest

from content.services.markdown_parser import markdown_to_blocks


# -- Headings -----------------------------------------------------------------

def test_parses_h1_heading_correctly():
    blocks = markdown_to_blocks("# Main Title")

    assert len(blocks) == 1
    assert blocks[0] == {"type": "heading", "level": 1, "text": "Main Title"}


def test_parses_h2_heading_correctly():
    blocks = markdown_to_blocks("## Sub Title")

    assert len(blocks) == 1
    assert blocks[0] == {"type": "heading", "level": 2, "text": "Sub Title"}


def test_parses_h3_heading_correctly():
    blocks = markdown_to_blocks("### Minor Title")

    assert len(blocks) == 1
    assert blocks[0] == {"type": "heading", "level": 3, "text": "Minor Title"}


# -- Paragraph ----------------------------------------------------------------

def test_parses_paragraph_text():
    blocks = markdown_to_blocks("This is a simple paragraph.")

    assert len(blocks) == 1
    assert blocks[0] == {"type": "paragraph", "text": "This is a simple paragraph."}


def test_merges_consecutive_paragraph_lines_into_one_block():
    md = "Line one of paragraph.\nLine two of paragraph."

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert blocks[0]["text"] == "Line one of paragraph. Line two of paragraph."


# -- Lists --------------------------------------------------------------------

def test_parses_unordered_list_with_dash_items():
    md = "- Item one\n- Item two\n- Item three"

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "list"
    assert blocks[0]["ordered"] is False
    assert blocks[0]["items"][0]["text"] == "Item one"
    assert blocks[0]["items"][1]["text"] == "Item two"
    assert blocks[0]["items"][2]["text"] == "Item three"
    assert blocks[0]["items"][0]["children"] == []


def test_parses_ordered_list_with_numbered_items():
    md = "1. First\n2. Second\n3. Third"

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "list"
    assert blocks[0]["ordered"] is True
    assert blocks[0]["items"][0]["text"] == "First"
    assert blocks[0]["items"][1]["text"] == "Second"
    assert blocks[0]["items"][2]["text"] == "Third"
    assert blocks[0]["items"][0]["children"] == []


# -- Table ---------------------------------------------------------------------

def test_parses_table_with_headers_and_rows():
    md = (
        "| Name | Age |\n"
        "|------|-----|\n"
        "| Alice | 30 |\n"
        "| Bob | 25 |"
    )

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    assert blocks[0]["headers"] == ["Name", "Age"]
    assert blocks[0]["rows"] == [["Alice", "30"], ["Bob", "25"]]


def test_skips_table_separator_row():
    md = (
        "| Col A | Col B |\n"
        "|-------|-------|\n"
        "| val1  | val2  |"
    )

    blocks = markdown_to_blocks(md)

    assert blocks[0]["type"] == "table"
    # separator row must not appear in rows
    assert len(blocks[0]["rows"]) == 1
    assert blocks[0]["rows"][0] == ["val1", "val2"]


# -- Code blocks ---------------------------------------------------------------

def test_parses_fenced_code_block_with_language():
    md = "```python\nprint('hello')\n```"

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"
    assert blocks[0]["language"] == "python"
    assert blocks[0]["content"] == "print('hello')"


def test_parses_fenced_code_block_without_language_defaults_to_text():
    md = "```\nsome code\n```"

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"
    assert blocks[0]["language"] == "text"


# -- Blockquote ----------------------------------------------------------------

def test_parses_blockquote():
    md = "> This is a quote"

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "blockquote"
    assert blocks[0]["text"] == "This is a quote"


# -- Separator -----------------------------------------------------------------

def test_parses_separator():
    blocks = markdown_to_blocks("---")

    assert len(blocks) == 1
    assert blocks[0] == {"type": "separator"}


# -- Section header / sub-section -----------------------------------------------

def test_parses_section_header_from_numbered_h3():
    blocks = markdown_to_blocks("### 1. Introduction")

    assert len(blocks) == 1
    assert blocks[0]["type"] == "section_header"
    assert blocks[0]["index"] == "01"
    assert blocks[0]["title"] == "Introduction"


def test_parses_sub_section_from_bold_numbered_pattern():
    blocks = markdown_to_blocks("**1.1. Overview**")

    assert len(blocks) == 1
    assert blocks[0]["type"] == "sub_section"
    assert blocks[0]["index"] == "1.1"
    assert blocks[0]["title"] == "Overview"


# -- Edge cases ----------------------------------------------------------------

def test_returns_empty_list_for_empty_input():
    blocks = markdown_to_blocks("")

    assert blocks == []


def test_handles_mixed_content_types_in_sequence():
    md = (
        "# Title\n"
        "\n"
        "A paragraph.\n"
        "\n"
        "- bullet\n"
        "\n"
        "---\n"
    )

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 4
    assert blocks[0]["type"] == "heading"
    assert blocks[1]["type"] == "paragraph"
    assert blocks[2]["type"] == "list"
    assert blocks[3]["type"] == "separator"


def test_preserves_inline_bold_in_paragraph_text():
    md = "This has **bold text** inside."

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert "**bold text**" in blocks[0]["text"]


# -- Callout blocks ------------------------------------------------------------

def test_parses_callout_note_block():
    md = "> [!NOTE]\n> This is an informative note."

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "callout"
    assert blocks[0]["style"] == "note"
    assert blocks[0]["text"] == "This is an informative note."


def test_parses_callout_warning_block():
    md = "> [!WARNING]\n> Be careful here."

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "callout"
    assert blocks[0]["style"] == "warning"


def test_parses_callout_tip_style():
    md = "> [!TIP]\n> Useful tip for the user."

    blocks = markdown_to_blocks(md)

    assert blocks[0]["type"] == "callout"
    assert blocks[0]["style"] == "tip"


def test_blockquote_without_callout_tag_stays_blockquote():
    md = "> This is a regular quote, not a callout."

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "blockquote"
    assert blocks[0]["text"] == "This is a regular quote, not a callout."


# -- Nested lists --------------------------------------------------------------

def test_parses_nested_unordered_list():
    md = "- Item 1\n  - Sub A\n  - Sub B\n- Item 2"

    blocks = markdown_to_blocks(md)

    assert len(blocks) == 1
    assert blocks[0]["type"] == "list"
    assert blocks[0]["ordered"] is False
    assert blocks[0]["items"][0]["text"] == "Item 1"
    assert blocks[0]["items"][0]["children"] == ["Sub A", "Sub B"]


def test_nested_list_item_has_children_key():
    md = "- Top level item"

    blocks = markdown_to_blocks(md)

    assert "children" in blocks[0]["items"][0]


def test_top_level_list_item_without_children_has_empty_children():
    md = "- Solo item with no children"

    blocks = markdown_to_blocks(md)

    assert blocks[0]["items"][0]["children"] == []
