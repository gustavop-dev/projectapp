import { mount } from '@vue/test-utils'
import BaseBadge from '../../components/base/BaseBadge.vue'

describe('BaseBadge', () => {
  it('renders default-slot content', () => {
    const wrapper = mount(BaseBadge, { slots: { default: 'Activo' } })
    expect(wrapper.text()).toBe('Activo')
  })

  it('uses neutral variant tokens by default', () => {
    const wrapper = mount(BaseBadge, { slots: { default: 'x' } })
    const cls = wrapper.find('span').classes()
    expect(cls).toContain('bg-surface-raised')
    expect(cls).toContain('text-text-muted')
  })

  it.each([
    ['success', 'bg-success-soft', 'text-success-strong'],
    ['warning', 'bg-warning-soft', 'text-warning-strong'],
    ['danger', 'bg-danger-soft', 'text-danger-strong'],
    ['accent', 'bg-accent-soft', 'text-primary-strong'],
    ['primary', 'bg-primary-soft', 'text-primary-strong'],
  ])('applies %s variant tokens', (variant, bg, text) => {
    const wrapper = mount(BaseBadge, { props: { variant }, slots: { default: 'x' } })
    const cls = wrapper.find('span').classes()
    expect(cls).toContain(bg)
    expect(cls).toContain(text)
  })

  it('applies sm size with text-[10px] and tighter padding', () => {
    const wrapper = mount(BaseBadge, { props: { size: 'sm' }, slots: { default: 'x' } })
    const cls = wrapper.find('span').attributes('class') || ''
    expect(cls).toContain('text-[10px]')
    expect(cls).toContain('px-2')
  })

  it('is rounded-full and inline-flex regardless of variant', () => {
    const wrapper = mount(BaseBadge, { props: { variant: 'danger' }, slots: { default: 'x' } })
    const cls = wrapper.find('span').classes()
    expect(cls).toContain('rounded-full')
    expect(cls).toContain('inline-flex')
  })
})
