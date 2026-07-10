"""Tests for the emoji-aware PDF text pipeline (Noto Emoji runs)."""
import io

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.pdf_utils import (
    EMOJI_FONT,
    _draw_line_with_links,
    _draw_mixed_string,
    _emoji_cmap,
    _emoji_font,
    _emoji_runs,
    _font,
    _mixed_string_width,
    _register_fonts,
    _renderable_emoji,
    _sanitize_pdf_text,
    _strip_emoji,
    _visible_len,
)


def _make_canvas():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    return c, buf


@pytest.fixture(autouse=True)
def _fonts():
    _register_fonts()


# ── _emoji_runs ───────────────────────────────────────────────

class TestEmojiRuns:
    def test_splits_mixed_text_into_alternating_runs(self):
        runs = _emoji_runs('Hola 🚀 mundo')

        assert runs == [('Hola ', False), ('🚀', True), (' mundo', False)]

    def test_text_without_emoji_is_single_run(self):
        assert _emoji_runs('solo texto') == [('solo texto', False)]

    def test_emoji_only_is_single_emoji_run(self):
        assert _emoji_runs('🚀') == [('🚀', True)]


# ── _renderable_emoji / _sanitize_pdf_text ────────────────────

class TestSanitizePdfText:
    def test_keeps_renderable_emoji(self):
        result = _sanitize_pdf_text('Hello 🚀 World')

        assert '🚀' in result
        assert 'Hello' in result

    def test_keeps_html_cleanup_behavior_of_strip_emoji(self):
        result = _sanitize_pdf_text('<b>bold</b> <br/> texto')

        assert '**bold**' in result
        assert '<b>' not in result

    def test_drops_cluster_with_unglyphed_codepoint(self):
        # Find a codepoint inside the emoji ranges that the font can't draw.
        cmap = _emoji_cmap()
        missing = next(
            chr(cp) for cp in range(0x1F900, 0x1FA00) if cp not in cmap
        )

        result = _sanitize_pdf_text(f'antes {missing} después')

        assert missing not in result  # never tofu
        assert 'antes' in result and 'después' in result

    def test_drops_skin_tone_but_keeps_base_emoji(self):
        result = _sanitize_pdf_text('ok 👍🏽 listo')

        assert '👍' in result
        assert '\U0001F3FD' not in result

    def test_zwj_sequence_leaves_no_zwj_in_output(self):
        result = _sanitize_pdf_text('familia 👨‍👩‍👧 unida')

        assert '‍' not in result

    def test_falls_back_to_strip_emoji_without_font(self, monkeypatch):
        monkeypatch.setattr(
            'content.services.pdf_utils._emoji_font', lambda: None,
        )

        result = _sanitize_pdf_text('Hello 🚀 World')

        assert result == _strip_emoji('Hello 🚀 World')

    def test_returns_empty_input_unchanged(self):
        assert _sanitize_pdf_text('') == ''


# ── width and drawing primitives ──────────────────────────────

class TestMixedPrimitives:
    def test_emoji_font_is_registered(self):
        assert _emoji_font() == EMOJI_FONT

    def test_mixed_width_fast_path_matches_string_width(self):
        c, _ = _make_canvas()
        fn = _font('regular')

        assert _mixed_string_width(c, 'sin emoji', fn, 10) == c.stringWidth(
            'sin emoji', fn, 10,
        )

    def test_mixed_width_sums_runs_and_exceeds_text_only_width(self):
        c, _ = _make_canvas()
        fn = _font('regular')

        with_emoji = _mixed_string_width(c, 'Hola 🚀', fn, 10)
        text_only = c.stringWidth('Hola ', fn, 10)

        assert with_emoji > text_only
        assert with_emoji == pytest.approx(
            text_only + c.stringWidth('🚀', EMOJI_FONT, 10),
        )

    def test_draw_mixed_string_advances_x_and_emits_pdf(self):
        c, buf = _make_canvas()
        fn = _font('regular')
        c.setFont(fn, 10)

        end_x = _draw_mixed_string(c, 50, 700, 'Hola 🚀 mundo', fn, 10)

        assert end_x == pytest.approx(
            50 + _mixed_string_width(c, 'Hola 🚀 mundo', fn, 10),
        )
        c.save()
        assert buf.getvalue()

    def test_draw_line_with_links_handles_bold_emoji_and_link(self):
        c, buf = _make_canvas()
        from reportlab.lib import colors

        _draw_line_with_links(
            c, 50, 700, '**Listo** 🚀 [link](https://example.com)',
            _font('regular'), 10, colors.black,
        )

        c.save()
        assert buf.getvalue()


# ── _visible_len (wrap weighting) ─────────────────────────────

class TestVisibleLen:
    def test_counts_emoji_double_and_markers_free(self):
        assert _visible_len('ab') == 2
        assert _visible_len('**ab**') == 2
        assert _visible_len('🚀') == 2
        assert _visible_len('a🚀b') == 4
