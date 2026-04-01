import { useMarkdownPreview } from '../../composables/useMarkdownPreview'

describe('useMarkdownPreview', () => {
  const { parseMarkdown } = useMarkdownPreview()

  it('returns empty string for falsy input', () => {
    expect(parseMarkdown('')).toBe('')
    expect(parseMarkdown(null)).toBe('')
  })

  it('converts CRLF to LF before processing', () => {
    const html = parseMarkdown('# T\r\n')
    expect(html).toContain('md-h1')
  })

  it('wraps fenced code and escapes HTML entities', () => {
    const html = parseMarkdown('```\n<a>\n```')
    expect(html).toContain('&lt;a&gt;')
    expect(html).toContain('md-code-block')
  })

  it('builds table with separator row', () => {
    const md = '| A | B |\n| --- | --- |\n| 1 | 2 |\n'
    const html = parseMarkdown(md)
    expect(html).toContain('md-table')
    expect(html).toContain('<thead>')
  })

  it('renders callout for NOTE directive', () => {
    const md = '> [!NOTE]\n> body **bold**'
    const html = parseMarkdown(md)
    expect(html).toContain('callout-note')
    expect(html).toContain('<strong>')
  })

  it('renders plain blockquote when not callout', () => {
    const md = '> quote line'
    const html = parseMarkdown(md)
    expect(html).toContain('md-blockquote')
  })

  it('renders headings h1 through h3', () => {
    expect(parseMarkdown('# One')).toContain('md-h1')
    expect(parseMarkdown('## Two')).toContain('md-h2')
    expect(parseMarkdown('### Three')).toContain('md-h3')
  })

  it('renders horizontal rule', () => {
    expect(parseMarkdown('---')).toContain('md-hr')
  })

  it('renders unordered list with nested item', () => {
    const md = '- a\n  - b'
    const html = parseMarkdown(md)
    expect(html).toContain('md-ul')
    expect(html).toContain('<li>')
  })

  it('renders ordered list', () => {
    const html = parseMarkdown('1. first\n2. second')
    expect(html).toContain('md-ol')
  })

  it('applies strikethrough and inline code', () => {
    const html = parseMarkdown('~~x~~ and `code`')
    expect(html).toContain('<del>')
    expect(html).toContain('<code>code</code>')
  })

  it('renders markdown link with security attributes', () => {
    const html = parseMarkdown('[t](https://e.com)')
    expect(html).toContain('rel="noopener noreferrer"')
    expect(html).toContain('md-link')
  })

  it('wraps loose text in paragraph', () => {
    const html = parseMarkdown('Hello world')
    expect(html).toContain('md-p')
  })
})
