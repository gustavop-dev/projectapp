import { buildProposalModuleLinkOptions } from '~/utils/proposalModuleLinkOptions'

describe('buildProposalModuleLinkOptions', () => {
  it('returns empty array when sections is not an array', () => {
    expect(buildProposalModuleLinkOptions(null)).toEqual([])
  })

  it('skips hidden groups', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [{ id: 1, title: 'G', is_visible: false, is_calculator_module: true, price_percent: 10 }],
        },
      },
    ]
    expect(buildProposalModuleLinkOptions(sections)).toEqual([])
  })

  it('skips group without title and without items', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: { groups: [{ id: 2, is_calculator_module: true, price_percent: 5 }] },
      },
    ]
    expect(buildProposalModuleLinkOptions(sections)).toEqual([])
  })

  it('skips group with zero price_percent when not calculator', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [{ id: 3, title: 'T', is_calculator_module: false, price_percent: 0 }],
        },
      },
    ]
    expect(buildProposalModuleLinkOptions(sections)).toEqual([])
  })

  it('emits module id for calculator group', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [{ id: 9, title: 'Calc', is_calculator_module: true, price_percent: 0 }],
        },
      },
    ]
    const opts = buildProposalModuleLinkOptions(sections)
    expect(opts).toEqual([{ id: 'module-9', label: 'Calc' }])
  })

  it('emits group id for non-calculator with price', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [{ id: 4, title: 'Pack', icon: '📦', is_calculator_module: false, price_percent: 10 }],
        },
      },
    ]
    const opts = buildProposalModuleLinkOptions(sections)
    expect(opts[0].id).toBe('group-4')
    expect(opts[0].label).toContain('Pack')
  })

  it('merges additionalModules into groups', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [],
          additionalModules: [
            { id: 5, title: 'Add', is_calculator_module: true, price_percent: 1 },
          ],
        },
      },
    ]
    expect(buildProposalModuleLinkOptions(sections)[0].id).toBe('module-5')
  })

  it('adds investment modules with string id', () => {
    const sections = [
      { section_type: 'investment', content_json: { modules: [{ id: 'inv1', title: 'I' }] } },
    ]
    const opts = buildProposalModuleLinkOptions(sections)
    expect(opts).toEqual([{ id: 'inv1', label: 'I' }])
  })

  it('skips investment module with empty id', () => {
    const sections = [
      { section_type: 'investment', content_json: { modules: [{ id: '', title: 'x' }] } },
    ]
    expect(buildProposalModuleLinkOptions(sections)).toEqual([])
  })

  it('uses id as label when group title is missing', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [{ id: 7, items: ['x'], is_calculator_module: true, price_percent: 0 }],
        },
      },
    ]
    const opts = buildProposalModuleLinkOptions(sections)
    expect(opts[0].label).toBe('7')
  })

  it('falls back to 0 when price_percent is undefined', () => {
    const sections = [
      {
        section_type: 'functional_requirements',
        content_json: {
          groups: [{ id: 8, title: 'T', is_calculator_module: true }],
        },
      },
    ]
    const opts = buildProposalModuleLinkOptions(sections)
    expect(opts[0].id).toBe('module-8')
  })

  it('uses module id as label when investment module has no title', () => {
    const sections = [
      { section_type: 'investment', content_json: { modules: [{ id: 'inv2' }] } },
    ]
    const opts = buildProposalModuleLinkOptions(sections)
    expect(opts[0].label).toBe('inv2')
  })
})
