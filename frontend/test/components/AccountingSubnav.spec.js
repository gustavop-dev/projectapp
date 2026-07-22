import { mount } from '@vue/test-utils'

import AccountingSubnav from '../../components/accounting/AccountingSubnav.vue'

global.useLocalePath = jest.fn(() => (path) => path)

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a :href="to" v-bind="$attrs"><slot /></a>', props: ['to'] },
  },
}

describe('AccountingSubnav', () => {
  it('renders one link per accounting section', () => {
    const wrapper = mount(AccountingSubnav, { global: GLOBAL })
    expect(wrapper.findAll('a')).toHaveLength(12)
    expect(wrapper.text()).toContain('Bolsillo')
    expect(wrapper.text()).toContain('Extractos')
  })

  it('marks the active section with aria-current', () => {
    const wrapper = mount(AccountingSubnav, {
      props: { active: 'incomes' },
      global: GLOBAL,
    })
    const active = wrapper.find('[data-testid="accounting-subnav-incomes"]')
    expect(active.attributes('aria-current')).toBe('page')
    expect(active.classes()).toContain('bg-primary')
  })

  it('leaves inactive sections without aria-current', () => {
    const wrapper = mount(AccountingSubnav, {
      props: { active: 'incomes' },
      global: GLOBAL,
    })
    const inactive = wrapper.find('[data-testid="accounting-subnav-pocket"]')
    expect(inactive.attributes('aria-current')).toBeUndefined()
    expect(inactive.classes()).toContain('bg-surface-raised')
  })

  it('points each link at its accounting route', () => {
    const wrapper = mount(AccountingSubnav, { global: GLOBAL })
    expect(
      wrapper.find('[data-testid="accounting-subnav-statements"]').attributes('href'),
    ).toBe('/panel/accounting/statements')
  })

  it('defaults the active section to the summary', () => {
    const wrapper = mount(AccountingSubnav, { global: GLOBAL })
    expect(
      wrapper.find('[data-testid="accounting-subnav-index"]').attributes('aria-current'),
    ).toBe('page')
  })
})
