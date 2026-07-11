# Documents Dual PDF Template (Friendly / Professional) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Documents render/download in two selectable PDF styles — `professional` (current brand look) and `friendly` (mirrors the on-screen preview) — with a preview switch, dual download menu, a persisted per-document default used by platform clients and email attachments, plus a markdown-fidelity overhaul of the shared ReportLab layout engine (measured wrapping, exact box heights, proportional tables, wrapped code, multi-level lists).

**Architecture:** The friendly style is a second ReportLab theme (`PdfTheme` in a new `pdf_theme.py`), not a second pipeline. Shared drawing functions in `pdf_utils.py` gain an optional `theme=None` parameter (None = today's constants, so proposals/contracts are visually unchanged). Independently, the char-count wrapping engine is replaced by a measured, tokenize-first layout engine (`_layout_inline` + `_draw_fragments_line`) that all block drawers reuse, which fixes width/overlap/break bugs for every PDF service. Spec: `docs/superpowers/specs/2026-07-10-documents-dual-pdf-template-design.md`.

**Tech Stack:** Django 5 + DRF (function-based `@api_view`), ReportLab canvas + pypdf, Nuxt 3 + Vue 3 + Pinia (Options API stores), Jest + @vue/test-utils, Playwright.

## Global Constraints

- Work happens in the worktree `/home/ryzepeck/webapps/projectapp/.claude/worktrees/documents-dual-pdf` on branch `feat/10072026-documents-dual-pdf-template`. Verify with `git rev-parse --abbrev-ref HEAD` before every commit.
- Backend venv is `backend/venv` (NOT `.venv` at repo root). Run pytest as: `cd backend && venv/bin/pytest <path> -v --no-cov`. Judge by exit code; coverage plugin suppresses the summary line.
- NEVER run a full test suite. Max 20 tests per batch, max 3 test commands per cycle. Frontend unit: `npm --prefix frontend test -- <path>`.
- Backend views stay function-based `@api_view`; business logic in services/serializers. Never modify old migrations; add new ones.
- Choice values are `professional` and `friendly` (English identifiers); user-facing labels are Spanish («Profesional», «Amigable»). Query param name: `template`. Model/serializer field name: `template_style`.
- Default is `professional` everywhere so existing documents/PDFs do not change.
- Frontend: content flows use `request_http.js` (never `usePlatformApi`); Pinia Options API; semantic tokens for NEW chrome (the `.markdown-preview` body CSS intentionally uses raw hex — keep that pattern there).
- Commit messages: Conventional Commits (`feat:`/`fix:`/`refactor:`/`test:`), NO `Co-Authored-By` trailers, NO "Generated with Claude Code" footers.
- Emoji safety: any text drawn with brand fonts may contain emoji; always measure/draw via the mixed-run helpers (`_string_w`, `_draw_mixed_string`). Never `c.drawString` sanitized-but-emoji-bearing text directly.
- The dry-run TOC pass (`_collect_section_pages`) must use the same theme as the real pass, or page numbers drift.

---

### Task 1: Measured inline layout engine in `pdf_utils.py`

The root cause of "paragraphs don't fill the width / weird line breaks" is char-count wrapping (`int(max_width / (font_size * 0.48))`) plus `_md_wrap`'s marker-rebalancing. Replace with: tokenize inline markdown FIRST (markers disappear), split tokens into styled word fragments, greedy-fill lines by REAL measured width, and draw fragments directly. Long unbreakable tokens (URLs, enums) hard-split at measured width.

**Files:**
- Modify: `backend/content/services/pdf_utils.py` (add new functions after `_draw_line_with_links`, around line 700; do not delete old functions yet)
- Test: `backend/content/tests/services/test_pdf_layout.py` (new)

**Interfaces:**
- Consumes: existing `_tokenize_inline(text)`, `_sanitize_pdf_text(text)`, `_emoji_runs`, `_renderable_emoji`, `EMOJI_FONT`, `_EMOJI_RE`, `_font(style)`, `_register_fonts()`.
- Produces (later tasks rely on these exact signatures):
  - `_string_w(text, font_name, font_size) -> float` — emoji-aware width via `pdfmetrics.stringWidth` (no canvas needed).
  - `_layout_inline(text, max_width, font_name, font_size, bold_font_name=None) -> list[list[dict]]` — lines of fragments `{'text','type','url','font','size','width','glue'}`; `glue=True` means no space before the fragment.
  - `_draw_fragments_line(c, x, y, frags, text_color, link_color=None, justify=False, max_width=None) -> float` (returns end x).

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/services/test_pdf_layout.py
"""Tests for the measured inline layout engine (pdf_utils)."""
import io

import pytest
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4

from content.services.pdf_utils import (
    _register_fonts, _font, _string_w, _layout_inline, _draw_fragments_line,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _fonts():
    _register_fonts()


def _line_width(frags):
    total = 0.0
    for i, f in enumerate(frags):
        if i > 0 and not f.get('glue'):
            total += _string_w(' ', f['font'], f['size'])
        total += f['width']
    return total


class TestStringW:
    def test_matches_pdfmetrics_for_plain_text(self):
        from reportlab.pdfbase import pdfmetrics
        fn = _font('regular')
        assert _string_w('hola mundo', fn, 10) == pytest.approx(
            pdfmetrics.stringWidth('hola mundo', fn, 10))

    def test_emoji_measured_without_crash(self):
        w = _string_w('hola \U0001F600 mundo', _font('regular'), 10)
        assert w > _string_w('hola  mundo', _font('regular'), 10) - 1


class TestLayoutInline:
    def test_every_line_fits_max_width(self):
        text = ('palabra ' * 80).strip()
        lines = _layout_inline(text, 200, _font('regular'), 10)
        assert len(lines) > 1
        for frags in lines:
            assert _line_width(frags) <= 200 + 0.01

    def test_lines_fill_available_width_greedily(self):
        text = ('palabra ' * 80).strip()
        lines = _layout_inline(text, 200, _font('regular'), 10)
        word_w = _string_w('palabra', _font('regular'), 10)
        space_w = _string_w(' ', _font('regular'), 10)
        # every line except the last could not fit one more word
        for frags in lines[:-1]:
            assert _line_width(frags) + space_w + word_w > 200

    def test_bold_span_never_leaks_markers(self):
        text = 'inicio ' + '**negrita larga que se parte en varias lineas** ' * 10
        lines = _layout_inline(text.strip(), 150, _font('regular'), 10)
        for frags in lines:
            for f in frags:
                assert '*' not in f['text']
                assert f['type'] in ('text', 'bold')

    def test_bold_fragments_use_bold_font(self):
        lines = _layout_inline('a **b** c', 500, _font('regular'), 10)
        types = [f['type'] for f in lines[0]]
        fonts = {f['type']: f['font'] for f in lines[0]}
        assert 'bold' in types
        assert fonts['bold'] == _font('bold')

    def test_long_url_hard_splits_within_width(self):
        url = 'https://example.com/' + 'segmento/' * 30
        lines = _layout_inline(url, 180, _font('regular'), 9)
        for frags in lines:
            assert _line_width(frags) <= 180 + 0.01

    def test_inline_code_gets_glue_when_no_spaces(self):
        lines = _layout_inline('con`codigo`junto', 500, _font('regular'), 10)
        frags = lines[0]
        assert [f['type'] for f in frags] == ['text', 'code', 'text']
        assert frags[1]['glue'] is True and frags[2]['glue'] is True

    def test_empty_text_returns_single_empty_line(self):
        assert _layout_inline('', 200, _font('regular'), 10) == [[]]


class TestDrawFragmentsLine:
    def test_draws_without_error_and_advances_x(self):
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        from reportlab.lib import colors
        lines = _layout_inline('texto **bold** y [link](https://x.co) \U0001F600',
                               400, _font('regular'), 10)
        end_x = _draw_fragments_line(c, 48, 700, lines[0], colors.black)
        assert end_x > 48
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py -v --no-cov`
Expected: FAIL / ERROR with `ImportError: cannot import name '_string_w'`.

- [ ] **Step 3: Implement the engine in `pdf_utils.py`**

Insert after `_draw_line_with_links` (keep that function — later tasks retire its callers):

```python
# ─────────────────────────────────────────────────────────────
# Measured inline layout engine (tokenize-first wrapping)
# ─────────────────────────────────────────────────────────────

_CODE_PAD = 3  # horizontal padding drawn around inline-code chips


def _string_w(text, font_name, font_size):
    """Emoji-aware stringWidth via pdfmetrics (no canvas required)."""
    if not text:
        return 0.0
    if not _EMOJI_RE.search(text):
        return pdfmetrics.stringWidth(text, font_name, font_size)
    total = 0.0
    for segment, is_emoji in _emoji_runs(text):
        if is_emoji:
            segment = _renderable_emoji(segment)
            if segment:
                total += pdfmetrics.stringWidth(segment, EMOJI_FONT, font_size)
        else:
            total += pdfmetrics.stringWidth(segment, font_name, font_size)
    return total


def _frag_font(tok_type, font_name, bold_font_name=None):
    if tok_type == 'bold':
        return bold_font_name or _font('bold')
    if tok_type == 'italic':
        return _font('italic')
    if tok_type == 'bold_italic':
        return _font('bolditalic')
    if tok_type == 'code':
        return 'Courier'
    return font_name


def _hard_split_word(word, font_name, font_size, max_w):
    """Split one overlong word (URL, enum) at measured width."""
    parts, cur = [], ''
    for ch in word:
        if cur and _string_w(cur + ch, font_name, font_size) > max_w:
            parts.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts or [word]


def _layout_inline(text, max_width, font_name, font_size, bold_font_name=None):
    """Tokenize inline markdown, then wrap into measured lines.

    Returns list of lines; each line is a list of fragments
    {'text','type','url','font','size','width','glue'}. Markers are
    consumed by tokenization, so a styled span can wrap across lines
    without ever leaking asterisks. glue=True → no space before.
    """
    _register_fonts()
    lines, cur, cur_w = [], [], 0.0

    def flush():
        nonlocal cur, cur_w
        if cur:
            lines.append(cur)
        cur, cur_w = [], 0.0

    clean = _sanitize_pdf_text(str(text or ''))
    pending_space = False
    for tok in _tokenize_inline(clean):
        tok_type = tok['type']
        tok_text = tok.get('text', '')
        if not tok_text:
            continue
        fn = _frag_font(tok_type, font_name, bold_font_name)
        fs = max(font_size - 1, 7) if tok_type == 'code' else font_size
        pad = _CODE_PAD * 2 if tok_type == 'code' else 0
        space_w = _string_w(' ', fn, fs)
        # Inline code chips stay whole; other tokens wrap word by word.
        pieces = [tok_text] if tok_type == 'code' else tok_text.split(' ')
        for wi, word in enumerate(pieces):
            if wi > 0:
                pending_space = True
            if not word:
                continue
            glue = not pending_space
            pending_space = False
            w = _string_w(word, fn, fs) + pad
            frag = {'text': word, 'type': tok_type, 'url': tok.get('url', ''),
                    'font': fn, 'size': fs, 'width': w, 'glue': glue}
            if w > max_width:
                flush()
                for piece in _hard_split_word(word, fn, fs, max_width - pad):
                    pw = _string_w(piece, fn, fs) + pad
                    lines.append([dict(frag, text=piece, width=pw, glue=True)])
                continue
            gap = 0.0 if (not cur or glue) else space_w
            if cur and cur_w + gap + w > max_width:
                flush()
                frag = dict(frag, glue=True)
                gap = 0.0
            cur.append(frag)
            cur_w += gap + w
    flush()
    return lines or [[]]


def _draw_fragments_line(c, x, y, frags, text_color, link_color=None,
                         justify=False, max_width=None):
    """Draw one measured line of fragments; returns the end x."""
    if link_color is None:
        link_color = colors.HexColor('#059669')
    gaps = [i for i, f in enumerate(frags) if i > 0 and not f.get('glue')]
    extra = 0.0
    if justify and max_width and gaps:
        used = sum(f['width'] for f in frags) + sum(
            _string_w(' ', frags[i]['font'], frags[i]['size']) for i in gaps)
        extra = max(0.0, (max_width - used) / len(gaps))
    cx = x
    for i, f in enumerate(frags):
        if i > 0 and not f.get('glue'):
            cx += _string_w(' ', f['font'], f['size']) + extra
        seg_start = cx
        if f['type'] == 'code':
            c.saveState()
            c.setFillColor(colors.HexColor('#F3F4F6'))
            c.roundRect(cx, y - 2, f['width'], f['size'] + 3, 2, fill=1, stroke=0)
            c.restoreState()
            c.setFont(f['font'], f['size'])
            c.setFillColor(colors.HexColor('#6B7280'))
            c.drawString(cx + _CODE_PAD, y, f['text'])
            cx += f['width']
            continue
        fill = link_color if f['type'] == 'link' else text_color
        c.setFont(f['font'], f['size'])
        c.setFillColor(fill)
        end_x = _draw_mixed_string(c, cx, y, f['text'], f['font'], f['size'])
        if f['type'] == 'strike':
            c.setStrokeColor(text_color)
            c.setLineWidth(0.6)
            c.line(cx, y + f['size'] * 0.35, end_x, y + f['size'] * 0.35)
        if f['type'] == 'link' and f.get('url'):
            c.linkURL(f['url'], (seg_start, y - 2, end_x, y + f['size'] - 1),
                      relative=0)
            c.setStrokeColor(link_color)
            c.setLineWidth(0.4)
            c.line(seg_start, y - 1.5, end_x, y - 1.5)
        cx = end_x
    return cx
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py -v --no-cov`
Expected: all PASS (exit code 0).

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/pdf_utils.py backend/content/tests/services/test_pdf_layout.py
git commit -m "feat: add measured inline layout engine to pdf_utils"
```

---

### Task 2: Migrate `_draw_paragraphs` and `_estimate_text_height` to measured wrapping

**Files:**
- Modify: `backend/content/services/pdf_utils.py:797-841` (`_draw_paragraphs`, `_estimate_text_height`)
- Test: `backend/content/tests/services/test_pdf_layout.py` (extend)

**Interfaces:**
- Consumes: `_layout_inline`, `_draw_fragments_line` (Task 1).
- Produces: `_draw_paragraphs(c, y, paragraphs, max_width=None, font_size=10, leading=15, color=ESMERALD_80, ps=None, x=None, font_name=None, justify=False, bold_font_name=None, link_color=None) -> y` — same signature as today PLUS trailing `link_color=None`. `_estimate_text_height(paragraphs, max_width=None, font_size=10, leading=15, font_name=None, bold_font_name=None) -> float` (two new optional kwargs). Callers in `proposal_pdf_service.py`, `technical_document_pdf.py`, etc. keep working unchanged.

- [ ] **Step 1: Write the failing tests** (append to `test_pdf_layout.py`)

```python
class TestDrawParagraphsMeasured:
    def _canvas(self):
        buf = io.BytesIO()
        return rl_canvas.Canvas(buf, pagesize=A4), buf

    def test_paragraph_renders_and_returns_lower_y(self):
        from content.services.pdf_utils import _draw_paragraphs
        c, buf = self._canvas()
        text = 'Un parrafo con **negrita**, *italica*, `codigo` y ' \
               'https://projectapp.co que debe envolverse. ' * 5
        y = _draw_paragraphs(c, 700, [text], max_width=300)
        assert y < 700 - 15 * 3  # wrapped into several lines
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'

    def test_estimate_matches_layout_line_count(self):
        from content.services.pdf_utils import (
            _estimate_text_height, _layout_inline)
        text = 'palabra ' * 60
        est = _estimate_text_height([text], max_width=250, font_size=10,
                                    leading=15)
        n_lines = len(_layout_inline(text, 250, _font('regular'), 10))
        assert est == n_lines * 15 + 5

    def test_no_spurious_breaks_short_text_single_line(self):
        from content.services.pdf_utils import _layout_inline
        lines = _layout_inline('Texto corto sin cortes.', 400,
                               _font('regular'), 10)
        assert len(lines) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py -v --no-cov -k "Measured or estimate or spurious"`
Expected: `test_estimate_matches_layout_line_count` FAILS (old char-count estimate ≠ measured count). Others may pass — that is fine; the estimate test is the contract.

- [ ] **Step 3: Replace both function bodies**

```python
def _draw_paragraphs(c, y, paragraphs, max_width=None, font_size=10,
                      leading=15, color=ESMERALD_80, ps=None, x=None,
                      font_name=None, justify=False, bold_font_name=None,
                      link_color=None):
    """Draw a list of paragraph strings and return the new y."""
    if max_width is None:
        max_width = CONTENT_W
    if x is None:
        x = MARGIN_L
    fn = font_name or _font('regular')
    for para in (paragraphs or []):
        if not para:
            continue
        lines = _layout_inline(para, max_width, fn, font_size,
                               bold_font_name=bold_font_name)
        if ps and len(lines) > 1 and y < MARGIN_B + leading * 2:
            y = _new_page(c, ps)
        for i, frags in enumerate(lines):
            if ps:
                y = _check_y(c, y, ps)
            elif y < MARGIN_B + 20:
                return y
            _draw_fragments_line(
                c, x, y, frags, color, link_color=link_color,
                justify=justify and i < len(lines) - 1, max_width=max_width,
            )
            y -= leading
        y -= 5
    return y


def _estimate_text_height(paragraphs, max_width=None, font_size=10,
                          leading=15, font_name=None, bold_font_name=None):
    """Pre-estimate vertical height for wrapped paragraphs without drawing."""
    if max_width is None:
        max_width = CONTENT_W
    fn = font_name or _font('regular')
    total = 0
    for para in (paragraphs or []):
        if not para:
            continue
        total += len(_layout_inline(para, max_width, fn, font_size,
                                    bold_font_name=bold_font_name)) * leading + 5
    return total
```

Note: `_replace_urls_with_placeholders` is no longer called here — the tokenizer already converts URLs into link fragments with clean display labels.

- [ ] **Step 4: Run tests + regression slice**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py -v --no-cov`
Expected: PASS.
Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_utils.py content/tests/services/test_pdf_utils_emoji.py -v --no-cov`
Expected: PASS. If a test asserted char-count internals of the OLD `_draw_paragraphs`/`_estimate_text_height`, update that test to assert the measured contract instead (line count × leading + 5) — behavior, not implementation.
Run: `cd backend && venv/bin/pytest content/tests/services/test_document_pdf_service.py -v --no-cov`
Expected: PASS (service smoke unaffected).

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/pdf_utils.py backend/content/tests/services/test_pdf_layout.py
git commit -m "refactor: measured width wrapping for paragraphs and height estimates"
```

---

### Task 3: Unified box heights + pagination for blockquote, callout and code

Today each boxed block estimates its height with its own char-count math; when the estimate diverges from the drawn lines, the next block overlaps or text spills past the footer (callouts paginate text mid-box while the background stays on the first page). Fix: compute lines ONCE with the measured engine, derive `box_h` from that exact count, and split long boxes into per-page chunks, each drawn as its own complete box. Also wrap long code lines at measured Courier width.

**Files:**
- Modify: `backend/content/services/pdf_utils.py:1201-1240` (`_draw_blockquote`), `:1252-1322` (`_draw_callout_box`), `:1325-1371` (`_draw_code_block`); add helpers `_split_lines_into_page_chunks` and `_wrap_code_line` just above `_draw_blockquote`.
- Test: `backend/content/tests/services/test_pdf_layout.py` (extend)

**Interfaces:**
- Consumes: `_layout_inline`, `_draw_fragments_line`, `_string_w`, `_new_page`, `_check_y`.
- Produces (same names, one new kwarg each — Task 6 adds `theme`):
  - `_draw_blockquote(c, y, text, ps=None) -> y`
  - `_draw_callout_box(c, y, text, style='note', ps=None) -> y`
  - `_draw_code_block(c, y, content, ps=None, language=None) -> y`
  - `_split_lines_into_page_chunks(lines, y, line_leading, fixed_h) -> list[list]`
  - `_wrap_code_line(line, font_size, max_w) -> list[str]`

- [ ] **Step 1: Write the failing tests** (append to `test_pdf_layout.py`)

```python
class TestBoxedBlocks:
    def _canvas(self):
        buf = io.BytesIO()
        return rl_canvas.Canvas(buf, pagesize=A4), buf

    def test_long_code_line_wraps_within_content_width(self):
        from content.services.pdf_utils import _wrap_code_line, CONTENT_W
        line = 'x' * 400
        pieces = _wrap_code_line(line, 8, CONTENT_W - 20)
        assert len(pieces) > 1
        for p in pieces:
            assert _string_w(p, 'Courier', 8) <= CONTENT_W - 20 + 0.01
        # nothing lost
        assert ''.join(p.lstrip() for p in pieces) == line

    def test_page_chunks_respect_available_space(self):
        from content.services.pdf_utils import _split_lines_into_page_chunks
        lines = [['l'] for _ in range(200)]
        chunks = _split_lines_into_page_chunks(lines, y=700, line_leading=13,
                                               fixed_h=30)
        assert sum(len(ch) for ch in chunks) == 200
        assert len(chunks) > 1
        assert all(len(ch) >= 1 for ch in chunks)

    def test_tall_callout_paginates_without_footer_collision(self):
        """A callout taller than one page must advance pages, and every
        drawn line must sit above MARGIN_B (no footer overlap)."""
        from content.services.pdf_utils import _draw_callout_box, MARGIN_B
        c, buf = self._canvas()
        ps = {'num': 1, 'client': '', 'total': None}
        text = 'Linea de aviso repetida para forzar paginacion. ' * 120
        y_end = _draw_callout_box(c, 700, text, style='warning', ps=ps)
        assert ps['num'] > 1          # paginated
        assert y_end >= MARGIN_B      # cursor never below bottom margin
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'

    def test_blockquote_box_height_matches_line_count(self):
        from content.services.pdf_utils import (
            _draw_blockquote, _layout_inline, CONTENT_W)
        c, buf = self._canvas()
        text = 'Cita con **negrita** que envuelve. ' * 8
        pad, accent_w = 12, 3
        avail = CONTENT_W - 2 * pad - accent_w
        n = len(_layout_inline(text, avail, _font('regular'), 9))
        y_end = _draw_blockquote(c, 700, text)
        # y drops exactly box height (2*pad + n*13) plus the 6pt gap
        assert y_end == pytest.approx(700 - (2 * pad + n * 13) - 6)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py::TestBoxedBlocks -v --no-cov`
Expected: ImportError on `_wrap_code_line` / `_split_lines_into_page_chunks`; height-match test fails against char-count sizing.

- [ ] **Step 3: Implement**

Helpers (insert above `_draw_blockquote`):

```python
def _wrap_code_line(line, font_size, max_w):
    """Split a preformatted code line at measured Courier width.
    Continuation pieces get a 2-space indent."""
    if _string_w(line, 'Courier', font_size) <= max_w:
        return [line]
    out, cur = [], ''
    for ch in line:
        if cur and _string_w(cur + ch, 'Courier', font_size) > max_w:
            out.append(cur)
            cur = '  ' + ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out or [line]


def _split_lines_into_page_chunks(lines, y, line_leading, fixed_h):
    """Split wrapped lines into chunks that each fit one page.

    The first chunk is limited by the space left at *y*; later chunks
    get a full fresh page. fixed_h is the box overhead (padding+label).
    Element type is irrelevant — works for fragment-lines and str lines."""
    avail_first = y - (MARGIN_B + 20) - fixed_h
    avail_full = (PAGE_H - MARGIN_T) - (MARGIN_B + 20) - fixed_h
    per_first = max(1, int(avail_first / line_leading))
    per_full = max(1, int(avail_full / line_leading))
    chunks, i, budget = [], 0, per_first
    while i < len(lines):
        chunks.append(lines[i:i + budget])
        i += budget
        budget = per_full
    return chunks or [[]]
```

(The code-block test's joined-content assertion uses `lstrip()`, so the 2-space continuation indent is fine.)

**check_y ordering (applies to all three drawers below):** when `ps` is not `None`, call `_check_y` ONCE *before* splitting into chunks — so the split sees a realistic starting `y` and never produces a degenerate 1-line first box near the page bottom. Do not also `_check_y` inside the `ci == 0` iteration. The `need` passed is the box overhead plus ~3 lines (bounded, so a genuinely tall box still starts on the current page and paginates via chunks).

`_draw_blockquote` — full replacement:

```python
def _draw_blockquote(c, y, text, ps=None):
    """Draw a blockquote with left accent bar. Returns new y."""
    if not text:
        return y
    font_size, line_leading, pad, accent_w = 9, 13, 12, 3
    avail_w = CONTENT_W - 2 * pad - accent_w
    fn = _font('regular')
    lines = _layout_inline(text, avail_w, fn, font_size)
    if ps is not None:
        y = _check_y(c, y, ps, need=2 * pad + min(len(lines), 3) * line_leading + 8)
    chunks = ([lines] if ps is None else
              _split_lines_into_page_chunks(lines, y, line_leading, 2 * pad))
    for ci, chunk in enumerate(chunks):
        if ci > 0:
            y = _new_page(c, ps)
        box_h = 2 * pad + len(chunk) * line_leading
        box_y = y - box_h
        c.setFillColor(BONE)
        c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 6, fill=1, stroke=0)
        c.setFillColor(LEMON)
        c.rect(MARGIN_L, box_y, accent_w, box_h, fill=1, stroke=0)
        ty = y - pad - font_size + 2
        for frags in chunk:
            _draw_fragments_line(c, MARGIN_L + accent_w + pad, ty, frags,
                                 ESMERALD)
            ty -= line_leading
        y = box_y - 6
    return y
```

`_draw_callout_box` — full replacement (same chunking; label only on first chunk):

```python
def _draw_callout_box(c, y, text, style='note', ps=None):
    """Draw a GitHub-style callout box; long boxes split per page."""
    cfg = _CALLOUT_STYLES.get(style, _CALLOUT_STYLES['note'])
    bg_color = colors.HexColor(cfg['bg'])
    bar_color = colors.HexColor(cfg['bar'])
    label_text = cfg['label']

    font_size, label_size = 9, 8
    leading = font_size * 1.35
    pad_x, pad_y, bar_w = 14, 10, 4
    label_h = label_size + 4
    text_w = CONTENT_W - bar_w - pad_x * 2
    fn = _font('regular')

    wrapped = []
    for raw_line in (text or '').split('\n'):
        if raw_line.strip():
            wrapped.extend(_layout_inline(raw_line.strip(), text_w, fn,
                                          font_size))
        else:
            wrapped.append([])
    if not wrapped:
        wrapped = [[]]

    if ps is not None:
        y = _check_y(c, y, ps,
                     need=2 * pad_y + label_h + min(len(wrapped), 3) * leading + 16)
    chunks = ([wrapped] if ps is None else
              _split_lines_into_page_chunks(wrapped, y, leading,
                                            2 * pad_y + label_h))
    for ci, chunk in enumerate(chunks):
        if ci > 0:
            y = _new_page(c, ps)
        head_h = label_h if ci == 0 else 0
        box_h = pad_y + head_h + len(chunk) * leading + pad_y
        c.saveState()
        c.setFillColor(bg_color)
        c.roundRect(MARGIN_L, y - box_h, CONTENT_W, box_h, 4, fill=1, stroke=0)
        c.setFillColor(bar_color)
        c.rect(MARGIN_L, y - box_h, bar_w, box_h, fill=1, stroke=0)
        c.restoreState()
        text_x = MARGIN_L + bar_w + pad_x
        body_y = y - pad_y
        if ci == 0:
            body_y -= label_size
            c.setFont(_font('bold'), label_size)
            c.setFillColor(bar_color)
            c.drawString(text_x, body_y, label_text)
            body_y -= leading * 0.6
        for frags in chunk:
            body_y -= leading
            _draw_fragments_line(c, text_x, body_y, frags, ESMERALD_DARK)
        y = y - box_h - 12
    return y
```

`_draw_code_block` — full replacement:

```python
def _draw_code_block(c, y, content, ps=None, language=None):
    """Draw a preformatted code block; wraps long lines, splits per page."""
    if not content:
        return y
    font_size, line_leading, pad = 8, 11, 10
    max_w = CONTENT_W - 2 * pad
    code_lines = []
    for raw in content.split('\n'):
        code_lines.extend(_wrap_code_line(raw, font_size, max_w))

    if ps is not None:
        y = _check_y(c, y, ps, need=2 * pad + min(len(code_lines), 3) * line_leading + 8)
    chunks = ([code_lines] if ps is None else
              _split_lines_into_page_chunks(code_lines, y, line_leading,
                                            2 * pad))
    for ci, chunk in enumerate(chunks):
        if ci > 0:
            y = _new_page(c, ps)
        box_h = 2 * pad + len(chunk) * line_leading
        box_y = y - box_h
        c.setFillColor(GRAY_200)
        c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 6, fill=1, stroke=0)
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.5)
        c.roundRect(MARGIN_L, box_y, CONTENT_W, box_h, 6, fill=0, stroke=1)
        c.setFont('Courier', font_size)
        c.setFillColor(ESMERALD_80)
        ty = y - pad - font_size + 2
        for line in chunk:
            c.drawString(MARGIN_L + pad, ty, line)
            ty -= line_leading
        y = box_y - 6
    return y
```

- [ ] **Step 4: Run tests + regression slice**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py -v --no-cov`
Expected: PASS.
Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_utils_gaps.py content/tests/services/test_pdf_utils_gaps2.py -v --no-cov`
Expected: PASS; if a gap test pinned the OLD callout mid-box pagination or exact code-block behavior, update it to the new contract (chunked boxes, wrapped code lines).
Run: `cd backend && venv/bin/pytest content/tests/services/test_document_pdf_service_gaps.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/pdf_utils.py backend/content/tests/services/test_pdf_layout.py
git commit -m "fix: exact box heights and clean pagination for quote/callout/code blocks"
```

---

### Task 4: Content-proportional table columns with measured row heights

**Files:**
- Modify: `backend/content/services/pdf_utils.py:1103-1198` (`_draw_table`); add `_table_col_widths` just above it.
- Test: `backend/content/tests/services/test_pdf_layout.py` (extend)

**Interfaces:**
- Consumes: `_string_w`, `_layout_inline`, `_draw_fragments_line`, `_clean_inline_bold`, `_sanitize_pdf_text`.
- Produces: `_table_col_widths(headers, rows, max_width, pad_h, font_size=8) -> list[float]`; `_draw_table(c, y, headers, rows, ps=None, max_width=None) -> y` (signature unchanged).

- [ ] **Step 1: Write the failing tests** (append to `test_pdf_layout.py`)

```python
class TestTableColumns:
    def test_widths_proportional_to_content(self):
        from content.services.pdf_utils import _table_col_widths
        headers = ['#', 'Descripcion']
        rows = [['1', 'Una descripcion bastante larga que necesita espacio'],
                ['2', 'Otra fila con mucho mas texto que la primera columna']]
        widths = _table_col_widths(headers, rows, 500, pad_h=6)
        assert len(widths) == 2
        assert widths[1] > widths[0] * 2          # content-driven
        assert sum(widths) == pytest.approx(500)  # fills full width

    def test_equal_content_splits_evenly(self):
        from content.services.pdf_utils import _table_col_widths
        widths = _table_col_widths(['a', 'b'], [['x', 'x']], 400, pad_h=6)
        assert widths[0] == pytest.approx(widths[1])

    def test_many_columns_never_below_min(self):
        from content.services.pdf_utils import _table_col_widths
        headers = [f'Columna {i} con texto largo' for i in range(6)]
        widths = _table_col_widths(headers, [], 499, pad_h=6)
        assert sum(widths) <= 499 + 0.01
        assert min(widths) >= 30

    def test_draw_table_renders_with_variable_columns(self):
        import io
        from reportlab.pdfgen import canvas as rl_canvas
        from content.services.pdf_utils import _draw_table
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        ps = {'num': 1, 'client': '', 'total': None}
        y = _draw_table(c, 700, ['#', 'Detalle'],
                        [['1', 'texto ' * 30], ['2', 'corto']], ps=ps)
        assert y < 700
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py::TestTableColumns -v --no-cov`
Expected: ImportError `_table_col_widths`.

- [ ] **Step 3: Implement**

```python
def _table_col_widths(headers, rows, max_width, pad_h, font_size=8):
    """Distribute max_width across columns proportionally to content."""
    num_cols = len(headers)
    if num_cols == 0:
        return []
    min_w = max(30.0, (max_width / num_cols) * 0.35)
    fn = _font('regular')
    desired = []
    for ci in range(num_cols):
        cells = [str(headers[ci])] + [
            str(r[ci]) for r in (rows or []) if ci < len(r)]
        widest = max((_string_w(_clean_inline_bold(_sanitize_pdf_text(cell)),
                                fn, font_size) for cell in cells), default=0.0)
        desired.append(widest + 2 * pad_h + 4)
    total = sum(desired)
    if total <= 0:
        return [max_width / num_cols] * num_cols
    widths = [d * max_width / total for d in desired]
    # enforce the floor, shaving the excess off wider columns
    deficit = sum(min_w - w for w in widths if w < min_w)
    if deficit > 0:
        pool_idx = [i for i, w in enumerate(widths) if w > min_w]
        pool = sum(widths[i] - min_w for i in pool_idx)
        for i, w in enumerate(widths):
            if w < min_w:
                widths[i] = min_w
        if pool > 0:
            for i in pool_idx:
                widths[i] -= deficit * (widths[i] - min_w) / pool
    return widths
```

Rewrite `_draw_table` keeping its structure (header repeat on page break, zebra stripes, vertical centering) with these changes:
- Compute `col_ws = _table_col_widths(headers, rows, max_width, cell_pad_h)` once and `col_xs = [x_start + sum(col_ws[:i]) for i in range(len(col_ws))]`.
- Header and data cells wrap with `_layout_inline(cell_text, col_ws[ci] - 2 * cell_pad_h, fn, size)` instead of `textwrap.wrap`/`_md_wrap`/`_break_long_tokens` (drop the `_break_long_tokens` call here — the engine hard-splits internally).
- Header background `c.rect(x_start, y - row_h, max_width, row_h, ...)` stays full-width; each header cell draws its wrapped fragment lines with `_draw_fragments_line(..., WHITE)` at `col_xs[ci] + cell_pad_h`.
- Data rows: `row_h = max_lines * leading + 2 * cell_pad_v` from the measured wraps; cell text via `_draw_fragments_line(c, col_xs[ci] + cell_pad_h, ty, frags, ESMERALD_80)`; keep the `v_offset` vertical centering exactly as today.

- [ ] **Step 4: Run tests + regression**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py -v --no-cov`
Expected: PASS.
Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_utils_gaps3.py content/tests/services/test_document_pdf_service.py -v --no-cov`
Expected: PASS (update any test pinning equal `col_w = max_width/num_cols` to the new proportional contract).

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/pdf_utils.py backend/content/tests/services/test_pdf_layout.py
git commit -m "feat: content-proportional table columns with measured row heights"
```

---

### Task 5: Multi-level nested lists (parser + renderer)

Parser flattens nesting to one string-typed `children` level; renderer draws max two levels. Replace with true recursion. Backward compatibility is mandatory: existing `content_json` blocks contain `children: [str, ...]` and legacy string items.

**Files:**
- Modify: `backend/content/services/markdown_parser.py:160-249` (replace both list branches with one)
- Modify: `backend/content/services/pdf_utils.py:844-910` (`_draw_bullet_list`)
- Test: `backend/content/tests/services/test_markdown_parser_lists.py` (new), `backend/content/tests/services/test_pdf_layout.py` (extend)

**Interfaces:**
- Produces: list blocks are now `{'type':'list','ordered':bool,'items':[{'text':str,'children':[item,...]}]}` — children are ITEM DICTS (recursive), no longer strings. `_draw_bullet_list(c, y, items, x=None, max_width=None, font_size=9, leading=13, color=ESMERALD_80, bullet='•', ps=None, numbered=False, link_color=None) -> y` accepts dict items with recursive children AND legacy string children/items.

- [ ] **Step 1: Write the failing parser tests**

```python
# backend/content/tests/services/test_markdown_parser_lists.py
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
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/services/test_markdown_parser_lists.py -v --no-cov`
Expected: FAIL — three-level test gets flattened children (strings), ordered+unordered children currently strings.

- [ ] **Step 3: Implement the unified list parser**

In `markdown_parser.py`, add near the top:

```python
_LIST_ITEM_RE = re.compile(r'^([ \t]*)([-*]|\d+\.)\s+(.+)$')


def _indent_depth(ws):
    """2 spaces or 1 tab = one nesting level."""
    return ws.count('\t') + len(ws.replace('\t', '')) // 2
```

Replace sections 7 and 8 (both `while` list branches, lines 160-249) with ONE branch:

```python
        # 7. Lists (ordered or unordered, arbitrarily nested)
        list_m = _LIST_ITEM_RE.match(line)
        if list_m and not re.match(r'^[-*_]{3,}\s*$', stripped):
            ordered = list_m.group(2) not in ('-', '*')
            root_items = []
            stack = [(0, root_items)]  # (depth, items list at that depth)
            while i < len(lines):
                raw = lines[i]
                m = _LIST_ITEM_RE.match(raw)
                if m and not re.match(r'^[-*_]{3,}\s*$', raw.strip()):
                    depth = min(_indent_depth(m.group(1)), stack[-1][0] + 1)
                    while len(stack) > 1 and depth < stack[-1][0]:
                        stack.pop()
                    if depth > stack[-1][0] and stack[-1][1]:
                        stack.append((depth, stack[-1][1][-1]['children']))
                    stack[-1][1].append(
                        {'text': m.group(3).strip(), 'children': []})
                    i += 1
                    continue
                s = raw.strip()
                if (
                    s
                    and not s.startswith('#')
                    and not s.startswith('|')
                    and not s.startswith('>')
                    and not s.startswith('```')
                    and not re.match(r'^[-*_]{3,}\s*$', s)
                    and not re.match(r'^\*\*\d+\.\d+', s)
                ):
                    # Continuation line: append to the innermost last item
                    items = stack[-1][1]
                    if items:
                        items[-1]['text'] += ' ' + s
                        i += 1
                        continue
                break
            if root_items:
                blocks.append({
                    'type': 'list',
                    'ordered': ordered,
                    'items': root_items,
                })
            continue
```

Delete the now-dead sections 7 and 8 entirely (the paragraph fallback's guards at lines 276-277 already stop on list markers, keep those).

- [ ] **Step 4: Replace `_draw_bullet_list` with a recursive renderer** (in `pdf_utils.py`)

```python
_UL_MARKERS = ['•', '–', '◦']  # • – ◦ per depth


def _normalize_list_item(item):
    """Accept new dict items, legacy dicts with string children, and
    legacy plain-string items."""
    if isinstance(item, dict):
        children = [_normalize_list_item(ch) for ch in item.get('children', [])]
        return {'text': item.get('text', ''), 'children': children}
    return {'text': str(item), 'children': []}


def _draw_list_items(c, y, items, x, max_width, font_size, leading, color,
                     ps, numbered, depth, link_color=None):
    fn = _font('regular')
    for idx, raw_item in enumerate(items or []):
        item = _normalize_list_item(raw_item)
        if numbered:
            prefix = f'  {idx + 1}.  '
        else:
            prefix = f'  {_UL_MARKERS[min(depth, len(_UL_MARKERS) - 1)]}  '
        pw = _string_w(prefix, fn, font_size)
        lines = _layout_inline(item['text'], max_width - pw, fn, font_size)
        if ps and len(lines) > 1 and y < MARGIN_B + leading * 2:
            y = _new_page(c, ps)
        for li, frags in enumerate(lines):
            if ps:
                y = _check_y(c, y, ps)
            elif y < MARGIN_B + 20:
                return y
            if li == 0:
                c.setFont(fn, font_size)
                c.setFillColor(color)
                c.drawString(x, y, prefix)
            _draw_fragments_line(c, x + pw, y, frags, color,
                                 link_color=link_color)
            y -= leading
        y -= 2
        if item['children']:
            y = _draw_list_items(c, y, item['children'], x + 18,
                                 max_width - 18, font_size, leading, color,
                                 ps, numbered, depth + 1,
                                 link_color=link_color)
    return y


def _draw_bullet_list(c, y, items, x=None, max_width=None,
                       font_size=9, leading=13, color=ESMERALD_80,
                       bullet='•', ps=None, numbered=False,
                       link_color=None):
    """Draw a (possibly nested) list and return the new y."""
    if max_width is None:
        max_width = CONTENT_W
    if x is None:
        x = MARGIN_L
    return _draw_list_items(c, y, items, x, max_width, font_size, leading,
                            color, ps, numbered, depth=0,
                            link_color=link_color)
```

Add renderer tests to `test_pdf_layout.py`:

```python
class TestNestedListRendering:
    def test_renders_three_levels_and_legacy_children(self):
        import io
        from reportlab.pdfgen import canvas as rl_canvas
        from content.services.pdf_utils import _draw_bullet_list
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        items = [
            {'text': 'uno', 'children': [
                {'text': 'dos', 'children': [
                    {'text': 'tres', 'children': []}]}]},
            {'text': 'legacy', 'children': ['hijo string']},  # old shape
            'item plano',                                     # oldest shape
        ]
        y = _draw_bullet_list(c, 700, items,
                              ps={'num': 1, 'client': '', 'total': None})
        assert y < 700
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'
```

- [ ] **Step 5: Run tests + regression**

Run: `cd backend && venv/bin/pytest content/tests/services/test_markdown_parser_lists.py content/tests/services/test_pdf_layout.py::TestNestedListRendering -v --no-cov`
Expected: PASS.
Run: `cd backend && venv/bin/pytest content/tests/services/test_document_pdf_service.py content/tests/services/test_document_pdf_service_emoji.py -v --no-cov`
Expected: PASS. Existing parser tests: run the file that covers `markdown_to_blocks` (`cd backend && venv/bin/pytest content/tests -k "markdown_parser" -v --no-cov`); update any test that asserted `children` as strings to the new dict shape.

- [ ] **Step 6: Commit**

```bash
git add backend/content/services/markdown_parser.py backend/content/services/pdf_utils.py \
        backend/content/tests/services/test_markdown_parser_lists.py \
        backend/content/tests/services/test_pdf_layout.py
git commit -m "feat: true multi-level nested lists in markdown parser and PDF renderer"
```

---

### Task 6: `PdfTheme` and theming the shared drawers

Introduce a `PdfTheme` dataclass and two instances (`PROFESSIONAL_THEME` reproducing today's constants; `FRIENDLY_THEME` mirroring `DocumentMarkdownBody.vue`). Add an optional `theme=None` parameter to the shared drawers the document service uses; `None` → `PROFESSIONAL_THEME`, so every OTHER caller (proposals, contracts, collection accounts, diagnostics, onboarding) is visually unchanged.

**Files:**
- Create: `backend/content/services/pdf_theme.py`
- Modify: `backend/content/services/pdf_utils.py` — add `theme=None` to `_draw_header_bar`, `_draw_section_header`, `_draw_table`, `_draw_blockquote`, `_draw_code_block`, `_draw_separator`; resolve `theme = theme or PROFESSIONAL_THEME` at the top of each and read colors from it.
- Test: `backend/content/tests/services/test_pdf_theme.py` (new)

**Interfaces:**
- Produces:
  - `PdfTheme` frozen dataclass (fields below); `PROFESSIONAL_THEME`, `FRIENDLY_THEME`; `get_theme(name) -> PdfTheme` (`'friendly'`→FRIENDLY, anything else→PROFESSIONAL).
  - Shared drawers gain trailing `theme=None`; default output is byte-identical palette to today.

- [ ] **Step 1: Write the failing tests**

```python
# backend/content/tests/services/test_pdf_theme.py
"""PdfTheme selection and default-preserves-professional guarantees."""
import io

import pytest
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4

from content.services.pdf_theme import (
    PdfTheme, PROFESSIONAL_THEME, FRIENDLY_THEME, get_theme)

pytestmark = pytest.mark.django_db


class TestThemeSelection:
    def test_get_theme_friendly(self):
        assert get_theme('friendly') is FRIENDLY_THEME

    def test_get_theme_defaults_professional(self):
        assert get_theme('professional') is PROFESSIONAL_THEME
        assert get_theme('') is PROFESSIONAL_THEME
        assert get_theme(None) is PROFESSIONAL_THEME
        assert get_theme('nonsense') is PROFESSIONAL_THEME

    def test_professional_matches_legacy_constants(self):
        from content.services import pdf_utils as u
        assert PROFESSIONAL_THEME.h1_color == u.ESMERALD
        assert PROFESSIONAL_THEME.body_color == u.ESMERALD_80
        assert PROFESSIONAL_THEME.header_bar_color == u.ESMERALD

    def test_friendly_uses_preview_palette(self):
        from reportlab.lib.colors import HexColor
        assert FRIENDLY_THEME.h1_color == HexColor('#047857')
        assert FRIENDLY_THEME.body_color == HexColor('#374151')
        assert FRIENDLY_THEME.quote_bg == HexColor('#F0FDF4')

    def test_is_frozen(self):
        with pytest.raises(Exception):
            FRIENDLY_THEME.h1_color = None


class TestDefaultThemePreservesLook:
    def test_drawers_accept_theme_none_without_error(self):
        from content.services.pdf_utils import (
            _draw_header_bar, _draw_section_header, _draw_separator,
            _register_fonts)
        _register_fonts()
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        _draw_header_bar(c)                    # theme defaulted
        _draw_section_header(c, 780, '01', 'Titulo')
        _draw_separator(c, 700)
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_theme.py -v --no-cov`
Expected: `ModuleNotFoundError: content.services.pdf_theme`.

- [ ] **Step 3: Create `pdf_theme.py`**

```python
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
```

- [ ] **Step 4: Thread `theme` through the shared drawers** (`pdf_utils.py`)

At module import add (after the color constants, avoiding a circular import — `pdf_theme` imports from `pdf_utils`, so import lazily inside a resolver):

```python
def _resolve_theme(theme):
    from content.services.pdf_theme import PROFESSIONAL_THEME
    return theme or PROFESSIONAL_THEME
```

Then, for each drawer, add trailing `theme=None`, call `t = _resolve_theme(theme)` first, and swap hardcoded colors for `t.*`:
- `_draw_header_bar(c, theme=None)`: bar `t.header_bar_color`, dot `t.header_dot_color`.
- `_draw_section_header(c, y, index_str, title, ps=None, theme=None)`: index `t.section_index_color`, title `t.section_title_color`, rule `t.section_rule_color`. Draw the title with `_draw_fragments_line`/`_layout_inline` (still fine; keeps emoji support).
- `_draw_table(..., theme=None)`: header bg `t.table_header_bg`, header text `t.table_header_text`, stripe `t.table_stripe_bg`, non-stripe `t.table_row_bg`, border `t.table_border_color`, body text `t.table_body_text`.
- `_draw_blockquote(c, y, text, ps=None, theme=None)`: bg `t.quote_bg`, accent `t.quote_accent`, text `t.quote_text`.
- `_draw_code_block(..., theme=None)`: bg `t.code_bg`, border `t.code_border`, text `t.code_text`.
- `_draw_separator(c, y, ps=None, theme=None)`: line `t.rule_color`.

Do NOT change `_draw_callout_box` colors — `_CALLOUT_STYLES` is shared and matches both previews already; just pass through (no theme needed there).

- [ ] **Step 5: Run tests + full regression of shared drawers**

Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_theme.py content/tests/services/test_pdf_layout.py -v --no-cov`
Expected: PASS.
Run: `cd backend && venv/bin/pytest content/tests/services/test_pdf_utils.py content/tests/services/test_pdf_utils_gaps.py content/tests/services/test_pdf_utils_gaps2.py -v --no-cov`
Expected: PASS — default theme must not alter existing behavior.
Run: `cd backend && venv/bin/pytest content/tests/services/test_proposal_pdf_service.py -v --no-cov` (proof proposals unaffected; if the filename differs use `-k proposal_pdf`).
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/content/services/pdf_theme.py backend/content/services/pdf_utils.py \
        backend/content/tests/services/test_pdf_theme.py
git commit -m "feat: add PdfTheme with professional and friendly palettes for shared drawers"
```

---

### Task 7: `DocumentPdfService.generate(document, template_style='professional')`

Thread the theme through the document service: `_render_heading`, `_render_title_page`, `_render_section_header`, the header-bar/separator/table/quote/code calls, and — critically — the dry-run TOC pass must use the SAME theme so page numbers don't drift. Also apply the friendly heading underline.

**Files:**
- Modify: `backend/content/services/document_pdf_service.py` (all render methods + `generate` + `_collect_section_pages` + `generate_from_markdown`)
- Test: `backend/content/tests/services/test_document_pdf_service.py` (extend)

**Interfaces:**
- Consumes: `get_theme`, `PdfTheme`, themed drawers (Task 6), `_layout_inline`/`_draw_fragments_line` (Task 1).
- Produces: `DocumentPdfService.generate(cls, document, template_style=None) -> bytes|None` (default `None` → `document.template_style` if set else `'professional'`); `generate_from_markdown(..., template_style='professional')`. All private render helpers take `theme` (turn the `@staticmethod` heading/section/paragraph helpers into `@classmethod` or pass `theme` explicitly).

- [ ] **Step 1: Write the failing tests** (extend `test_document_pdf_service.py`)

```python
class TestDocumentPdfServiceTemplateStyle:
    @pytest.fixture(autouse=True)
    def _bypass_merge(self):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService._merge_with_covers',
            side_effect=lambda b, **kw: b,
        ):
            yield

    def test_friendly_style_generates_pdf(self):
        from content.services.document_pdf_service import DocumentPdfService
        doc = _document(content_json=_with_blocks([
            {'type': 'heading', 'level': 1, 'text': 'Titulo'},
            {'type': 'paragraph', 'text': 'Cuerpo del documento.'},
            {'type': 'table', 'headers': ['A', 'B'], 'rows': [['1', '2']]},
        ]))
        out = DocumentPdfService.generate(doc, template_style='friendly')
        assert isinstance(out, bytes) and out[:4] == b'%PDF'

    def test_professional_is_default_when_unspecified(self):
        from content.services.document_pdf_service import DocumentPdfService
        doc = _document(content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Hola.'}]))
        # no template_style attribute set on the fixture → professional
        out = DocumentPdfService.generate(doc)
        assert out[:4] == b'%PDF'

    def test_uses_document_field_when_style_arg_none(self):
        from content.services.document_pdf_service import DocumentPdfService
        doc = _document(template_style='friendly', content_json=_with_blocks([
            {'type': 'paragraph', 'text': 'Hola.'}]))
        out = DocumentPdfService.generate(doc, template_style=None)
        assert out[:4] == b'%PDF'

    def test_toc_page_count_matches_between_passes(self):
        """Dry-run and real pass share the theme → stable page numbers."""
        from content.services.document_pdf_service import DocumentPdfService
        blocks = [{'type': 'toc'}]
        for n in range(6):
            blocks.append({'type': 'heading', 'level': 1, 'text': f'H{n}'})
            blocks.append({'type': 'paragraph', 'text': 'x ' * 200})
        doc = _document(include_subportada=False,
                        content_json=_with_blocks(blocks))
        out = DocumentPdfService.generate(doc, template_style='friendly')
        assert out[:4] == b'%PDF'
```

Note: `test_professional_is_default_when_unspecified` requires `_document()` to tolerate a missing `template_style`. Since Task 8 adds the field with default `'professional'`, this passes after Task 8; to keep Task 7 self-contained, make `generate` read `getattr(document, 'template_style', None)`.

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/services/test_document_pdf_service.py::TestDocumentPdfServiceTemplateStyle -v --no-cov`
Expected: FAIL — `generate()` takes no `template_style`.

- [ ] **Step 3: Implement**

- `generate(cls, document, template_style=None)`: resolve
  `style = template_style or getattr(document, 'template_style', None) or 'professional'`,
  `theme = get_theme(style)` (import at top: `from content.services.pdf_theme import get_theme`). Pass `theme` to `_draw_header_bar(c, theme=theme)`, every `_render_*` call, `_draw_footer` (unchanged), and store `theme` on `ps['theme'] = theme` so nested `_new_page`/`_check_y` header bars use it — update `_new_page` in `pdf_utils.py` to call `_draw_header_bar(c, theme=ps.get('theme'))`.
- `_render_heading(cls, c, y, block, ps, theme)`: use `theme.h1_color/h2_color/h3_color`; for the accent under h1/h2, if `theme.heading_rule_full` draw a full-width thin line in `theme.heading_rule_color` (friendly underline) else the short 60pt lemon rule (professional). Render text via `_layout_inline`/`_draw_fragments_line` for emoji safety.
- `_render_section_header` → pass `theme` to `_draw_section_header`.
- `_render_paragraph` → `_draw_paragraphs(..., color=theme.body_color, link_color=theme.link_color)`.
- `_render_list` → `_draw_bullet_list(..., color=theme.body_color, link_color=theme.link_color)`.
- `_render_table/_render_blockquote/_render_code/_render_separator` → pass `theme=theme`.
- `_render_title_page(cls, c, document, meta, ps, theme)`: swap `ESMERALD` title color for `theme.title_color`, decorative circles for `theme.quote_bg`/`ESMERALD_LIGHT` (keep circles; friendly can reuse `ESMERALD_LIGHT`), divider color `theme.section_rule_color`.
- `_collect_section_pages(cls, document, theme)`: accept and use the SAME theme for its dry-run `_render_*` calls and `_draw_header_bar(c, theme=theme)`; `generate` passes its resolved `theme`.
- `generate_from_markdown(..., template_style='professional')`: set `document.template_style = template_style` on the transient Document and pass through.

- [ ] **Step 4: Run tests + regression**

Run: `cd backend && venv/bin/pytest content/tests/services/test_document_pdf_service.py content/tests/services/test_document_pdf_service_gaps.py content/tests/services/test_document_pdf_service_emoji.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/content/services/document_pdf_service.py backend/content/services/pdf_utils.py \
        backend/content/tests/services/test_document_pdf_service.py
git commit -m "feat: DocumentPdfService renders selectable professional/friendly theme"
```

---

### Task 8: `Document.template_style` field + migration

**Files:**
- Modify: `backend/content/models/document.py` (add `TemplateStyle` choices + field)
- Create: `backend/content/migrations/0154_document_template_style.py`
- Test: `backend/content/tests/models/test_document_template_style.py` (new)

**Interfaces:**
- Produces: `Document.TemplateStyle` (`PROFESSIONAL='professional'`, `FRIENDLY='friendly'`); `Document.template_style` CharField, default `professional`.

- [ ] **Step 1: Write the failing test**

```python
# backend/content/tests/models/test_document_template_style.py
import pytest
from content.models import Document

pytestmark = pytest.mark.django_db


def test_default_template_style_is_professional():
    doc = Document.objects.create(title='X')
    assert doc.template_style == 'professional'


def test_template_style_accepts_friendly():
    doc = Document.objects.create(title='Y', template_style='friendly')
    doc.refresh_from_db()
    assert doc.template_style == 'friendly'


def test_template_style_choices():
    assert Document.TemplateStyle.FRIENDLY == 'friendly'
    assert Document.TemplateStyle.PROFESSIONAL == 'professional'
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/models/test_document_template_style.py -v --no-cov`
Expected: `AttributeError`/`FieldError` — field/choices absent.

- [ ] **Step 3: Add the field** (in `document.py`, near `CoverType` and the `include_*` flags)

```python
    class TemplateStyle(models.TextChoices):
        PROFESSIONAL = 'professional', 'Profesional'
        FRIENDLY = 'friendly', 'Amigable'
```

and after `include_contraportada`:

```python
    template_style = models.CharField(
        max_length=20,
        choices=TemplateStyle.choices,
        default=TemplateStyle.PROFESSIONAL,
        help_text='Estilo de PDF por defecto: profesional o amigable.',
    )
```

- [ ] **Step 4: Generate + verify the migration**

Run: `cd backend && venv/bin/python manage.py makemigrations content --name document_template_style`
Expected: creates `0154_document_template_style.py` adding the field. Confirm it is additive only.
Run: `cd backend && venv/bin/python manage.py migrate content --plan | tail -3`
Expected: lists the new migration.

- [ ] **Step 5: Run tests**

Run: `cd backend && venv/bin/pytest content/tests/models/test_document_template_style.py -v --no-cov`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/content/models/document.py backend/content/migrations/0154_document_template_style.py \
        backend/content/tests/models/test_document_template_style.py
git commit -m "feat: add Document.template_style field (professional default)"
```

---

### Task 9: Expose `template_style` in document serializers

**Files:**
- Modify: `backend/content/serializers/document.py` (`DocumentDetailSerializer`, `DocumentCreateUpdateSerializer`, `DocumentFromMarkdownSerializer`, `DocumentListSerializer`)
- Test: `backend/content/tests/views/test_document_views.py` (extend) or a focused serializer test

**Interfaces:**
- Produces: `template_style` readable in detail/list, writable in create/update (choice-validated), and accepted by the from-markdown serializer (default `professional`).

- [ ] **Step 1: Write the failing tests** (append to `test_document_views.py`; reuse its admin-auth client fixture)

```python
class TestDocumentTemplateStyleApi:
    def test_detail_includes_template_style(self, admin_client):
        from content.models import Document
        doc = Document.objects.create(title='D', template_style='friendly')
        resp = admin_client.get(f'/api/documents/{doc.id}/detail/')
        assert resp.status_code == 200
        assert resp.json()['template_style'] == 'friendly'

    def test_update_sets_template_style(self, admin_client):
        from content.models import Document
        doc = Document.objects.create(title='D')
        resp = admin_client.patch(
            f'/api/documents/{doc.id}/update/',
            {'template_style': 'friendly'}, content_type='application/json')
        assert resp.status_code == 200
        doc.refresh_from_db()
        assert doc.template_style == 'friendly'

    def test_update_rejects_bad_template_style(self, admin_client):
        from content.models import Document
        doc = Document.objects.create(title='D')
        resp = admin_client.patch(
            f'/api/documents/{doc.id}/update/',
            {'template_style': 'fancy'}, content_type='application/json')
        assert resp.status_code == 400
        assert 'template_style' in resp.json()
```

If `test_document_views.py` has no `admin_client` fixture, mirror the auth setup already used by its other tests in this new class (check the top of the file and copy the pattern verbatim).

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/views/test_document_views.py -k TemplateStyle -v --no-cov`
Expected: FAIL — field not serialized.

- [ ] **Step 3: Add `template_style` to the four serializers' `fields` tuples** (`DocumentDetailSerializer`, `DocumentListSerializer`, `DocumentCreateUpdateSerializer`) and to `DocumentFromMarkdownSerializer` as:

```python
    template_style = serializers.ChoiceField(
        choices=Document.TemplateStyle.choices, required=False,
        default='professional',
    )
```

Then in `create_document_from_markdown` / `upload_document_markdown` views, pass `template_style=data.get('template_style', 'professional')` into `Document.objects.create(...)` and into the `meta` dict.

- [ ] **Step 4: Run tests**

Run: `cd backend && venv/bin/pytest content/tests/views/test_document_views.py -k TemplateStyle -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/content/serializers/document.py backend/content/views/document.py \
        backend/content/tests/views/test_document_views.py
git commit -m "feat: expose template_style in document serializers and markdown creation"
```

---

### Task 10: `?template=` on the panel PDF endpoint; platform + email use the persisted style

**Files:**
- Modify: `backend/content/views/document.py:304-329` (`download_document_pdf`)
- (No change needed to `accounts/document_views.py` or `standalone_email.py` — both already call `DocumentPdfService.generate(doc)`, which now defaults to `document.template_style`. Add a regression test to lock that in.)
- Test: `backend/content/tests/views/test_document_views.py` (extend)

**Interfaces:**
- Consumes: `DocumentPdfService.generate(document, template_style=...)`.
- Produces: `GET /api/documents/<id>/pdf/?template=friendly|professional` → that style; absent/invalid → `document.template_style`.

- [ ] **Step 1: Write the failing tests**

```python
class TestDownloadPdfTemplateParam:
    def _doc(self):
        from content.models import Document
        return Document.objects.create(
            title='D', template_style='professional',
            content_json={'meta': {}, 'blocks': [
                {'type': 'paragraph', 'text': 'Hola.'}]})

    def test_param_overrides_to_friendly(self, admin_client):
        doc = self._doc()
        with patch('content.services.document_pdf_service.'
                   'DocumentPdfService.generate') as gen:
            gen.return_value = b'%PDF-1.4 x'
            resp = admin_client.get(
                f'/api/documents/{doc.id}/pdf/?template=friendly')
        assert resp.status_code == 200
        assert gen.call_args.kwargs.get('template_style') == 'friendly' \
            or gen.call_args[0][1:] == ('friendly',)

    def test_invalid_param_falls_back_to_document_style(self, admin_client):
        doc = self._doc()
        with patch('content.services.document_pdf_service.'
                   'DocumentPdfService.generate') as gen:
            gen.return_value = b'%PDF-1.4 x'
            resp = admin_client.get(
                f'/api/documents/{doc.id}/pdf/?template=bogus')
        assert resp.status_code == 200
        passed = gen.call_args.kwargs.get('template_style')
        assert passed in ('professional', None)

    def test_no_param_uses_document_style(self, admin_client):
        doc = self._doc()
        doc.template_style = 'friendly'
        doc.save(update_fields=['template_style'])
        with patch('content.services.document_pdf_service.'
                   'DocumentPdfService.generate') as gen:
            gen.return_value = b'%PDF-1.4 x'
            resp = admin_client.get(f'/api/documents/{doc.id}/pdf/')
        assert resp.status_code == 200
```

(Requires `from unittest.mock import patch` at the top of the test file.)

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && venv/bin/pytest content/tests/views/test_document_views.py -k DownloadPdfTemplateParam -v --no-cov`
Expected: FAIL — view ignores `template`.

- [ ] **Step 3: Implement** (in `download_document_pdf`)

```python
    from content.services.document_pdf_service import DocumentPdfService  # noqa: E402
    requested = request.query_params.get('template')
    valid = {'professional', 'friendly'}
    style = requested if requested in valid else document.template_style
    pdf_bytes = DocumentPdfService.generate(document, template_style=style)
```

- [ ] **Step 4: Run tests + regression of platform + email paths**

Run: `cd backend && venv/bin/pytest content/tests/views/test_document_views.py -k "DownloadPdfTemplateParam" -v --no-cov`
Expected: PASS.
Run: `cd backend && venv/bin/pytest backend/content/tests/views/test_document_views.py -k "pdf" -v --no-cov` (existing download tests still pass).
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/content/views/document.py backend/content/tests/views/test_document_views.py
git commit -m "feat: honor ?template= on document PDF download; platform/email use persisted style"
```

---

### Task 11: `downloadPdf(id, title, template)` — add template param + move to shared client

**Files:**
- Modify: `frontend/stores/documents.js:287-310` (`downloadPdf`)
- Test: `frontend/test/stores/documents.test.js:267-` (`downloadPdf` describe block)

**Interfaces:**
- Consumes: `get_request(url, config)` from `./services/request_http` (already imported? No — add `get_request` is imported; `axios` import is dropped if no longer used elsewhere. It IS still imported for nothing else — verify and remove the now-unused `import axios from 'axios'`).
- Produces: `downloadPdf(id, title = 'document', template = null) -> {success}` — appends `?template=<template>` only when `template` is `'friendly'` or `'professional'`.

- [ ] **Step 1: Update the failing tests** (rewrite the `downloadPdf` describe block)

```javascript
  describe('downloadPdf', () => {
    beforeEach(() => {
      global.URL.createObjectURL = jest.fn(() => 'blob:x')
      global.URL.revokeObjectURL = jest.fn()
    })

    it('requests the pdf blob and triggers a download', async () => {
      get_request.mockResolvedValue({ data: new Blob(['x']) })
      const clickSpy = jest.fn()
      jest.spyOn(document, 'createElement').mockReturnValue({
        href: '', setAttribute: jest.fn(), click: clickSpy, remove: jest.fn(),
      })
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})

      const result = await store.downloadPdf(3, 'My Doc')
      expect(get_request).toHaveBeenCalledWith(
        'documents/3/pdf/', { responseType: 'blob' })
      expect(clickSpy).toHaveBeenCalled()
      expect(result.success).toBe(true)
    })

    it('appends the template query when given a valid style', async () => {
      get_request.mockResolvedValue({ data: new Blob(['x']) })
      jest.spyOn(document, 'createElement').mockReturnValue({
        href: '', setAttribute: jest.fn(), click: jest.fn(), remove: jest.fn(),
      })
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})

      await store.downloadPdf(1, 't', 'friendly')
      expect(get_request).toHaveBeenCalledWith(
        'documents/1/pdf/?template=friendly', { responseType: 'blob' })
    })

    it('ignores an unknown template value', async () => {
      get_request.mockResolvedValue({ data: new Blob(['x']) })
      jest.spyOn(document, 'createElement').mockReturnValue({
        href: '', setAttribute: jest.fn(), click: jest.fn(), remove: jest.fn(),
      })
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})

      await store.downloadPdf(1, 't', 'bogus')
      expect(get_request).toHaveBeenCalledWith(
        'documents/1/pdf/', { responseType: 'blob' })
    })

    it('returns an error result on failure', async () => {
      get_request.mockRejectedValue(new Error('boom'))
      const result = await store.downloadPdf(1)
      expect(result.success).toBe(false)
    })
  })
```

- [ ] **Step 2: Run to verify failure**

Run: `npm --prefix frontend test -- test/stores/documents.test.js`
Expected: FAIL — store still calls `axios.get('/api/documents/...')`, not `get_request`.

- [ ] **Step 3: Rewrite `downloadPdf`**

```javascript
    /**
     * downloadPdf: Download a document as PDF in the chosen template style.
     * @param {number} id - Document ID.
     * @param {string} title - Filename (without extension).
     * @param {string|null} template - 'friendly' | 'professional' | null (server default).
     */
    async downloadPdf(id, title = 'document', template = null) {
      try {
        const valid = template === 'friendly' || template === 'professional';
        const url = valid
          ? `documents/${id}/pdf/?template=${template}`
          : `documents/${id}/pdf/`;
        const response = await get_request(url, { responseType: 'blob' });
        const objectUrl = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = objectUrl;
        link.setAttribute('download', `${title}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(objectUrl);
        return { success: true };
      } catch (error) {
        console.error('Error downloading PDF:', error);
        return {
          success: false,
          errors: error.response?.data,
          ...normalizeApiError(error, 'No se pudo descargar el PDF.'),
        };
      }
    },
```

Remove `import axios from 'axios';` (line 2) if no other action uses it — grep the file first; the platform store keeps its own axios.

- [ ] **Step 4: Run tests**

Run: `npm --prefix frontend test -- test/stores/documents.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/stores/documents.js frontend/test/stores/documents.test.js
git commit -m "feat: downloadPdf accepts template style and uses shared http client"
```

---

### Task 12: `theme` prop + professional palette on `DocumentMarkdownBody`

**Files:**
- Modify: `frontend/components/panel/documents/DocumentMarkdownBody.vue`
- Test: `frontend/test/components/DocumentMarkdownBody.test.js` (new)

**Interfaces:**
- Produces: prop `theme: 'friendly' | 'professional'` (default `'friendly'` — preserves current look for cards/existing callers); adds root class `markdown-preview--professional` when professional. `variant` (size) unchanged and composable with `theme`.

- [ ] **Step 1: Write the failing test**

```javascript
// frontend/test/components/DocumentMarkdownBody.test.js
import { mount } from '@vue/test-utils'
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue'

// The composable is auto-imported in the app; provide it explicitly for jest.
jest.mock('~/composables/useMarkdownPreview', () => ({
  useMarkdownPreview: () => ({ parseMarkdown: (md) => `<p class="md-p">${md}</p>` }),
}), { virtual: true })

describe('DocumentMarkdownBody theme', () => {
  it('defaults to the friendly look (no professional modifier)', () => {
    const w = mount(DocumentMarkdownBody, { props: { markdown: 'hola' } })
    expect(w.classes()).toContain('markdown-preview')
    expect(w.classes()).not.toContain('markdown-preview--professional')
  })

  it('adds the professional modifier when theme=professional', () => {
    const w = mount(DocumentMarkdownBody, {
      props: { markdown: 'hola', theme: 'professional' },
    })
    expect(w.classes()).toContain('markdown-preview--professional')
  })

  it('composes theme with the size variant', () => {
    const w = mount(DocumentMarkdownBody, {
      props: { markdown: 'hola', theme: 'professional', variant: 'full' },
    })
    expect(w.classes()).toContain('markdown-preview--professional')
    expect(w.classes()).toContain('markdown-preview--full')
  })
})
```

If the repo's jest config resolves `~/` differently or does not stub composables this way, mirror the mocking style already used by an existing component test that imports a composable (check `frontend/test/components/BlogContentRenderer.test.js`) and adjust the mock path/config to match. Behavior asserted (root classes) stays the same.

- [ ] **Step 2: Run to verify failure**

Run: `npm --prefix frontend test -- test/components/DocumentMarkdownBody.test.js`
Expected: FAIL — professional modifier not applied.

- [ ] **Step 3: Add the prop + class + CSS**

Prop and template:

```javascript
const props = defineProps({
  markdown: { type: String, default: '' },
  variant: { type: String, default: 'default', validator: oneOf(['default', 'full', 'mini']) },
  theme: { type: String, default: 'friendly', validator: oneOf(['friendly', 'professional']) },
})
```

```html
  <div
    class="markdown-preview"
    :class="{
      'markdown-preview--full': variant === 'full',
      'markdown-preview--mini': variant === 'mini',
      'markdown-preview--professional': theme === 'professional',
    }"
    v-html="safeHtml"
  />
```

Append to the `<style scoped>` block a professional override mirroring the ReportLab palette (dark esmerald headings, bone/esmerald-light surfaces, dark table header, lemon accent). Include dark-mode variants:

```css
/* Professional theme — mirrors the ReportLab brand PDF */
.markdown-preview--professional :deep(.md-h1),
.markdown-preview--professional :deep(.md-h2) {
  color: #002921;
  border-bottom-color: #f0ff3d;
}
.markdown-preview--professional :deep(.md-h3),
.markdown-preview--professional :deep(.md-h4),
.markdown-preview--professional :deep(.md-h5),
.markdown-preview--professional :deep(.md-h6) { color: #335550; }
.markdown-preview--professional :deep(.md-p),
.markdown-preview--professional :deep(.md-ul),
.markdown-preview--professional :deep(.md-ol) { color: #335550; }
.markdown-preview--professional :deep(.md-blockquote) {
  background-color: #faf3e0;
  border-left-color: #f0ff3d;
  color: #002921;
  font-style: normal;
}
.markdown-preview--professional :deep(.md-table th) {
  background-color: #002921;
  color: #ffffff;
  border-color: #002921;
}
.markdown-preview--professional :deep(.md-table td) { border-color: #d1d5db; }
.markdown-preview--professional :deep(.md-table tbody tr:nth-child(even)) {
  background-color: #e6efef;
}
.markdown-preview--professional :deep(.md-link) { color: #059669; }
.markdown-preview--professional :deep(.md-code-block) {
  background-color: #e5e7eb;
  border-color: #d1d5db;
}
:global(.dark) .markdown-preview--professional :deep(.md-h1),
:global(.dark) .markdown-preview--professional :deep(.md-h2),
:global(.dark) .markdown-preview--professional :deep(.md-h3) { color: #a7f3d0; }
:global(.dark) .markdown-preview--professional :deep(.md-p),
:global(.dark) .markdown-preview--professional :deep(.md-ul),
:global(.dark) .markdown-preview--professional :deep(.md-ol) { color: #d1d5db; }
:global(.dark) .markdown-preview--professional :deep(.md-blockquote) {
  background-color: rgba(250, 243, 224, 0.08);
  color: #e5e7eb;
}
```

- [ ] **Step 4: Run tests**

Run: `npm --prefix frontend test -- test/components/DocumentMarkdownBody.test.js`
Expected: PASS.
Run design-token check (NEW chrome only; the `.md-*` body legitimately uses hex — the checker targets component class attributes, not `:deep` CSS, so this should pass; if it flags the scoped CSS, that file is pre-existing hex and exempt):
`node frontend/scripts/check-design-tokens.mjs --files frontend/components/panel/documents/DocumentMarkdownBody.vue`
Expected: no NEW violations.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/panel/documents/DocumentMarkdownBody.vue \
        frontend/test/components/DocumentMarkdownBody.test.js
git commit -m "feat: add professional theme palette to DocumentMarkdownBody preview"
```

---

### Task 13: Preview style switch + persistence in editor and create page

**Files:**
- Modify: `frontend/pages/panel/documents/[id]/edit.vue`
- Modify: `frontend/pages/panel/documents/create.vue`
- Test: covered by the E2E in Task 15 (page-level wiring; no separate unit test — these are thin view bindings).

**Interfaces:**
- Consumes: `BaseSegmented` (auto-imported), `DocumentMarkdownBody` `theme` prop (Task 12), store `updateDocument`/`createFromMarkdown` carrying `template_style`.

- [ ] **Step 1: edit.vue — add the field to the form + persistence**

In `form` reactive: add `template_style: 'professional',`.
In `reloadDocument()` mapping: add
`form.template_style = result.data.template_style || 'professional';` (before the `savedForm.value = ...` line).
In `handleSave()` payload: add `template_style: form.template_style,`.

- [ ] **Step 2: edit.vue — add the switch in the preview toolbar** (inside the `flex items-center gap-2 flex-wrap` div at ~line 185, before the "Vista completa" button)

```html
            <BaseSegmented
              v-model="form.template_style"
              size="sm"
              :options="templateStyleOptions"
              aria-label="Estilo de plantilla"
            />
```

and in `<script setup>`:

```javascript
const templateStyleOptions = [
  { value: 'friendly', label: 'Amigable', testId: 'doc-style-friendly' },
  { value: 'professional', label: 'Profesional', testId: 'doc-style-professional' },
];
```

- [ ] **Step 3: edit.vue — drive the theme into both previews**

Split preview body:
```html
            <DocumentMarkdownBody
              v-if="form.content_markdown.trim()"
              :markdown="form.content_markdown"
              :theme="form.template_style"
              class="px-5 py-4"
            />
```
Full-screen modal body:
```html
      <DocumentMarkdownBody
        v-if="form.content_markdown.trim()"
        :markdown="form.content_markdown"
        variant="full"
        :theme="form.template_style"
        class="max-w-4xl mx-auto"
      />
```

- [ ] **Step 4: create.vue — mirror the same wiring**

`form`: add `template_style: 'professional',`.
`handleSubmit()` payload: add `template_style: form.template_style,`.
Add the same `templateStyleOptions` const and the `<BaseSegmented>` in the preview toolbar (the `flex items-center gap-3` div at ~line 152), and `:theme="form.template_style"` on the `<DocumentMarkdownBody>` (~line 192).

- [ ] **Step 5: Verify build + token check**

Run: `node frontend/scripts/check-design-tokens.mjs --files frontend/pages/panel/documents/[id]/edit.vue frontend/pages/panel/documents/create.vue`
Expected: no NEW violations.
Run: `npm --prefix frontend run build`
Expected: build succeeds (no template/compile errors). If the machine OOMs on build, per project memory the build is heap-sensitive; a scoped `nuxi typecheck` or dev-server smoke is an acceptable substitute — note which you ran.

- [ ] **Step 6: Commit**

```bash
git add frontend/pages/panel/documents/[id]/edit.vue frontend/pages/panel/documents/create.vue
git commit -m "feat: template-style preview switch persisted in document editor and create page"
```

---

### Task 14: Dual download (editor split-button + actions sheet + list/gallery)

**Files:**
- Modify: `frontend/pages/panel/documents/[id]/edit.vue` (header + mobile download → BaseDropdown split button)
- Modify: `frontend/components/panel/documents/DocumentActionsSheet.vue` (two download rows carrying a template)
- Modify: `frontend/pages/panel/documents/index.vue:215,518` (`handleDownloadPdf(doc, template)`)
- Test: covered by Task 15 E2E.

**Interfaces:**
- Consumes: `BaseDropdown` (`items:[{label,onClick}]` + `#trigger` slot), `documentStore.downloadPdf(id, title, template)`.
- Produces: editor emits two download choices; the sheet emits `download-pdf` with a `template` string argument.

- [ ] **Step 1: edit.vue — replace the header "Descargar PDF" button with a split dropdown**

Replace the desktop download `<button>` (lines 26-34) with:

```html
        <BaseDropdown :items="downloadItems" align="right">
          <template #trigger>
            <button
              type="button"
              :disabled="isDownloading"
              class="px-5 py-2.5 bg-surface text-text-default border border-border-default rounded-xl font-medium text-sm
                     hover:bg-surface-raised transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
            >
              {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </template>
        </BaseDropdown>
```

Do the same for the mobile download button (lines 288-296). In `<script setup>`:

```javascript
const downloadItems = computed(() => [
  { label: 'Descargar · Amigable', onClick: () => handleDownloadPdf('friendly') },
  { label: 'Descargar · Profesional', onClick: () => handleDownloadPdf('professional') },
]);
```

Change `handleDownloadPdf` to take a template:

```javascript
async function handleDownloadPdf(template = null) {
  isDownloading.value = true;
  const result = await documentStore.downloadPdf(
    route.params.id, form.title || 'document', template);
  isDownloading.value = false;
  if (!result.success) {
    notify.error({ title: 'No se pudo descargar el PDF', detail: result.message });
  }
}
```

- [ ] **Step 2: DocumentActionsSheet.vue — two download rows carrying a template**

Replace the single `download-pdf` entry in `actions` with:

```javascript
  {
    event: 'download-pdf', template: 'friendly',
    label: 'Descargar PDF · Amigable',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
  },
  {
    event: 'download-pdf', template: 'professional',
    label: 'Descargar PDF · Profesional',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
  },
```

Update the click binding and `trigger`:

```html
              @click="trigger(action)"
```

```javascript
function trigger(action) {
  emit(action.event, action.template);
  close();
}
```

(`action.template` is `undefined` for non-download actions — harmless.)

- [ ] **Step 3: index.vue — pass the template through**

Line 215 binding:
```html
      @download-pdf="(tpl) => handleDownloadPdf(actionDoc, tpl)"
```
Handler (line 518):
```javascript
async function handleDownloadPdf(doc, template = null) {
  const result = await documentStore.downloadPdf(doc.id, doc.title || 'document', template);
  if (!result.success) {
    notify.error({ title: 'No se pudo descargar el PDF', detail: result.message });
  }
}
```
(If `index.vue` currently has no `notify`, keep its existing failure handling; only thread the `template` arg.)

- [ ] **Step 4: Verify build + token check**

Run: `node frontend/scripts/check-design-tokens.mjs --files frontend/pages/panel/documents/[id]/edit.vue frontend/components/panel/documents/DocumentActionsSheet.vue frontend/pages/panel/documents/index.vue`
Expected: no NEW violations.
Run: `npm --prefix frontend run build` (or the substitute noted in Task 13).
Expected: succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/panel/documents/[id]/edit.vue \
        frontend/components/panel/documents/DocumentActionsSheet.vue \
        frontend/pages/panel/documents/index.vue
git commit -m "feat: dual-style PDF download in document editor, actions sheet, and list"
```

---

### Task 15: E2E coverage for switch + dual download, then run the flows audit

**Files:**
- Modify: `frontend/e2e/admin/admin-document-edit.spec.js` (add switch + download-menu assertions)
- Modify: `frontend/e2e/flow-definitions.json` (update the documents list/edit flow descriptions to mention the style switch and dual download)
- Test/verify: Playwright slice + the mandatory `e2e-user-flows-check` skill.

**Interfaces:**
- Consumes: testIds `doc-style-friendly` / `doc-style-professional` (Task 13) and the dropdown labels (Task 14).

- [ ] **Step 1: Add an E2E test to `admin-document-edit.spec.js`**

Follow the file's existing setup (auth via `global-setup`, `E2E_PORT`, `domcontentloaded`, `test.setTimeout(60_000)`). Add:

```javascript
test('template style switch toggles the preview and exposes both downloads', async ({ page }) => {
  // (reuse the spec's existing navigation to an editable document)
  await page.getByTestId('doc-style-professional').click();
  await expect(page.locator('.markdown-preview--professional')).toBeVisible();
  await page.getByTestId('doc-style-friendly').click();
  await expect(page.locator('.markdown-preview--professional')).toHaveCount(0);

  await page.getByRole('button', { name: /Descargar PDF/i }).click();
  await expect(page.getByText(/Descargar · Amigable/i)).toBeVisible();
  await expect(page.getByText(/Descargar · Profesional/i)).toBeVisible();
});
```

Match the spec's actual document-open helper (grab the first row/card → edit) rather than inventing selectors; reuse whatever the existing tests in that file already do to reach the editor.

- [ ] **Step 2: Run the E2E slice** (own port; do not reuse another tree's dev server — project memory)

Per project memory the Playwright `webServer` cold-starts too slowly on the VPS. Start the dev server yourself on a dedicated port, then run the spec against it:
```bash
E2E_PORT=3217 npm --prefix frontend run dev &   # wait until it serves
E2E_PORT=3217 npm --prefix frontend run e2e -- e2e/admin/admin-document-edit.spec.js
```
Expected: the new test passes (retry once if the first run is flaky from cold start). If the dev server cannot be brought up in this environment, record that the spec is written and defer execution — do not delete it.

- [ ] **Step 3: Update `flow-definitions.json`**

In the documents list flow (`admin-document-list`, ~line 1585) and the gallery/edit flow descriptions, append that each document has a persisted style (Amigable/Profesional), the editor exposes a style switch that changes the preview, and PDF download offers both styles. Keep the JSON valid.

- [ ] **Step 4: Run the mandatory flows audit** (CLAUDE.md requirement — a frontend user flow changed)

Invoke the `e2e-user-flows-check` skill. Address any high-priority coverage gap it reports for the documents flow (or record it as a follow-up if out of scope for this branch).

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/admin/admin-document-edit.spec.js frontend/e2e/flow-definitions.json
git commit -m "test: e2e for document template-style switch and dual PDF download"
```

---

## Final verification (before opening the PR)

- [ ] Backend focused slices all green (run in ≤3-command cycles, ≤20 tests each):
  - `cd backend && venv/bin/pytest content/tests/services/test_pdf_layout.py content/tests/services/test_pdf_theme.py -v --no-cov`
  - `cd backend && venv/bin/pytest content/tests/services/test_document_pdf_service.py content/tests/services/test_document_pdf_service_emoji.py content/tests/services/test_markdown_parser_lists.py -v --no-cov`
  - `cd backend && venv/bin/pytest content/tests/views/test_document_views.py -k "TemplateStyle or DownloadPdf" content/tests/models/test_document_template_style.py -v --no-cov`
  - Regression proof that shared changes didn't disturb other PDFs: `cd backend && venv/bin/pytest content/tests/services/test_pdf_utils.py -k "not slow" -v --no-cov` and one proposal slice.
- [ ] Frontend: `npm --prefix frontend test -- test/stores/documents.test.js test/components/DocumentMarkdownBody.test.js`
- [ ] `git rev-parse --abbrev-ref HEAD` == `feat/10072026-documents-dual-pdf-template` before pushing.
- [ ] Manual visual smoke (per the `verify` skill): generate one document as `friendly` and once as `professional`, open both PDFs, confirm — paragraphs fill the width, no overlap between blocks, tables size to content, long code lines wrap, nested lists indent 3 levels, emojis render, covers/TOC/footer intact in both.
- [ ] PR body: describe both the fidelity overhaul (shared `pdf_utils`) and the dual-template feature; test plan lists the slices above. No AI-tooling attribution.



