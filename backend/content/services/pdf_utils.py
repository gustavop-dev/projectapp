"""
Shared PDF drawing utilities for ReportLab-based document generation.

Provides brand colours, font registration, page layout constants,
text processing helpers, and reusable drawing functions used by
proposal_pdf_service and other PDF generators.
"""

import logging
import re
import textwrap
from pathlib import Path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# ── Register Ubuntu fonts ────────────────────────────────────
_FONTS_DIR = (
    Path(settings.BASE_DIR).parent / 'frontend' / 'assets' / 'fonts'
)
_FONT_MAP = {
    'Ubuntu': 'Ubuntu-Regular.ttf',
    'Ubuntu-Bold': 'Ubuntu-Bold.ttf',
    'Ubuntu-Light': 'Ubuntu-Light.ttf',
    'Ubuntu-Medium': 'Ubuntu-Medium.ttf',
    'Ubuntu-Italic': 'Ubuntu-Italic.ttf',
    'Ubuntu-BoldItalic': 'Ubuntu-BoldItalic.ttf',
    'Ubuntu-LightItalic': 'Ubuntu-LightItalic.ttf',
    'Ubuntu-MediumItalic': 'Ubuntu-MediumItalic.ttf',
}
_fonts_registered = False


def _register_fonts():
    """Register Ubuntu TTF fonts once (falls back to Helvetica if missing)."""
    global _fonts_registered
    if _fonts_registered:
        return
    for name, filename in _FONT_MAP.items():
        path = _FONTS_DIR / filename
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            except Exception:
                logger.debug('Could not register font %s', name)
    _fonts_registered = True


# Font helpers – fall back to Helvetica if Ubuntu is not available
def _font(style='regular'):
    """Return the best available font name for *style*."""
    mapping = {
        'regular': ('Ubuntu', 'Helvetica'),
        'bold': ('Ubuntu-Bold', 'Helvetica-Bold'),
        'light': ('Ubuntu-Light', 'Helvetica'),
        'medium': ('Ubuntu-Medium', 'Helvetica'),
        'italic': ('Ubuntu-Italic', 'Helvetica-Oblique'),
        'bolditalic': ('Ubuntu-BoldItalic', 'Helvetica-BoldOblique'),
        'lightitalic': ('Ubuntu-LightItalic', 'Helvetica-Oblique'),
    }
    primary, fallback = mapping.get(style, ('Ubuntu', 'Helvetica'))
    try:
        pdfmetrics.getFont(primary)
        return primary
    except KeyError:
        return fallback


# ── Brand colours (match frontend tailwind.config.js) ────────
ESMERALD = colors.HexColor('#002921')
ESMERALD_DARK = colors.HexColor('#001713')
ESMERALD_LIGHT = colors.HexColor('#E6EFEF')
GREEN_LIGHT = colors.HexColor('#809490')
LEMON = colors.HexColor('#F0FF3D')
BONE = colors.HexColor('#FAF3E0')
WINDOW_BLACK = colors.HexColor('#191919')
GRAY_700 = colors.HexColor('#374151')
GRAY_500 = colors.HexColor('#6B7280')
GRAY_300 = colors.HexColor('#D1D5DB')
GRAY_200 = colors.HexColor('#E5E7EB')
WHITE = colors.white

# Derived colours
ESMERALD_80 = colors.HexColor('#335550')  # esmerald at ~80% mixed with white

# ── Cover / back-cover PDF paths ─────────────────────────────
COVER_PDF = Path(settings.BASE_DIR) / 'static' / 'front_page' / 'Portada_Propuesta_ProjectApp.pdf'
BACK_COVER_PDF = (
    Path(settings.BASE_DIR) / 'static' / 'front_page' / 'Contraportada_ProjectApp.pdf'
)

# ── Page dimensions (portrait A4) ────────────────────────────
PAGE_W, PAGE_H = A4  # ≈595 × 842 pt
MARGIN_L = 48
MARGIN_R = 48
MARGIN_T = 56
MARGIN_B = 48
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R
TEXT_AREA_W = CONTENT_W * 0.60
SIDEBAR_X = MARGIN_L + TEXT_AREA_W + 20
SIDEBAR_W = CONTENT_W - TEXT_AREA_W - 20


# ─────────────────────────────────────────────────────────────
# Emoji / symbol stripping
# ─────────────────────────────────────────────────────────────

_EMOJI_RE = re.compile(
    '['
    '\U0001F000-\U0001FFFF'
    '\U00002600-\U000027BF'
    '\U00002300-\U000023FF'
    '\U0000FE00-\U0000FE0F'
    '\U0000200D'
    '\U000020E3'
    '\U00002B50-\U00002B55'
    '\U000025A0-\U000025FF'
    '\U00002702-\U000027B0'
    '\U0000231A-\U0000231B'
    '\U000023E9-\U000023F3'
    '\U000023F8-\U000023FA'
    '\U0000200B'
    '\U0000FFFD'
    ']+',
)
_BR_TAG_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)
_BOLD_HTML_RE = re.compile(r'<b>(.*?)</b>', re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r'</?[a-zA-Z][^>]*>', re.IGNORECASE)


def _strip_emoji(text):
    """Remove emoji/symbol characters that the fonts cannot render."""
    if not text:
        return text
    text = _BOLD_HTML_RE.sub(r'**\1**', str(text))
    text = _BR_TAG_RE.sub(' ', text)
    text = _HTML_TAG_RE.sub('', text)
    return _EMOJI_RE.sub('', text).strip()


def _format_cop(value):
    """Format a number as Colombian currency: $1.490.000 (dots as thousands)."""
    try:
        num = int(value)
    except (TypeError, ValueError):
        return str(value)
    formatted = f'{num:,}'.replace(',', '.')
    return f'${formatted}'


_URL_RE = re.compile(r'(https?://[^\s),]+)')
_BARE_DOMAIN_RE = re.compile(
    r'(?<![/\w@])'
    r'([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.'
    r'(?:com|co|net|org|io|dev|app|at|de|es|fr|uk|us|me|info|biz|tv|cc)'
    r'(?:/[^\s),]*)?)'
    r'(?![/\w])'
)


def _clean_url_display(url):
    """Return a clean display label for a URL (domain + path, no scheme)."""
    try:
        from urllib.parse import urlparse
        p = urlparse(url if '://' in url else f'https://{url}')
        host = p.hostname or url
        host = host.lstrip('www.')
        path = p.path.rstrip('/')
        return host + path if path and path != '/' else host
    except Exception:
        return url


def _replace_urls_with_placeholders(text):
    """Find URLs (full + bare domains) in text and return (clean_text, links).

    Returns:
        clean_text: text with URLs replaced by their display labels.
        links: list of (display_label, full_url) tuples in order.
    """
    links = []

    def _collect_full(m):
        url = m.group(0)
        display = _clean_url_display(url)
        links.append((display, url))
        return display

    def _collect_bare(m):
        domain = m.group(0)
        display = _clean_url_display(domain)
        full = f'https://{domain}'
        links.append((display, full))
        return display

    result = _URL_RE.sub(_collect_full, text)
    result = _BARE_DOMAIN_RE.sub(_collect_bare, result)
    return result, links


# Compiled once at module level — used by _tokenize_inline
_INLINE_RE = re.compile(
    r'(?P<bold_italic>\*{3}(?P<bi_text>.+?)\*{3})'
    r'|(?P<bold>\*{2}(?P<b_text>.+?)\*{2})'
    r'|(?P<italic_star>\*(?P<is_text>.+?)\*)'
    r'|(?P<italic_under>_(?P<iu_text>.+?)_)'
    r'|(?P<strike>~~(?P<st_text>.+?)~~)'
    r'|(?P<code>`(?P<c_text>.+?)`)'
    r'|(?P<md_link>\[(?P<ml_text>.+?)\]\((?P<ml_url>[^)]+)\))'
    r'|(?P<full_url>https?://[^\s),<>]+)'
    r'|(?P<bare_domain>[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?'
    r'\.(?:com|co|net|org|io|dev|app|at|de|es|fr|uk|us|me|info|biz|tv|cc)'
    r'(?:/[^\s),<>]*)?)',
    re.DOTALL,
)


def _tokenize_inline(text):
    """Convert inline markdown to an ordered list of token dicts.

    Supported tokens:
      {'type': 'text',       'text': '...'}
      {'type': 'bold',       'text': '...'}
      {'type': 'italic',     'text': '...'}
      {'type': 'bold_italic','text': '...'}
      {'type': 'code',       'text': '...'}
      {'type': 'strike',     'text': '...'}
      {'type': 'link',       'text': '...', 'url': '...'}
    """
    tokens = []
    last_end = 0
    for m in _INLINE_RE.finditer(text):
        start, end = m.span()
        # Plain text between matches
        if start > last_end:
            tokens.append({'type': 'text', 'text': text[last_end:start]})
        if m.group('bold_italic'):
            tokens.append({'type': 'bold_italic', 'text': m.group('bi_text')})
        elif m.group('bold'):
            tokens.append({'type': 'bold', 'text': m.group('b_text')})
        elif m.group('italic_star'):
            tokens.append({'type': 'italic', 'text': m.group('is_text')})
        elif m.group('italic_under'):
            tokens.append({'type': 'italic', 'text': m.group('iu_text')})
        elif m.group('strike'):
            tokens.append({'type': 'strike', 'text': m.group('st_text')})
        elif m.group('code'):
            tokens.append({'type': 'code', 'text': m.group('c_text')})
        elif m.group('md_link'):
            url = m.group('ml_url')
            if not url.startswith('http'):
                url = 'https://' + url
            tokens.append({'type': 'link', 'text': m.group('ml_text'), 'url': url})
        elif m.group('full_url'):
            url = m.group('full_url')
            tokens.append({'type': 'link', 'text': _clean_url_display(url), 'url': url})
        elif m.group('bare_domain'):
            domain = m.group('bare_domain')
            tokens.append({'type': 'link', 'text': _clean_url_display(domain),
                           'url': f'https://{domain}'})
        last_end = end
    # Remaining plain text
    if last_end < len(text):
        tokens.append({'type': 'text', 'text': text[last_end:]})
    return tokens


def _draw_line_with_links(c, x, y, line, font_name, font_size, text_color,
                          link_color=None, bold_font_name=None):
    """Draw a single line of text with full inline Markdown support.

    Handles: **bold**, *italic*, ***bold-italic***, `inline code`,
    [text](url) links, bare domain links, ~~strikethrough~~.
    """
    if link_color is None:
        link_color = colors.HexColor('#059669')  # emerald-600
    if bold_font_name is None:
        bold_font_name = _font('bold')

    tokens = _tokenize_inline(line)
    cx = x

    for tok in tokens:
        tok_type = tok['type']
        tok_text = tok.get('text', '')
        if not tok_text:
            continue

        if tok_type == 'text':
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)
            c.drawString(cx, y, tok_text)
            cx += c.stringWidth(tok_text, font_name, font_size)

        elif tok_type == 'bold':
            fn = bold_font_name
            c.setFont(fn, font_size)
            c.setFillColor(text_color)
            c.drawString(cx, y, tok_text)
            cx += c.stringWidth(tok_text, fn, font_size)

        elif tok_type == 'italic':
            fn = _font('italic')
            c.setFont(fn, font_size)
            c.setFillColor(text_color)
            c.drawString(cx, y, tok_text)
            cx += c.stringWidth(tok_text, fn, font_size)

        elif tok_type == 'bold_italic':
            fn = _font('bolditalic')
            c.setFont(fn, font_size)
            c.setFillColor(text_color)
            c.drawString(cx, y, tok_text)
            cx += c.stringWidth(tok_text, fn, font_size)

        elif tok_type == 'code':
            fn = 'Courier'
            code_size = max(font_size - 1, 7)
            tw = c.stringWidth(tok_text, fn, code_size)
            pad = 3
            # Gray pill background
            c.saveState()
            c.setFillColor(colors.HexColor('#F3F4F6'))  # gray-100
            c.roundRect(cx - pad, y - 2, tw + pad * 2, font_size + 2, 2, fill=1, stroke=0)
            c.restoreState()
            c.setFont(fn, code_size)
            c.setFillColor(colors.HexColor('#6B7280'))  # gray-500
            c.drawString(cx, y, tok_text)
            cx += tw + pad * 2

        elif tok_type == 'link':
            url = tok.get('url', '')
            c.setFont(font_name, font_size)
            c.setFillColor(link_color)
            tw = c.stringWidth(tok_text, font_name, font_size)
            if url:
                c.linkURL(url, (cx, y - 2, cx + tw, y + font_size - 1), relative=0)
            c.drawString(cx, y, tok_text)
            # Underline
            c.setStrokeColor(link_color)
            c.setLineWidth(0.4)
            c.line(cx, y - 1.5, cx + tw, y - 1.5)
            cx += tw

        elif tok_type == 'strike':
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)
            tw = c.stringWidth(tok_text, font_name, font_size)
            c.drawString(cx, y, tok_text)
            # Strikethrough line at 40% of font height
            strike_y = y + font_size * 0.35
            c.setStrokeColor(text_color)
            c.setLineWidth(0.6)
            c.line(cx, strike_y, cx + tw, strike_y)
            cx += tw

    return cx


def _safe(data, key, default=''):
    """Safely get a key from a dict, returning default if missing."""
    if not isinstance(data, dict):
        return default
    val = data.get(key, default)
    if val is None or val == '':
        return default
    return val


# ─────────────────────────────────────────────────────────────
# Auto-pagination helpers
# ─────────────────────────────────────────────────────────────

def _new_page(c, ps):
    """Emit current page and start a new one with header bar + footer."""
    _draw_footer(c, ps['num'], ps.get('total'), ps['client'])
    c.showPage()
    ps['num'] += 1
    _draw_header_bar(c)
    return PAGE_H - MARGIN_T


def _check_y(c, y, ps, need=20):
    """If y is too low, start a new page and return fresh y."""
    if y < MARGIN_B + need:
        y = _new_page(c, ps)
    return y


# ─────────────────────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────────────────────

def _draw_header_bar(c):
    """Draw a thin accent bar at the top of the page."""
    c.setFillColor(ESMERALD)
    c.rect(0, PAGE_H - 6, PAGE_W, 6, fill=1, stroke=0)
    # Lemon accent dot
    c.setFillColor(LEMON)
    c.circle(PAGE_W - 30, PAGE_H - 3, 3, fill=1, stroke=0)


def _draw_green_bar(c):
    """Alias kept for backward compatibility."""
    _draw_header_bar(c)


def _draw_footer(c, page_num, total_pages=None, client_name=''):
    """Draw a discrete footer with page number and branding."""
    footer_y = MARGIN_B - 14
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.4)
    c.line(MARGIN_L, footer_y, PAGE_W - MARGIN_R, footer_y)
    c.setFont(_font('regular'), 7)
    c.setFillColor(GRAY_500)
    c.drawString(MARGIN_L, footer_y - 11, 'Project App  |  projectapp.co')
    if client_name:
        c.drawCentredString(PAGE_W / 2, footer_y - 11, client_name)
    c.setFillColor(GREEN_LIGHT)
    page_label = (
        f'{page_num} / {total_pages}' if total_pages
        else f'P\u00e1gina {page_num}'
    )
    c.drawRightString(PAGE_W - MARGIN_R, footer_y - 11, page_label)


def _draw_section_header(c, y, index_str, title, ps=None):
    """Draw section index + title and return the new y position."""
    if index_str:
        c.setFont(_font('light'), 11)
        c.setFillColor(GREEN_LIGHT)
        c.drawString(MARGIN_L, y, str(index_str).zfill(2))
        y -= 22
    c.setFont(_font('light'), 24)
    c.setFillColor(ESMERALD)
    max_chars = 38
    clean_title = _strip_emoji(title)
    if len(clean_title) > max_chars:
        lines = textwrap.wrap(clean_title, width=max_chars)
        for line in lines:
            c.drawString(MARGIN_L, y, line)
            y -= 30
    else:
        c.drawString(MARGIN_L, y, clean_title)
        y -= 30
    # Thin accent line
    c.setStrokeColor(LEMON)
    c.setLineWidth(2)
    c.line(MARGIN_L, y + 6, MARGIN_L + 60, y + 6)
    y -= 18
    return y


def _draw_paragraphs(c, y, paragraphs, max_width=None, font_size=10,
                      leading=15, color=ESMERALD_80, ps=None, x=None):
    """Draw a list of paragraph strings and return the new y."""
    if max_width is None:
        max_width = CONTENT_W
    if x is None:
        x = MARGIN_L
    chars_per_line = int(max_width / (font_size * 0.48))
    fn = _font('regular')
    for para in (paragraphs or []):
        if not para:
            continue
        clean, _links = _replace_urls_with_placeholders(_strip_emoji(str(para)))
        lines = textwrap.wrap(clean, width=chars_per_line)
        if ps and len(lines) > 1 and y < MARGIN_B + leading * 2:
            y = _new_page(c, ps)
        for line in lines:
            if ps:
                y = _check_y(c, y, ps)
            elif y < MARGIN_B + 20:
                return y
            _draw_line_with_links(c, x, y, line, fn, font_size, color)
            y -= leading
        y -= 5
    return y


def _draw_bullet_list(c, y, items, x=None, max_width=None,
                       font_size=9, leading=13, color=ESMERALD_80,
                       bullet='\u2022', ps=None, numbered=False):
    """Draw a bulleted list and return the new y."""
    if max_width is None:
        max_width = CONTENT_W
    if x is None:
        x = MARGIN_L
    chars_per_line = int(max_width / (font_size * 0.48))
    fn = _font('regular')
    for item_idx, item in enumerate(items or []):
        # Support both legacy string items and new dict items {text, children}
        if isinstance(item, dict):
            item_text = item.get('text', '')
            children  = item.get('children', [])
        else:
            item_text = str(item)
            children  = []

        clean = _strip_emoji(item_text)
        lines = textwrap.wrap(clean, width=chars_per_line - 4) or [clean]
        if ps and len(lines) > 1 and y < MARGIN_B + leading * 2:
            y = _new_page(c, ps)
        for i, line in enumerate(lines):
            if ps:
                y = _check_y(c, y, ps)
            elif y < MARGIN_B + 20:
                return y
            if i == 0:
                if numbered:
                    prefix = f'  {item_idx + 1}.  '
                else:
                    prefix = f'  {bullet}  '
            else:
                prefix = '      '
            # Draw prefix in normal color, then line with inline formatting
            c.setFont(fn, font_size)
            c.setFillColor(color)
            pw = c.stringWidth(prefix, fn, font_size)
            c.drawString(x, y, prefix)
            _draw_line_with_links(c, x + pw, y, line, fn, font_size, color)
            y -= leading
        y -= 2

        # Render nested children (1 level deep) with en-dash + indent
        if children:
            child_x = x + 18
            child_bullet = '\u2013'  # en-dash
            child_chars = int((max_width - 18) / (font_size * 0.48))
            for child in children:
                child_clean = _strip_emoji(str(child))
                child_lines = textwrap.wrap(child_clean, width=child_chars - 4) or [child_clean]
                for ci, cline in enumerate(child_lines):
                    if ps:
                        y = _check_y(c, y, ps)
                    elif y < MARGIN_B + 20:
                        return y
                    child_prefix = f'  {child_bullet}  ' if ci == 0 else '      '
                    c.setFont(fn, font_size)
                    c.setFillColor(color)
                    cpw = c.stringWidth(child_prefix, fn, font_size)
                    c.drawString(child_x, y, child_prefix)
                    _draw_line_with_links(c, child_x + cpw, y, cline, fn, font_size, color)
                    y -= leading
                y -= 1

    return y


def _sidebar_box_height(items, sidebar_w=None):
    """Pre-calculate the height a sidebar box would occupy (without drawing)."""
    sw = sidebar_w or SIDEBAR_W
    line_h = 13
    header_h = 22
    items_h = sum(
        max(1, len(textwrap.wrap(str(it), width=int(sw / 5.2)))) * line_h + 2
        for it in (items or [])
    )
    return header_h + items_h + 14


def _draw_sidebar_box(c, y_start, title, items, sidebar_x=None,
                       sidebar_w=None):
    """Draw a branded sidebar box with a title and bullet items."""
    sx = sidebar_x or SIDEBAR_X
    sw = sidebar_w or SIDEBAR_W
    line_h = 13
    header_h = 22
    items_h = sum(
        max(1, len(textwrap.wrap(str(it), width=int(sw / 5.2)))) * line_h + 2
        for it in (items or [])
    )
    box_h = header_h + items_h + 14
    box_y = y_start - box_h

    c.setFillColor(ESMERALD_LIGHT)
    c.roundRect(sx, box_y, sw, box_h, 6, fill=1, stroke=0)

    inner_y = y_start - 16
    c.setFont(_font('bold'), 10)
    c.setFillColor(ESMERALD)
    c.drawString(sx + 10, inner_y, _strip_emoji(str(title)))
    inner_y -= 16

    c.setFont(_font('regular'), 9)
    c.setFillColor(ESMERALD_80)
    chars = int(sw / 5.2)
    for item in (items or []):
        text = _strip_emoji(str(item))
        lines = textwrap.wrap(text, width=chars)
        for j, line in enumerate(lines):
            prefix = '\u2022  ' if j == 0 else '    '
            c.drawString(sx + 10, inner_y, f'{prefix}{line}')
            inner_y -= line_h
        inner_y -= 2

    return box_y


def _draw_subtitle(c, y, text, color=ESMERALD, ps=None):
    """Draw a bold subtitle and return the new y."""
    if ps:
        y = _check_y(c, y, ps, need=24)
    c.setFont(_font('bold'), 12)
    c.setFillColor(color)
    c.drawString(MARGIN_L, y, _strip_emoji(str(text)))
    return y - 18


def _draw_pill(c, x, y, text, bg_color=ESMERALD_LIGHT, text_color=ESMERALD,
               font_size=7, padding_h=8, padding_v=3):
    """Draw a rounded pill/badge and return (right_x, pill_y_bottom).

    The pill is vertically centred on *y* so that it aligns nicely next to
    text drawn at the same y coordinate.
    """
    text = _strip_emoji(str(text))
    c.setFont(_font('medium'), font_size)
    tw = c.stringWidth(text, _font('medium'), font_size)
    pill_w = tw + padding_h * 2
    pill_h = font_size + padding_v * 2
    pill_y = y - padding_v + 1
    c.setFillColor(bg_color)
    c.roundRect(x, pill_y, pill_w, pill_h, pill_h / 2, fill=1, stroke=0)
    c.setFont(_font('medium'), font_size)
    c.setFillColor(text_color)
    c.drawString(x + padding_h, y, text)
    return x + pill_w, pill_y


def _draw_banner_box(c, x, y, width, text, bg_color=BONE,
                     text_color=ESMERALD, font_size=9, icon_text='',
                     ps=None):
    """Draw a full-width banner box with optional icon prefix. Returns new y."""
    text = _strip_emoji(str(text))
    leading = font_size + 3
    pad_x = 12
    pad_y = 10

    # Calculate available width for body text
    icon_w = 0
    if icon_text:
        icon_w = pdfmetrics.stringWidth(
            icon_text, _font('bold'), font_size
        ) + 6

    avail_w = width - 2 * pad_x - icon_w
    char_w = font_size * 0.48
    wrap_width = max(int(avail_w / char_w), 20)
    lines = textwrap.wrap(text, width=wrap_width)
    if not lines:
        lines = ['']

    box_h = 2 * pad_y + len(lines) * leading
    if ps:
        y = _check_y(c, y, ps, need=box_h + 12)

    box_y = y - box_h + 8
    c.setFillColor(bg_color)
    c.roundRect(x, box_y, width, box_h, 6, fill=1, stroke=0)

    inner_x = x + pad_x
    text_top_y = box_y + box_h - pad_y - font_size + 2
    if icon_text:
        c.setFont(_font('bold'), font_size)
        c.setFillColor(text_color)
        c.drawString(inner_x, text_top_y, icon_text)
        inner_x += icon_w

    c.setFont(_font('regular'), font_size)
    c.setFillColor(text_color)
    ty = text_top_y
    for line in lines:
        c.drawString(inner_x, ty, line)
        ty -= leading
    return box_y - 6


# ─────────────────────────────────────────────────────────────
# Markdown parsing helpers
# ─────────────────────────────────────────────────────────────

def _parse_markdown_lines(raw):
    """Parse raw markdown text into a list of (type, text) tuples.

    Supported types: 'h1', 'h2', 'h3', 'h4', 'bullet', 'numbered',
    'bold_line', 'paragraph', 'blank'.
    Inline **bold** markers are stripped into clean text.
    """
    if not raw:
        return []
    raw = _BR_TAG_RE.sub('\n', raw)
    raw = _BOLD_HTML_RE.sub(r'**\1**', raw)
    raw = _HTML_TAG_RE.sub('', raw)
    result = []
    for line in raw.split('\n'):
        stripped = line.strip()
        if not stripped:
            result.append(('blank', ''))
            continue
        # Headings
        if stripped.startswith('#### '):
            result.append(('h4', stripped[5:].strip()))
        elif stripped.startswith('### '):
            result.append(('h3', stripped[4:].strip()))
        elif stripped.startswith('## '):
            result.append(('h2', stripped[3:].strip()))
        elif stripped.startswith('# '):
            result.append(('h1', stripped[2:].strip()))
        # Bullet list
        elif stripped.startswith('- ') or stripped.startswith('* '):
            result.append(('bullet', stripped[2:].strip()))
        # Numbered list (e.g. "1. ", "2. ")
        elif len(stripped) > 2 and stripped[0].isdigit() and '. ' in stripped[:5]:
            idx = stripped.index('. ')
            result.append(('numbered', stripped[idx + 2:].strip()))
        # Line that is entirely bold  **text**
        elif stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4:
            result.append(('bold_line', stripped[2:-2].strip()))
        else:
            result.append(('paragraph', stripped))
    return result


def _clean_inline_bold(text):
    """Strip **bold** markers from inline text for PDF rendering."""
    return re.sub(r'\*\*(.+?)\*\*', r'\1', text)


# ─────────────────────────────────────────────────────────────
# New drawing functions
# ─────────────────────────────────────────────────────────────

def _draw_table(c, y, headers, rows, ps=None, max_width=None):
    """Draw a table with header row and data rows. Returns new y."""
    if not headers:
        return y
    if max_width is None:
        max_width = CONTENT_W

    x_start = MARGIN_L
    num_cols = len(headers)
    col_w = max_width / num_cols
    cell_pad_h = 6
    cell_pad_v = 4
    header_font_size = 9
    data_font_size = 8
    leading = 12

    def _draw_header_row(c, y):
        """Draw the header row and return new y."""
        # Calculate header row height
        max_lines = 1
        for h in headers:
            clean = _strip_emoji(str(h))
            chars = int((col_w - 2 * cell_pad_h) / (header_font_size * 0.48))
            lines = textwrap.wrap(clean, width=max(chars, 10))
            max_lines = max(max_lines, len(lines) if lines else 1)
        row_h = max_lines * leading + 2 * cell_pad_v

        # Background
        c.setFillColor(ESMERALD)
        c.rect(x_start, y - row_h, max_width, row_h, fill=1, stroke=0)

        # Text
        for ci, h in enumerate(headers):
            cx = x_start + ci * col_w + cell_pad_h
            clean = _strip_emoji(str(h))
            chars = int((col_w - 2 * cell_pad_h) / (header_font_size * 0.48))
            lines = textwrap.wrap(clean, width=max(chars, 10)) or ['']
            ty = y - cell_pad_v - header_font_size + 2
            for line in lines:
                c.setFont(_font('bold'), header_font_size)
                c.setFillColor(WHITE)
                c.drawString(cx, ty, line)
                ty -= leading

        return y - row_h

    # Draw initial header
    if ps:
        y = _check_y(c, y, ps, need=40)
    y = _draw_header_row(c, y)

    # Draw data rows
    for ri, row in enumerate(rows or []):
        # Calculate row height
        max_lines = 1
        for cell in row:
            clean = _strip_emoji(str(cell))
            chars = int((col_w - 2 * cell_pad_h) / (data_font_size * 0.48))
            lines = textwrap.wrap(clean, width=max(chars, 10))
            max_lines = max(max_lines, len(lines) if lines else 1)
        row_h = max_lines * leading + 2 * cell_pad_v

        # Check pagination
        if ps and y - row_h < MARGIN_B + 20:
            y = _new_page(c, ps)
            y = _draw_header_row(c, y)

        # Alternating background
        bg = ESMERALD_LIGHT if ri % 2 == 0 else WHITE
        c.setFillColor(bg)
        c.rect(x_start, y - row_h, max_width, row_h, fill=1, stroke=0)

        # Bottom border
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.4)
        c.line(x_start, y - row_h, x_start + max_width, y - row_h)

        # Cell text
        for ci, cell in enumerate(row):
            cx = x_start + ci * col_w + cell_pad_h
            clean = _strip_emoji(str(cell))
            chars = int((col_w - 2 * cell_pad_h) / (data_font_size * 0.48))
            lines = textwrap.wrap(clean, width=max(chars, 10)) or ['']
            ty = y - cell_pad_v - data_font_size + 2
            fn = _font('regular')
            for line in lines:
                _draw_line_with_links(c, cx, ty, line, fn, data_font_size, ESMERALD_80)
                ty -= leading

        y -= row_h

    return y - 6


def _draw_blockquote(c, y, text, ps=None):
    """Draw a blockquote with left accent bar. Returns new y."""
    if not text:
        return y

    clean, _links = _replace_urls_with_placeholders(_strip_emoji(str(text)))
    font_size = 9
    line_leading = 13
    pad = 12
    accent_w = 3
    avail_w = CONTENT_W - 2 * pad - accent_w
    chars = int(avail_w / (font_size * 0.48))
    lines = textwrap.wrap(clean, width=max(chars, 20))
    if not lines:
        lines = ['']

    box_h = 2 * pad + len(lines) * line_leading

    if ps:
        y = _check_y(c, y, ps, need=box_h + 8)

    box_y = y - box_h

    # Background
    c.setFillColor(BONE)
    c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 6, fill=1, stroke=0)

    # Left accent bar
    c.setFillColor(LEMON)
    c.rect(MARGIN_L, box_y, accent_w, box_h, fill=1, stroke=0)

    # Text
    fn = _font('regular')
    ty = y - pad - font_size + 2
    for line in lines:
        _draw_line_with_links(c, MARGIN_L + accent_w + pad, ty, line,
                              fn, font_size, ESMERALD)
        ty -= line_leading

    return box_y - 6


_CALLOUT_STYLES = {
    'note':      {'label': 'NOTA',       'bg': '#E6EFEF', 'bar': '#002921'},   # ESMERALD_LIGHT / ESMERALD
    'tip':       {'label': 'CONSEJO',    'bg': '#F0FFF4', 'bar': '#809490'},   # green-50 / GREEN_LIGHT
    'important': {'label': 'IMPORTANTE', 'bg': '#EEF2FF', 'bar': '#6366F1'},   # indigo-50 / indigo-500
    'warning':   {'label': 'AVISO',      'bg': '#FFFBEB', 'bar': '#F0FF3D'},   # amber-50 / LEMON
    'caution':   {'label': 'PRECAUCION', 'bg': '#FFF1F2', 'bar': '#F43F5E'},   # rose-50 / rose-500
}


def _draw_callout_box(c, y, text, style='note', ps=None):
    """Draw a GitHub-style callout box with a left accent bar and label.

    Args:
        c: ReportLab canvas.
        y: Current y position (top of block).
        text: Body text (supports inline markdown formatting).
        style: One of note | tip | important | warning | caution.
        ps: Pagination state dict.
    """
    cfg = _CALLOUT_STYLES.get(style, _CALLOUT_STYLES['note'])
    bg_color   = colors.HexColor(cfg['bg'])
    bar_color  = colors.HexColor(cfg['bar'])
    label_text = cfg['label']

    font_size  = 9
    label_size = 8
    leading    = font_size * 1.35
    pad_x      = 14   # horizontal padding inside box (after bar)
    pad_y      = 10   # vertical padding top/bottom
    bar_w      = 4    # accent bar width
    label_h    = label_size + 4

    # Wrap text to calculate height
    text_w = CONTENT_W - bar_w - pad_x * 2
    wrapped_lines = []
    for raw_line in (text or '').split('\n'):
        words = raw_line.split()
        current = ''
        for word in words:
            test = (current + ' ' + word).strip()
            if c.stringWidth(_strip_emoji(test), _font('regular'), font_size) <= text_w:
                current = test
            else:
                if current:
                    wrapped_lines.append(current)
                current = word
        if current:
            wrapped_lines.append(current)
    if not wrapped_lines:
        wrapped_lines = ['']

    box_h = pad_y + label_h + len(wrapped_lines) * leading + pad_y
    need  = box_h + 16

    if ps:
        y = _check_y(c, y, ps, need=max(need, 60))

    # Background
    c.saveState()
    c.setFillColor(bg_color)
    c.roundRect(MARGIN_L, y - box_h, CONTENT_W, box_h, 4, fill=1, stroke=0)
    # Left accent bar
    c.setFillColor(bar_color)
    c.rect(MARGIN_L, y - box_h, bar_w, box_h, fill=1, stroke=0)
    c.restoreState()

    # Label
    text_x = MARGIN_L + bar_w + pad_x
    label_y = y - pad_y - label_size
    c.setFont(_font('bold'), label_size)
    c.setFillColor(bar_color)
    c.drawString(text_x, label_y, label_text)

    # Body text lines
    body_y = label_y - leading * 0.6
    for wl in wrapped_lines:
        body_y -= leading
        if ps:
            if body_y < MARGIN_B + leading:
                _draw_footer(c, ps['num'], client_name=ps.get('client', ''))
                c.showPage()
                ps['num'] += 1
                _draw_header_bar(c)
                body_y = PAGE_H - MARGIN_T - leading
        _draw_line_with_links(
            c, text_x, body_y, _strip_emoji(wl),
            _font('regular'), font_size, ESMERALD_DARK,
        )

    return y - box_h - 12


def _draw_code_block(c, y, content, ps=None, language=None):
    """Draw a preformatted code block. Returns new y."""
    if not content:
        return y

    font_size = 8
    line_leading = 11
    pad = 10
    code_lines = content.split('\n')

    box_h = 2 * pad + len(code_lines) * line_leading

    if ps:
        y = _check_y(c, y, ps, need=min(box_h + 8, PAGE_H - MARGIN_T - MARGIN_B))

    # If block is taller than page, we need to split
    if box_h > PAGE_H - MARGIN_T - MARGIN_B - 40:
        # Render lines one by one with pagination
        for line in code_lines:
            if ps:
                y = _check_y(c, y, ps, need=line_leading + 4)
            c.setFont('Courier', font_size)
            c.setFillColor(ESMERALD_80)
            c.drawString(MARGIN_L + pad, y, line)
            y -= line_leading
        return y - 6

    box_y = y - box_h

    # Background
    c.setFillColor(GRAY_200)
    c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 6, fill=1, stroke=0)

    # Border
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.5)
    c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 6, fill=0, stroke=1)

    # Code text
    c.setFont('Courier', font_size)
    c.setFillColor(ESMERALD_80)
    ty = y - pad - font_size + 2
    for line in code_lines:
        c.drawString(MARGIN_L + pad, ty, line)
        ty -= line_leading

    return box_y - 6


def _draw_separator(c, y, ps=None):
    """Draw a horizontal rule. Returns new y."""
    y -= 12
    if ps:
        y = _check_y(c, y, ps, need=4)
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y, PAGE_W - MARGIN_R, y)
    return y - 12


def safe_pdf_filename(prefix, proposal_title, date_str):
    """Build a clean filename: Prefix_SafeTitle_YYYY-MM-DD.pdf"""
    safe = re.sub(r'[^\w\s-]', '', proposal_title or '').strip()
    safe = re.sub(r'\s+', '_', safe)[:80]
    return f'{prefix}_{safe}_{date_str}.pdf'
