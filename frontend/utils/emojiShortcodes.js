import EMOJI_SHORTCODES from '~/assets/emoji/shortcodes.json'

/**
 * GitHub-style :shortcode: → Unicode emoji conversion.
 *
 * The shortcode table lives in `assets/emoji/shortcodes.json`, which is the
 * single source of truth shared with the backend
 * (`backend/content/services/emoji_shortcodes.py` loads the same file), so
 * both the on-screen preview and the PDF pipeline convert the exact same set.
 *
 * Unknown shortcodes are left untouched, and nothing inside fenced code
 * blocks (```...```) or inline code (`...`) is converted.
 */

const SHORTCODE_RE = /:([a-z0-9_+-]+):/g

// Capturing split: odd segments are code (fenced first so ``` wins over `).
const CODE_SEGMENT_RE = /(```[\s\S]*?(?:```|$)|`[^`\n]*`)/g

function convertSegment(text) {
  return text.replace(SHORTCODE_RE, (match, name) => EMOJI_SHORTCODES[name] || match)
}

export function replaceEmojiShortcodes(text) {
  if (text == null) return ''
  const str = String(text)
  if (!str.includes(':')) return str
  return str
    .split(CODE_SEGMENT_RE)
    .map((segment) => (segment.startsWith('`') ? segment : convertSegment(segment)))
    .join('')
}

export { EMOJI_SHORTCODES }
