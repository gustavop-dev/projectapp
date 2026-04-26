/**
 * Roundtrip tests for buildFormFromJson / formToJson.
 *
 * Every section type must be able to go JSON -> form -> JSON without
 * losing non-empty data.
 */
import {
  SECTION_TYPES,
  buildFormFromJson,
  formToJson,
} from '../../components/WebAppDiagnostic/admin/diagnosticSectionEditorUtils'

describe('diagnosticSectionEditorUtils', () => {
  it('exposes all 8 section types', () => {
    expect(SECTION_TYPES).toEqual([
      'purpose', 'radiography', 'categories', 'delivery_structure',
      'executive_summary', 'cost', 'timeline', 'scope',
    ])
  })

  it('purpose: roundtrip preserves paragraphs and severity levels', () => {
    const original = {
      index: '1',
      title: 'Propósito',
      paragraphs: ['Uno', 'Dos'],
      scopeNote: 'Alcance',
      severityTitle: 'Escala',
      severityIntro: 'Intro',
      severityLevels: [{ level: 'Crítico', meaning: 'X' }],
    }
    const form = buildFormFromJson('purpose', original)
    expect(form.paragraphsText).toBe('Uno\nDos')
    expect(formToJson('purpose', form)).toMatchObject({
      paragraphs: ['Uno', 'Dos'],
      severityLevels: [{ level: 'Crítico', meaning: 'X' }],
    })
  })

  it('radiography: roundtrip preserves includes and classification rows', () => {
    const original = {
      index: '2',
      title: 'Radiografía',
      intro: 'Texto',
      includes: [{ title: 'Stack', description: 'desc' }],
      classificationRows: [{ dimension: 'Entidades', small: '<15', medium: '15-50', large: '>50' }],
    }
    const form = buildFormFromJson('radiography', original)
    const back = formToJson('radiography', form)
    expect(back.includes).toEqual([{ title: 'Stack', description: 'desc' }])
    expect(back.classificationRows[0]).toMatchObject({ dimension: 'Entidades' })
  })

  it('categories: roundtrip preserves the 14-category structure', () => {
    const original = {
      title: 'Cats',
      categories: [
        {
          key: 'architecture',
          title: 'Arquitectura',
          description: 'desc',
          strengths: ['ok'],
          findings: [{ level: 'Alto', title: 'F', detail: 'd' }],
          recommendations: [{ level: 'Alto', title: 'R', detail: 'd' }],
        },
      ],
    }
    const form = buildFormFromJson('categories', original)
    expect(form.categories[0].strengthsText).toBe('ok')
    const back = formToJson('categories', form)
    expect(back.categories[0].strengths).toEqual(['ok'])
    expect(back.categories[0].findings).toHaveLength(1)
    expect(back.categories[0].recommendations).toHaveLength(1)
  })

  it('delivery_structure: roundtrip preserves blocks', () => {
    const original = {
      title: 'Entrega',
      blocks: [
        { title: 'Lo bueno', paragraphs: ['p1'], example: 'ej' },
      ],
    }
    const form = buildFormFromJson('delivery_structure', original)
    const back = formToJson('delivery_structure', form)
    expect(back.blocks[0]).toEqual({ title: 'Lo bueno', paragraphs: ['p1'], example: 'ej' })
  })

  it('executive_summary: coerces severity counts to numbers', () => {
    const original = {
      title: 'Resumen',
      severityCounts: { critico: '2', alto: 1, medio: 0, bajo: 0 },
      narrative: 'n',
      highlights: ['h'],
    }
    const back = formToJson('executive_summary', buildFormFromJson('executive_summary', original))
    expect(back.severityCounts).toEqual({ critico: 2, alto: 1, medio: 0, bajo: 0 })
    expect(back.highlights).toEqual(['h'])
  })

  it('cost: roundtrip preserves payment description list', () => {
    const original = {
      title: 'Costo',
      paymentDescription: [{ label: 'al inicio', detail: 'apertura' }],
      note: 'nota',
    }
    const back = formToJson('cost', buildFormFromJson('cost', original))
    expect(back.paymentDescription).toEqual([{ label: 'al inicio', detail: 'apertura' }])
  })

  it('cost: roundtrip preserves valueBullets through textarea form', () => {
    const original = {
      title: 'Costo',
      valueBullets: ['Claridad técnica', 'Priorización de inversión'],
      paymentDescription: [],
      note: '',
    }
    const form = buildFormFromJson('cost', original)
    expect(form.valueBulletsText).toBe('Claridad técnica\nPriorización de inversión')
    const back = formToJson('cost', form)
    expect(back.valueBullets).toEqual(['Claridad técnica', 'Priorización de inversión'])
  })

  it('timeline: roundtrip preserves distribution', () => {
    const original = {
      title: 'Cronograma',
      distribution: [{ dayRange: 'Día 1', description: 'desc' }],
    }
    const back = formToJson('timeline', buildFormFromJson('timeline', original))
    expect(back.distribution).toEqual([{ dayRange: 'Día 1', description: 'desc' }])
  })

  it('scope: roundtrip preserves considerations', () => {
    const original = { title: 'Alcance', considerations: ['Uno', 'Dos'] }
    const back = formToJson('scope', buildFormFromJson('scope', original))
    expect(back.considerations).toEqual(['Uno', 'Dos'])
  })

  it('drops empty entries when serializing', () => {
    const form = buildFormFromJson('purpose', {
      severityLevels: [
        { level: '', meaning: '' },
        { level: 'Alto', meaning: 'x' },
      ],
    })
    const back = formToJson('purpose', form)
    expect(back.severityLevels).toHaveLength(1)
    expect(back.severityLevels[0].level).toBe('Alto')
  })
})
