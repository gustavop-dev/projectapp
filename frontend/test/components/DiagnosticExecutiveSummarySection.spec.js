import { mount } from '@vue/test-utils'

import ExecutiveSummarySection from '../../components/WebAppDiagnostic/public/ExecutiveSummarySection.vue'

const content = (overrides = {}) => ({
  index: '05',
  title: 'Resumen',
  intro: '',
  severityCounts: { critico: 2, alto: 3, medio: 1, bajo: 4 },
  narrative: '',
  highlights: [],
  ...overrides,
})

describe('WebAppDiagnostic public ExecutiveSummarySection', () => {
  it('renders the four severity tiles with counts and labels', () => {
    const wrapper = mount(ExecutiveSummarySection, { props: { content: content() } })
    const text = wrapper.text()
    expect(text).toContain('Crítico')
    expect(text).toContain('Alto')
    expect(text).toContain('Medio')
    expect(text).toContain('Bajo')
    expect(wrapper.find('.text-rose-600').text()).toBe('2')
    expect(wrapper.find('.text-amber-600').text()).toBe('3')
  })

  it('defaults missing severity counts to zero', () => {
    const wrapper = mount(ExecutiveSummarySection, {
      props: { content: content({ severityCounts: { critico: 5 } }) },
    })
    expect(wrapper.find('.text-rose-600').text()).toBe('5')
    expect(wrapper.find('.text-amber-600').text()).toBe('0')
  })

  it('shows intro and narrative only when provided', () => {
    const withText = mount(ExecutiveSummarySection, {
      props: { content: content({ intro: 'Contexto general.', narrative: 'La app está sana.' }) },
    })
    const withoutText = mount(ExecutiveSummarySection, { props: { content: content() } })
    expect(withText.text()).toContain('Contexto general.')
    expect(withText.text()).toContain('La app está sana.')
    expect(withoutText.text()).not.toContain('Contexto general.')
  })

  it('renders one bullet per highlight and omits the list when empty', () => {
    const withHighlights = mount(ExecutiveSummarySection, {
      props: { content: content({ highlights: ['Buen stack', 'Deuda en pagos'] }) },
    })
    const withoutHighlights = mount(ExecutiveSummarySection, { props: { content: content() } })
    expect(withHighlights.findAll('li')).toHaveLength(2)
    expect(withoutHighlights.find('ul').exists()).toBe(false)
  })
})
