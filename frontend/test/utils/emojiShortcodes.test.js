import { replaceEmojiShortcodes, EMOJI_SHORTCODES } from '../../utils/emojiShortcodes'

describe('replaceEmojiShortcodes', () => {
  it('returns empty string for null/undefined', () => {
    expect(replaceEmojiShortcodes(null)).toBe('')
    expect(replaceEmojiShortcodes(undefined)).toBe('')
  })

  it('returns text unchanged when there are no colons', () => {
    expect(replaceEmojiShortcodes('hola mundo')).toBe('hola mundo')
  })

  it('converts known shortcodes to unicode emoji', () => {
    expect(replaceEmojiShortcodes('Lanzamos :rocket: ya')).toBe('Lanzamos 🚀 ya')
    expect(replaceEmojiShortcodes(':smile:')).toBe('😄')
    expect(replaceEmojiShortcodes(':+1: y :-1:')).toBe('👍 y 👎')
    expect(replaceEmojiShortcodes(':100:')).toBe('💯')
  })

  it('converts consecutive shortcodes', () => {
    expect(replaceEmojiShortcodes(':fire::rocket:')).toBe('🔥🚀')
  })

  it('leaves unknown shortcodes untouched', () => {
    expect(replaceEmojiShortcodes(':foobar_xyz:')).toBe(':foobar_xyz:')
  })

  it('does not mangle times or ratios', () => {
    expect(replaceEmojiShortcodes('cita a las 10:30:45')).toBe('cita a las 10:30:45')
  })

  it('does not convert inside fenced code blocks', () => {
    const md = 'antes :rocket:\n```\ncode :rocket: here\n```\ndespués :rocket:'
    const out = replaceEmojiShortcodes(md)
    expect(out).toContain('antes 🚀')
    expect(out).toContain('después 🚀')
    expect(out).toContain('code :rocket: here')
  })

  it('does not convert inside inline code', () => {
    expect(replaceEmojiShortcodes('usa `:rocket:` para 🚀')).toBe('usa `:rocket:` para 🚀')
  })

  it('handles an unterminated fence without dropping content', () => {
    const md = 'texto :fire:\n```\nsin cierre :rocket:'
    const out = replaceEmojiShortcodes(md)
    expect(out).toContain('texto 🔥')
    expect(out).toContain('sin cierre :rocket:')
  })

  it('exposes a non-empty shortcode table with string emoji values', () => {
    const entries = Object.entries(EMOJI_SHORTCODES)
    expect(entries.length).toBeGreaterThan(100)
    for (const [name, emoji] of entries) {
      expect(name).toMatch(/^[a-z0-9_+-]+$/)
      expect(typeof emoji).toBe('string')
      expect(emoji.length).toBeGreaterThan(0)
    }
  })
})
