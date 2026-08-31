import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import DashboardAdditionalModulesSection from '../../components/panel/dashboard/DashboardAdditionalModulesSection.vue'

global.useI18n = jest.fn(() => ({ locale: ref('es-co') }))
global.useLocalePath = jest.fn(() => (path) => `/es-co${path}`)
global.navigateTo = jest.fn()

const QuickAccessStub = {
  name: 'AdditionalModulesQuickAccess',
  props: ['language', 'stats', 'compact'],
  emits: ['share', 'customize-pdf', 'tracking', 'manage'],
  template: `
    <div>
      <button data-testid="share" @click="$emit('share')">share</button>
      <button data-testid="pdf" @click="$emit('customize-pdf')">pdf</button>
      <button data-testid="tracking" @click="$emit('tracking')">tracking</button>
      <button data-testid="manage" @click="$emit('manage')">manage</button>
    </div>
  `,
}

const summary = {
  active_module_count: 23,
  active_share_count: 4,
  unopened_active_share_count: 2,
  last_viewed_at: null,
}

function mountSection() {
  return mount(DashboardAdditionalModulesSection, {
    props: { summary },
    global: { stubs: { AdditionalModulesQuickAccess: QuickAccessStub } },
  })
}

describe('DashboardAdditionalModulesSection', () => {
  beforeEach(() => {
    navigateTo.mockClear()
  })

  it('passes the commercial summary to quick access', () => {
    const wrapper = mountSection()

    expect(wrapper.getComponent(QuickAccessStub).props('stats')).toEqual(summary)
  })

  it('opens the client selection from the dashboard', async () => {
    const wrapper = mountSection()

    await wrapper.get('[data-testid="share"]').trigger('click')

    expect(navigateTo).toHaveBeenCalledWith({
      path: '/es-co/panel/additional-modules',
      query: { action: 'share' },
    })
  })

  it('opens the personalized PDF from the dashboard', async () => {
    const wrapper = mountSection()

    await wrapper.get('[data-testid="pdf"]').trigger('click')

    expect(navigateTo).toHaveBeenCalledWith({
      path: '/es-co/panel/additional-modules',
      query: { action: 'pdf' },
    })
  })

  it('opens tracking from the dashboard', async () => {
    const wrapper = mountSection()

    await wrapper.get('[data-testid="tracking"]').trigger('click')

    expect(navigateTo).toHaveBeenCalledWith({
      path: '/es-co/panel/additional-modules',
      query: { action: 'tracking' },
    })
  })

  it('opens catalog administration from the dashboard', async () => {
    const wrapper = mountSection()

    await wrapper.get('[data-testid="manage"]').trigger('click')

    expect(navigateTo).toHaveBeenCalledWith('/es-co/panel/additional-modules')
  })
})
