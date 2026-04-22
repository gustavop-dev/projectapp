import {
  technicalFragmentHasContent,
  buildSyntheticTechnicalPanels,
  FRAGMENT_ORDER,
  TECH_PANEL_TITLES,
} from '~/utils/technicalProposalPanels'

describe('technicalFragmentHasContent', () => {
  it('returns true for intro', () => {
    expect(technicalFragmentHasContent('intro', {})).toBe(true)
  })

  it('returns false for unknown fragment', () => {
    expect(technicalFragmentHasContent('unknown', {})).toBe(false)
  })

  it('detects stack rows', () => {
    const doc = { stack: [{ layer: 'L', technology: 'T', rationale: 'R' }] }
    expect(technicalFragmentHasContent('stack', doc)).toBe(true)
  })

  it('detects architecture summary', () => {
    expect(technicalFragmentHasContent('architecture', { architecture: { summary: 's' } })).toBe(true)
  })

  it('detects architecture patterns', () => {
    const doc = { architecture: { patterns: [{ component: 'c', pattern: 'p', description: 'd' }] } }
    expect(technicalFragmentHasContent('architecture', doc)).toBe(true)
  })

  it('detects dataModel entities', () => {
    const doc = { dataModel: { entities: [{ name: 'n', description: 'd', keyFields: 'k' }] } }
    expect(technicalFragmentHasContent('dataModel', doc)).toBe(true)
  })

  it('detects growthReadiness strategies', () => {
    const doc = { growthReadiness: { strategies: [{ dimension: 'd', preparation: 'p', evolution: 'e' }] } }
    expect(technicalFragmentHasContent('growthReadiness', doc)).toBe(true)
  })

  it('detects epic requirement title', () => {
    const doc = { epics: [{ requirements: [{ title: 't' }] }] }
    expect(technicalFragmentHasContent('epics', doc)).toBe(true)
  })

  it('detects apiDomains', () => {
    const doc = { apiDomains: [{ domain: 'd', summary: 's' }] }
    expect(technicalFragmentHasContent('api', doc)).toBe(true)
  })

  it('detects integrations included', () => {
    const doc = {
      integrations: {
        included: [{ service: 's', provider: 'p', connection: 'c', dataExchange: 'x', accountOwner: 'a' }],
      },
    }
    expect(technicalFragmentHasContent('integrations', doc)).toBe(true)
  })

  it('detects integrations excluded', () => {
    const doc = { integrations: { excluded: [{ service: 's', reason: 'r', availability: 'a' }] } }
    expect(technicalFragmentHasContent('integrations', doc)).toBe(true)
  })

  it('detects environments rows', () => {
    const doc = { environments: [{ name: 'n', purpose: 'p', url: 'u', database: 'd', whoAccesses: 'w' }] }
    expect(technicalFragmentHasContent('environments', doc)).toBe(true)
  })

  it('detects security rows', () => {
    const doc = { security: [{ aspect: 'a', implementation: 'i' }] }
    expect(technicalFragmentHasContent('security', doc)).toBe(true)
  })

  it('detects performanceQuality metrics', () => {
    const doc = { performanceQuality: { metrics: [{ metric: 'm', target: 't', howMeasured: 'h' }] } }
    expect(technicalFragmentHasContent('performance', doc)).toBe(true)
  })

  it('detects backupsNote', () => {
    expect(technicalFragmentHasContent('backups', { backupsNote: 'note' })).toBe(true)
  })

  it('detects quality dimensions', () => {
    const doc = { quality: { dimensions: [{ dimension: 'd', evaluates: 'e', standard: 's' }] } }
    expect(technicalFragmentHasContent('quality', doc)).toBe(true)
  })

  it('detects decisions', () => {
    const doc = { decisions: [{ decision: 'd', alternative: 'a', reason: 'r' }] }
    expect(technicalFragmentHasContent('decisions', doc)).toBe(true)
  })

  it('returns false for stack when doc null coerces to empty object', () => {
    expect(technicalFragmentHasContent('stack', null)).toBe(false)
  })

  it('detects apiSummary alone', () => {
    expect(technicalFragmentHasContent('api', { apiSummary: 's' })).toBe(true)
  })

  it('detects environmentsNote', () => {
    expect(technicalFragmentHasContent('environments', { environmentsNote: 'n' })).toBe(true)
  })

  it('detects quality criticalFlowsNote', () => {
    expect(technicalFragmentHasContent('quality', { quality: { criticalFlowsNote: 'c' } })).toBe(true)
  })

  it('detects performance practices', () => {
    const doc = { performanceQuality: { practices: [{ strategy: 's', description: 'd' }] } }
    expect(technicalFragmentHasContent('performance', doc)).toBe(true)
  })

  it('detects dataModel summary', () => {
    expect(technicalFragmentHasContent('dataModel', { dataModel: { summary: 's' } })).toBe(true)
  })

  it('detects growthReadiness summary only', () => {
    expect(technicalFragmentHasContent('growthReadiness', { growthReadiness: { summary: 'g' } })).toBe(true)
  })

  it('detects epic header without requirements body', () => {
    const doc = { epics: [{ epicKey: 'k', requirements: [] }] }
    expect(technicalFragmentHasContent('epics', doc)).toBe(true)
  })

  it('detects epic by title field', () => {
    const doc = { epics: [{ title: 'My Epic', requirements: [] }] }
    expect(technicalFragmentHasContent('epics', doc)).toBe(true)
  })

  it('detects epic by description field', () => {
    const doc = { epics: [{ description: 'Some desc', requirements: [] }] }
    expect(technicalFragmentHasContent('epics', doc)).toBe(true)
  })

  it('detects quality testTypes', () => {
    const doc = { quality: { testTypes: [{ type: 't', validates: 'v', tool: 'x', whenRun: 'w' }] } }
    expect(technicalFragmentHasContent('quality', doc)).toBe(true)
  })

  it('returns false for stack row that is a non-object value', () => {
    expect(technicalFragmentHasContent('stack', { stack: ['not-an-object'] })).toBe(false)
  })

  it('returns false for epics with null requirements and no header fields', () => {
    expect(technicalFragmentHasContent('epics', { epics: [{ requirements: null }] })).toBe(false)
  })

  it('detects integrations notes', () => {
    expect(technicalFragmentHasContent('integrations', { integrations: { notes: 'some note' } })).toBe(true)
  })
})

describe('buildSyntheticTechnicalPanels', () => {
  it('returns panels only for fragments with content', () => {
    const technicalSection = {
      id: 42,
      content_json: {
        purpose: 'p',
        stack: [{ layer: 'l', technology: 't', rationale: 'r' }],
      },
    }
    const panels = buildSyntheticTechnicalPanels(technicalSection, 'en')
    const ids = panels.map((p) => p._technicalFragment)
    expect(ids).toContain('intro')
    expect(ids).toContain('stack')
    expect(panels[0].content_json).toEqual(technicalSection.content_json)
    expect(panels[0]._sourceTechnicalSectionId).toBe(42)
  })

  it('uses Spanish titles when lang missing key falls back via loc', () => {
    const technicalSection = { id: 1, content_json: { purpose: 'x' } }
    const panels = buildSyntheticTechnicalPanels(technicalSection, 'xx')
    expect(panels.length).toBeGreaterThan(0)
    expect(panels[0].title).toBe(TECH_PANEL_TITLES.es.intro)
  })

  it('handles missing content_json', () => {
    const panels = buildSyntheticTechnicalPanels({ id: 1 }, 'en')
    expect(panels.some((p) => p._technicalFragment === 'intro')).toBe(true)
  })

  it('handles null technicalSection gracefully', () => {
    const panels = buildSyntheticTechnicalPanels(null, 'en')
    expect(panels.some((p) => p._technicalFragment === 'intro')).toBe(true)
    expect(panels[0]._sourceTechnicalSectionId).toBeUndefined()
  })
})

describe('FRAGMENT_ORDER', () => {
  it('lists intro first', () => {
    expect(FRAGMENT_ORDER[0]).toBe('intro')
  })
})

describe('technicalFragmentHasContent additional branches', () => {
  const { technicalFragmentHasContent } = require('~/utils/technicalProposalPanels')

  it('detects architecture content from diagramNote only', () => {
    expect(technicalFragmentHasContent('architecture', { architecture: { diagramNote: 'note' } })).toBe(true)
  })

  it('detects dataModel content from relationships only', () => {
    expect(technicalFragmentHasContent('dataModel', { dataModel: { relationships: 'rel' } })).toBe(true)
  })

  it('detects growthReadiness content from summary only', () => {
    expect(technicalFragmentHasContent('growthReadiness', { growthReadiness: { summary: 'g' } })).toBe(true)
  })

  it('detects api content from apiSummary only', () => {
    expect(technicalFragmentHasContent('api', { apiSummary: 'sum' })).toBe(true)
  })

  it('detects integrations content from notes only', () => {
    expect(technicalFragmentHasContent('integrations', { integrations: { notes: 'n' } })).toBe(true)
  })

  it('detects environments content from environmentsNote only', () => {
    expect(technicalFragmentHasContent('environments', { environmentsNote: 'note' })).toBe(true)
  })

  it('detects quality content from criticalFlowsNote only', () => {
    expect(technicalFragmentHasContent('quality', { quality: { criticalFlowsNote: 'cf' } })).toBe(true)
  })

  it('returns false for unknown fragment', () => {
    expect(technicalFragmentHasContent('unknown-fragment', {})).toBe(false)
  })

  it('returns false when doc is null', () => {
    expect(technicalFragmentHasContent('stack', null)).toBe(false)
  })

  it('returns false when doc is not an object', () => {
    expect(technicalFragmentHasContent('stack', 'string')).toBe(false)
  })

  it('epics detects content via requirement configuration field', () => {
    const doc = { epics: [{ requirements: [{ configuration: 'cfg' }] }] }
    expect(technicalFragmentHasContent('epics', doc)).toBe(true)
  })

  it('epics returns false for empty epic with empty requirement', () => {
    expect(technicalFragmentHasContent('epics', { epics: [{ requirements: [{}] }] })).toBe(false)
  })
})
