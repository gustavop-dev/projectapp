import { mount } from '@vue/test-utils'
import CostSection from '../../components/WebAppDiagnostic/public/CostSection.vue'

function mountSection({ content = {}, diagnostic = {}, renderContext = {} } = {}) {
  return mount(CostSection, {
    props: {
      content: {
        index: '6',
        title: 'Costo y Formas de Pago',
        intro: 'Intro corta.',
        valueBullets: [],
        paymentDescription: [],
        note: '',
        ...content,
      },
      diagnostic: {
        investment_amount: null,
        currency: '',
        duration_label: '',
        payment_terms: {},
        ...diagnostic,
      },
      renderContext,
    },
    global: {
      stubs: {
        SectionHeader: { props: ['index', 'title', 'fallback'], template: '<h2>{{ title || fallback }}</h2>' },
      },
    },
  })
}

describe('CostSection', () => {
  it('renders investment amount and currency from diagnostic', () => {
    const w = mountSection({
      diagnostic: { investment_amount: 5000000, currency: 'COP' },
    })
    const card = w.find('[data-testid="cost-investment-card"]')
    expect(card.exists()).toBe(true)
    expect(card.text()).toContain('5.000.000')
    expect(card.text()).toContain('COP')
  })

  it('renders segmented bar with proportional flexGrow from renderContext pcts', () => {
    const w = mountSection({
      content: {
        paymentDescription: [
          { label: 'al inicio', detail: 'apertura' },
          { label: 'al final', detail: 'entrega' },
        ],
      },
      diagnostic: { investment_amount: 5000000, currency: 'COP' },
      renderContext: { payment_initial_pct: 40, payment_final_pct: 60 },
    })
    const initial = w.find('[data-testid="cost-bar-initial"]')
    const final = w.find('[data-testid="cost-bar-final"]')
    expect(initial.exists()).toBe(true)
    expect(final.exists()).toBe(true)
    expect(initial.attributes('style')).toContain('flex-grow: 40')
    expect(final.attributes('style')).toContain('flex-grow: 60')
    expect(initial.text()).toContain('40%')
    expect(initial.text()).toContain('al inicio')
    expect(final.text()).toContain('60%')
  })

  it('renders valueBullets as cards, splitting on ": " into title and body', () => {
    const w = mountSection({
      content: {
        valueBullets: [
          'Claridad técnica: un mapa del estado real',
          '  ',
          'Priorización',
        ],
      },
    })
    const grid = w.find('[data-testid="cost-value-cards"]')
    expect(grid.exists()).toBe(true)
    const cards = grid.findAll('div.rounded-2xl')
    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('Claridad técnica')
    expect(cards[0].text()).toContain('un mapa del estado real')
    expect(cards[1].text()).toContain('Priorización')
    expect(cards[1].find('p + p').exists()).toBe(false)
  })

  it('computes per-segment amounts as Math.round(investment * pct / 100)', () => {
    const w = mountSection({
      content: {
        paymentDescription: [
          { label: 'al inicio', detail: 'a' },
          { label: 'al final', detail: 'b' },
        ],
      },
      diagnostic: { investment_amount: 5000000, currency: 'COP' },
      renderContext: { payment_initial_pct: 40, payment_final_pct: 60 },
    })
    expect(w.find('[data-testid="cost-segment-amount-initial"]').text()).toContain('2.000.000')
    expect(w.find('[data-testid="cost-segment-amount-final"]').text()).toContain('3.000.000')
  })

  it('renders payment detail text inside each bar segment (no separate tranche list)', () => {
    const w = mountSection({
      content: {
        paymentDescription: [
          { label: 'al inicio', detail: 'para dar apertura formal al diagnóstico' },
          { label: 'al final', detail: 'contra entrega del informe' },
        ],
      },
      diagnostic: { investment_amount: 5000000, currency: 'COP' },
      renderContext: { payment_initial_pct: 50, payment_final_pct: 50 },
    })
    const initial = w.find('[data-testid="cost-bar-initial"]')
    const final = w.find('[data-testid="cost-bar-final"]')
    expect(initial.text()).toContain('para dar apertura formal al diagnóstico')
    expect(final.text()).toContain('contra entrega del informe')
    expect(w.find('[data-testid="cost-segment-detail-initial"]').exists()).toBe(true)
    expect(w.find('[data-testid="cost-segment-detail-final"]').exists()).toBe(true)
    expect(w.find('[data-testid="cost-tranche-list"]').exists()).toBe(false)
  })

  it('hides segmented bar and uses fallback list when no percentages are configured', () => {
    const w = mountSection({
      content: {
        paymentDescription: [
          { label: 'Cuota 1', detail: 'detalle 1' },
          { label: 'Cuota 2', detail: 'detalle 2' },
        ],
      },
      diagnostic: { investment_amount: 1000000, currency: 'COP' },
    })
    expect(w.find('[data-testid="cost-segmented-bar"]').exists()).toBe(false)
    const fallback = w.find('[data-testid="cost-fallback-list"]')
    expect(fallback.exists()).toBe(true)
    expect(fallback.text()).toContain('Cuota 1')
    expect(fallback.text()).toContain('Cuota 2')
    expect(fallback.text()).not.toContain('%')
  })

  it('reads percentages from renderContext when payment_terms is missing', () => {
    const w = mountSection({
      content: {
        paymentDescription: [
          { label: 'al inicio', detail: 'a' },
          { label: 'al final', detail: 'b' },
        ],
      },
      diagnostic: { investment_amount: 0, currency: '', payment_terms: {} },
      renderContext: { payment_initial_pct: 30, payment_final_pct: 70 },
    })
    expect(w.find('[data-testid="cost-bar-initial"]').text()).toContain('30%')
    expect(w.find('[data-testid="cost-bar-final"]').text()).toContain('70%')
    expect(w.find('[data-testid="cost-segment-amount-initial"]').exists()).toBe(false)
  })

  it('renders duration_label chip when present on diagnostic or renderContext', () => {
    const fromDiagnostic = mountSection({
      diagnostic: { investment_amount: 5000000, currency: 'COP', duration_label: '8 semanas' },
    })
    expect(fromDiagnostic.find('[data-testid="cost-investment-card"]').text()).toContain('8 semanas')

    const fromContext = mountSection({
      diagnostic: { investment_amount: 5000000, currency: 'COP' },
      renderContext: { duration_label: '4 semanas' },
    })
    expect(fromContext.find('[data-testid="cost-investment-card"]').text()).toContain('4 semanas')
  })
})
