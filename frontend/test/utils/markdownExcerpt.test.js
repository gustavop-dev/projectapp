import { makeSafeExcerpt } from '../../utils/markdownExcerpt'

describe('makeSafeExcerpt', () => {
  it('returns empty string for falsy input', () => {
    expect(makeSafeExcerpt('')).toBe('')
    expect(makeSafeExcerpt(null)).toBe('')
  })

  it('returns short markdown unchanged', () => {
    expect(makeSafeExcerpt('# Hola\n\nTexto.')).toBe('# Hola\n\nTexto.')
  })

  it('cuts long markdown at the last complete line', () => {
    const line = 'x'.repeat(80)
    const text = Array(10).fill(line).join('\n')

    const excerpt = makeSafeExcerpt(text, 500)

    expect(excerpt.length).toBeLessThanOrEqual(500)
    expect(excerpt.split('\n').every((l) => l === line)).toBe(true)
  })

  it('closes a dangling code fence', () => {
    const text = `intro\n\n\`\`\`\n${'code\n'.repeat(200)}`

    const excerpt = makeSafeExcerpt(text, 120)

    const fences = (excerpt.match(/```/g) || []).length
    expect(fences % 2).toBe(0)
    expect(excerpt.endsWith('```')).toBe(true)
  })

  it('leaves balanced fences alone', () => {
    const text = 'a\n```\ncode\n```\nb'
    expect(makeSafeExcerpt(text, 500)).toBe(text)
  })
})
