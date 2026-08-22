import { mount } from '@vue/test-utils'
import AccountingIndicatorGroup from '~/components/accounting/AccountingIndicatorGroup.vue'

const BaseButtonStub = {
  emits: ['click'],
  template: '<button type="button" v-bind="$attrs" @click="$emit(\'click\')"><slot /></button>',
}

function mountGroup(props = {}) {
  return mount(AccountingIndicatorGroup, {
    props: { columns: 5, secondaryCount: 2, ...props },
    slots: {
      primary: '<article data-testid="primary-kpi">Prioritario</article>',
      secondary: '<article data-testid="secondary-kpi">Secundario</article>',
    },
    global: { stubs: { BaseButton: BaseButtonStub } },
  })
}

describe('AccountingIndicatorGroup', () => {
  it('keeps the priority indicators outside the disclosed remainder', () => {
    const wrapper = mountGroup()

    expect(wrapper.get('[data-testid="primary-kpi"]').text()).toBe('Prioritario')
    expect(wrapper.get('[data-testid="primary-kpi"]')
      .element.closest('[data-testid="accounting-secondary-indicators"]')).toBeNull()
    expect(wrapper.get('[data-testid="secondary-kpi"]')
      .element.closest('[data-testid="accounting-secondary-indicators"]')).not.toBeNull()
  })

  it('announces the number of indicators hidden on narrow screens', () => {
    const wrapper = mountGroup()
    const toggle = wrapper.get('[data-testid="accounting-indicators-toggle"]')

    expect(toggle.text()).toContain('Ver todos los indicadores (2)')
    expect(toggle.attributes('aria-expanded')).toBe('false')
  })

  it('expands and collapses the secondary indicators from one control', async () => {
    const wrapper = mountGroup()
    const toggle = wrapper.get('[data-testid="accounting-indicators-toggle"]')

    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('[data-testid="accounting-secondary-indicators"]').classes())
      .toContain('contents')
    expect(toggle.text()).toContain('Ocultar indicadores')

    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('false')
  })

  it('omits the disclosure when every indicator is already primary', () => {
    const wrapper = mountGroup({ secondaryCount: 0 })

    expect(wrapper.find('[data-testid="accounting-indicators-toggle"]').exists()).toBe(false)
  })
})
