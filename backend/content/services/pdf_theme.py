"""Visual themes for the shared ReportLab drawers.

PROFESSIONAL_THEME reproduces the historical brand constants so every
existing PDF (proposals, contracts, …) is unchanged. FRIENDLY_THEME
mirrors the on-screen markdown preview (DocumentMarkdownBody.vue).
"""
from dataclasses import dataclass

from reportlab.lib.colors import Color, HexColor

from content.services.pdf_utils import (
    ESMERALD, ESMERALD_80, ESMERALD_DARK, ESMERALD_LIGHT, GREEN_LIGHT,
    LEMON, BONE, GRAY_200, GRAY_300, GRAY_500, WHITE,
)


@dataclass(frozen=True)
class PdfTheme:
    name: str
    # Headings
    h1_color: Color
    h2_color: Color
    h3_color: Color
    heading_rule_color: Color   # accent rule under h1/h2
    heading_rule_full: bool     # True → full-width thin underline (friendly)
    # Body / links
    body_color: Color
    link_color: Color
    # Section header (numbered)
    section_index_color: Color
    section_title_color: Color
    section_rule_color: Color
    # Page chrome
    header_bar_color: Color
    header_dot_color: Color
    # Blockquote
    quote_bg: Color
    quote_accent: Color
    quote_text: Color
    # Table
    table_header_bg: Color
    table_header_text: Color
    table_stripe_bg: Color
    table_row_bg: Color
    table_body_text: Color
    table_border_color: Color
    # Code
    code_bg: Color
    code_border: Color
    code_text: Color
    # Separator
    rule_color: Color
    # Title page
    title_color: Color


PROFESSIONAL_THEME = PdfTheme(
    name='professional',
    h1_color=ESMERALD, h2_color=ESMERALD, h3_color=ESMERALD,
    heading_rule_color=LEMON, heading_rule_full=False,
    body_color=ESMERALD_80, link_color=HexColor('#059669'),
    section_index_color=GREEN_LIGHT, section_title_color=ESMERALD,
    section_rule_color=LEMON,
    header_bar_color=ESMERALD, header_dot_color=LEMON,
    quote_bg=BONE, quote_accent=LEMON, quote_text=ESMERALD,
    table_header_bg=ESMERALD, table_header_text=WHITE,
    table_stripe_bg=ESMERALD_LIGHT, table_row_bg=WHITE,
    table_body_text=ESMERALD_80, table_border_color=GRAY_300,
    code_bg=GRAY_200, code_border=GRAY_300, code_text=ESMERALD_80,
    rule_color=GRAY_300, title_color=ESMERALD,
)

FRIENDLY_THEME = PdfTheme(
    name='friendly',
    h1_color=HexColor('#047857'), h2_color=HexColor('#047857'),
    h3_color=HexColor('#059669'),
    heading_rule_color=HexColor('#D1D5DB'), heading_rule_full=True,
    body_color=HexColor('#374151'), link_color=HexColor('#059669'),
    section_index_color=HexColor('#059669'),
    section_title_color=HexColor('#047857'),
    section_rule_color=HexColor('#10B981'),
    header_bar_color=HexColor('#047857'), header_dot_color=HexColor('#10B981'),
    quote_bg=HexColor('#F0FDF4'), quote_accent=HexColor('#10B981'),
    quote_text=HexColor('#4B5563'),
    table_header_bg=HexColor('#F9FAFB'), table_header_text=HexColor('#374151'),
    table_stripe_bg=HexColor('#F9FAFB'), table_row_bg=WHITE,
    table_body_text=HexColor('#4B5563'), table_border_color=HexColor('#E5E7EB'),
    code_bg=HexColor('#F3F4F6'), code_border=HexColor('#E5E7EB'),
    code_text=HexColor('#1F2937'),
    rule_color=HexColor('#D1D5DB'), title_color=HexColor('#047857'),
)


def get_theme(name):
    """Return the theme for *name*; unknown/empty → professional."""
    return FRIENDLY_THEME if name == 'friendly' else PROFESSIONAL_THEME
