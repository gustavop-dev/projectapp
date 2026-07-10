"""
GitHub-style :shortcode: → Unicode emoji conversion.

The shortcode table lives in ``frontend/assets/emoji/shortcodes.json`` and is
the single source of truth shared with the frontend renderer
(``frontend/utils/emojiShortcodes.js``), so the on-screen preview and the PDF
pipeline convert exactly the same set. Same precedent as the PDF fonts, which
the backend also reads from ``frontend/assets/fonts``.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

_SHORTCODES_JSON = (
    Path(settings.BASE_DIR).parent / 'frontend' / 'assets' / 'emoji' / 'shortcodes.json'
)

_SHORTCODE_RE = re.compile(r':([a-z0-9_+-]+):')
# Capturing split: matched segments are code spans (fenced wins over inline).
_CODE_SEGMENT_RE = re.compile(r'(```.*?(?:```|$)|`[^`\n]*`)', re.DOTALL)


@lru_cache(maxsize=1)
def _shortcode_table():
    """Load the shared shortcode table once; empty dict if unavailable."""
    try:
        with open(_SHORTCODES_JSON, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        logger.warning('emoji shortcodes table not readable at %s', _SHORTCODES_JSON)
        return {}


def replace_shortcodes(text):
    """Replace ``:name:`` with its Unicode emoji.

    Unknown shortcodes stay literal, and nothing inside fenced code blocks
    or inline code is converted.
    """
    if not text or ':' not in text:
        return text
    table = _shortcode_table()
    if not table:
        return text

    def _convert(segment):
        return _SHORTCODE_RE.sub(lambda m: table.get(m.group(1), m.group(0)), segment)

    parts = _CODE_SEGMENT_RE.split(text)
    return ''.join(
        part if part.startswith('`') else _convert(part)
        for part in parts
    )
