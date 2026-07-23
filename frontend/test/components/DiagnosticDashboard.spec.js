import { flushPromises, mount } from '@vue/test-utils'

import DiagnosticDashboard from '../../components/WebAppDiagnostic/admin/DiagnosticDashboard.vue'

const BaseCollapseStub = {
  props: ['open'],
  template: '<div v-if="open" data-testid="collapse-body"><slot /></div>',
}

const diagnostic = (overrides = {}) => ({
  id: 1,
  status: 'sent',
  investment_amount: '1000000',
  initial_sent_at: '2026-05-01T10:00:00Z',
  responded_at: null,
  view_count: 0,
  ...overrides,
})

function mountDashboard(diagnostics = []) {
  return mount(DiagnosticDashboard, {
    props: { diagnostics },
    global: { stubs: { BaseCollapse: BaseCollapseStub } },
  })
}

describe('DiagnosticDashboard', () => {
  afterEach(() => {
    localStorage.clear()
  })

  it('counts only sent, viewed and negotiating as active', () => {
    const wrapper = mountDashboard([
      diagnostic({ id: 1, status: 'sent' }),
      diagnostic({ id: 2, status: 'viewed' }),
      diagnostic({ id: 3, status: 'negotiating' }),
      diagnostic({ id: 4, status: 'draft' }),
      diagnostic({ id: 5, status: 'accepted' }),
    ])
    expect(wrapper.get('[data-testid="dashboard-active"]').text()).toBe('3')
  })

  it('sums the investment of the active pipeline only', () => {
    const wrapper = mountDashboard([
      diagnostic({ id: 1, status: 'sent', investment_amount: '1000000' }),
      diagnostic({ id: 2, status: 'draft', investment_amount: '5000000' }),
    ])
    expect(wrapper.text()).toContain('1.000.000')
    expect(wrapper.text()).not.toContain('5.000.000')
  })

  it('shows a dash for the response rate when nothing was ever sent', () => {
    const wrapper = mountDashboard([
      diagnostic({ id: 1, status: 'draft', initial_sent_at: null }),
    ])
    expect(wrapper.text()).toContain('Tasa de respuesta')
    expect(wrapper.text()).not.toContain('%')
  })

  it('computes the response rate over the diagnostics ever sent', () => {
    const wrapper = mountDashboard([
      diagnostic({ id: 1, status: 'accepted' }),
      diagnostic({ id: 2, status: 'sent' }),
      diagnostic({ id: 3, status: 'rejected' }),
      diagnostic({ id: 4, status: 'sent' }),
    ])
    // 2 responded (accepted + rejected) out of 4 ever sent.
    expect(wrapper.text()).toContain('50%')
  })

  it('counts diagnostics flagged by the attention helper', () => {
    const wrapper = mountDashboard([
      diagnostic({ id: 1, status: 'sent', view_count: 12 }),
      diagnostic({ id: 2, status: 'sent', view_count: 0, responded_at: '2026-06-01T10:00:00Z' }),
      diagnostic({ id: 3, status: 'draft' }),
    ])
    expect(Number(wrapper.get('[data-testid="dashboard-attention"]').text())).toBeGreaterThanOrEqual(1)
  })

  it('paints the attention tile in warning tone only when there is something to act on', () => {
    const calm = mountDashboard([diagnostic({ id: 1, status: 'draft' })])
    const alert = mountDashboard([diagnostic({ id: 1, status: 'sent', view_count: 12 })])
    expect(calm.get('[data-testid="dashboard-attention"]').classes()).toContain('text-text-default')
    expect(alert.get('[data-testid="dashboard-attention"]').classes()).toContain('text-warning-strong')
  })

  it('starts expanded and collapses on toggle, persisting the choice', async () => {
    const wrapper = mountDashboard([diagnostic()])
    expect(wrapper.find('[data-testid="collapse-body"]').exists()).toBe(true)

    await wrapper.get('button').trigger('click')

    expect(wrapper.find('[data-testid="collapse-body"]').exists()).toBe(false)
    expect(localStorage.getItem('diagnostics_dashboard_collapsed')).toBe('1')
  })

  it('restores the collapsed state from localStorage on mount', async () => {
    localStorage.setItem('diagnostics_dashboard_collapsed', '1')
    const wrapper = mountDashboard([diagnostic()])
    await flushPromises()
    expect(wrapper.find('[data-testid="collapse-body"]').exists()).toBe(false)
    expect(wrapper.get('button').attributes('aria-expanded')).toBe('false')
  })

  it('renders zeroed tiles for an empty list', () => {
    const wrapper = mountDashboard([])
    expect(wrapper.get('[data-testid="dashboard-active"]').text()).toBe('0')
    expect(wrapper.get('[data-testid="dashboard-attention"]').text()).toBe('0')
  })
})
