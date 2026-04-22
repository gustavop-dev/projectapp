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

  it('returns single-row table block as-is when no separator row', () => {
    const md = '| A | B |\n'
    const html = parseMarkdown(md)
    expect(html).not.toContain('<table')
  })

  it('renders table without separator row as plain body rows', () => {
    const md = '| A | B |\n| 1 | 2 |\n'
    const html = parseMarkdown(md)
    expect(html).toContain('md-table')
    expect(html).not.toContain('<thead>')
  })

  it('renders table without separator row as plain data rows', () => {
    const html = parseMarkdown('|a|b|\n|c|d|\n')
    expect(html).toContain('<table')
    expect(html).not.toContain('<thead')
  })

  it('does not transform a single-row table block', () => {
    const html = parseMarkdown('|a|b|\n')
    expect(html).not.toContain('<table')
  })

  it('renders bold italic combined formatting', () => {
    const html = parseMarkdown('***both***')
    expect(html).toContain('<strong><em>both</em></strong>')
  })

  it('renders plain bold formatting', () => {
    const html = parseMarkdown('**bold**')
    expect(html).toContain('<strong>bold</strong>')
  })

  it('renders italic with single star', () => {
    const html = parseMarkdown('*emph*')
    expect(html).toContain('<em>emph</em>')
  })

  it('renders headings h4 through h6', () => {
    const html = parseMarkdown('#### h4\n##### h5\n###### h6')
    expect(html).toContain('md-h4')
    expect(html).toContain('md-h5')
    expect(html).toContain('md-h6')
  })

  it.each(['TIP', 'IMPORTANT', 'WARNING', 'CAUTION'])('renders callout directive type %s', (type) => {
    const html = parseMarkdown(`> [!${type}]\n> body`)
    expect(html).toContain(`callout-${type.toLowerCase()}`)
  })

  it('preserves nested ordered list', () => {
    const html = parseMarkdown('1. parent\n   1. child')
    expect(html).toContain('<ol')
    expect(html).toContain('<li>parent')
  })

  it('preserves paragraph with inline br on single newlines', () => {
    const html = parseMarkdown('line one\nline two')
    expect(html).toContain('<br')
  })

  it('skips empty blocks between double newlines', () => {
    const html = parseMarkdown('first\n\n\n\nsecond')
    expect(html).toContain('<p class="md-p">first</p>')
    expect(html).toContain('<p class="md-p">second</p>')
  })
})
