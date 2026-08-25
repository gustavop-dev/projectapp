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

  it('uses the catalog label for its accessible name and tooltip', () => {
    const wrapper = factory()
    const button = wrapper.get('button')
    expect(button.attributes('aria-label')).toBe('Copiar')
    expect(button.attributes('title')).toBe('Copiar')
    expect(button.attributes('data-panel-action')).toBe('copy')
    expect(wrapper.getComponent(BaseActionIcon).props('action')).toBe('copy')
    const icon = wrapper.get('svg.base-action-icon')
    expect(icon.attributes('aria-hidden')).toBe('true')
    expect(icon.classes()).toEqual(expect.arrayContaining(['!h-4', '!w-4']))
  })

  it('uses one contextual label for the name and hover help', () => {
    const wrapper = factory({ label: 'Copiar URL pública' })
    expect(wrapper.get('button').attributes('aria-label')).toBe('Copiar URL pública')
    expect(wrapper.get('button').attributes('title')).toBe('Copiar URL pública')
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
