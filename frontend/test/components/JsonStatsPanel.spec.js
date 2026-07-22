import { mount } from '@vue/test-utils'

import JsonStatsPanel from '../../components/BusinessProposal/admin/JsonStatsPanel.vue'

const STATS = {
  sectionCount: 12,
  progress: 71,
  size: '4.2 KB',
  updatedAt: 'Jue, 16 jul 2026',
}

describe('JsonStatsPanel', () => {
  it('renders the four stats with their labels', () => {
    const wrapper = mount(JsonStatsPanel, {
      props: { stats: STATS, testId: 'json-stats' },
    })
    const text = wrapper.text()
    expect(text).toContain('Secciones: 12')
    expect(text).toContain('Progreso: 71%')
    expect(text).toContain('Tamaño del JSON: 4.2 KB')
    expect(text).toContain('Última actualización: Jue, 16 jul 2026')
  })

  it('exposes the provided test id on the panel root', () => {
    const wrapper = mount(JsonStatsPanel, {
      props: { stats: STATS, testId: 'proposal-json-stats' },
    })
    expect(wrapper.find('[data-testid="proposal-json-stats"]').exists()).toBe(true)
  })
})
