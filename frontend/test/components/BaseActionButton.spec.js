import { mount } from '@vue/test-utils'
import BaseActionButton from '../../components/base/BaseActionButton.vue'
import BaseActionIcon from '../../components/base/BaseActionIcon.vue'

const factory = (props = {}, attrs = {}) => mount(BaseActionButton, {
  props: { action: 'copy', ...props },
  attrs,
  attachTo: document.body,
  global: {
    stubs: {
      NuxtLink: { template: '<a><slot /></a>' },
    },
  },
})

describe('BaseActionButton', () => {
  afterEach(() => { document.body.innerHTML = '' })

  it('uses the catalog label for its accessible name', () => {
    const wrapper = factory()
    const button = wrapper.get('button')
    expect(button.attributes('aria-label')).toBe('Copiar')
    expect(button.attributes('title')).toBeUndefined()
    expect(button.attributes('data-panel-action')).toBe('copy')
    expect(wrapper.getComponent(BaseActionIcon).props('action')).toBe('copy')
    const icon = wrapper.get('svg.base-action-icon')
    expect(icon.attributes('aria-hidden')).toBe('true')
    expect(icon.classes()).toEqual(expect.arrayContaining(['!h-4', '!w-4']))
  })

  it('keeps contextual detail in the accessible name', () => {
    const wrapper = factory({ action: 'more', label: 'Acciones de Contrato de Servicios' })
    const button = wrapper.get('button')

    expect(button.attributes('aria-label')).toBe('Acciones de Contrato de Servicios')
    expect(button.attributes('title')).toBeUndefined()
  })

  it('shows the short catalog label in the application tooltip', async () => {
    const wrapper = factory({ action: 'more', label: 'Acciones de Contrato de Servicios' })

    await wrapper.get('button').trigger('focusin')

    const tooltip = wrapper.get('[role="tooltip"]')
    expect(tooltip.text()).toContain('Acciones')
    expect(tooltip.text()).not.toContain('Contrato de Servicios')
    expect(tooltip.classes()).toEqual(expect.arrayContaining(['w-max', 'max-w-xs']))
  })

  it('prefers an explicit application tooltip', async () => {
    const wrapper = factory({ label: 'Copiar URL pública', tooltip: 'Copiar enlace' })

    await wrapper.get('button').trigger('focusin')

    expect(wrapper.get('[role="tooltip"]').text()).toContain('Copiar enlace')
  })

  it('forwards button behavior and consumer attributes', async () => {
    const wrapper = factory({ variant: 'danger-ghost', size: 'md' }, { 'data-testid': 'copy-control' })
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
    expect(wrapper.get('button').attributes('data-testid')).toBe('copy-control')
  })

  it('forwards link semantics for navigational actions', () => {
    const wrapper = factory(
      { action: 'open-external', as: 'a', to: '/panel/views' },
      { target: '_blank', rel: 'noopener' },
    )
    const link = wrapper.get('a')
    expect(link.attributes('href')).toBe('/panel/views')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener')
  })

  it('blocks clicks while disabled', async () => {
    const wrapper = factory({ disabled: true })
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })

  it('keeps a disabled reason reachable from keyboard and touch', async () => {
    const wrapper = factory({
      disabled: true,
      disabledReason: 'Ya estás en la primera página.',
    })
    const proxy = wrapper.get('[data-disabled-action-proxy]')

    expect(proxy.attributes('tabindex')).toBe('0')
    expect(proxy.attributes('aria-label')).toContain('Ya estás en la primera página.')
    await proxy.trigger('click')
    expect(wrapper.get('[role="tooltip"]').text()).toContain('Ya estás en la primera página.')
  })

  it('shows the existing spinner instead of a second action glyph while loading', () => {
    const wrapper = factory({ loading: true })
    expect(wrapper.find('svg.base-action-icon').exists()).toBe(false)
    expect(wrapper.get('button').attributes('disabled')).toBeDefined()
    expect(wrapper.get('button').find('svg.animate-spin').exists()).toBe(true)
  })

  it('announces feedback without swapping the canonical icon', () => {
    const wrapper = factory({ statusLabel: 'Copiado: URL pública' })
    expect(wrapper.get('button').attributes('aria-label')).toBe('Copiado: URL pública')
    expect(wrapper.get('[role="status"]').text()).toBe('Copiado: URL pública')
    expect(wrapper.getComponent(BaseActionIcon).props('action')).toBe('copy')
  })
})
