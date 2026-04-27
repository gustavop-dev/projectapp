import { mount } from '@vue/test-utils'
import BaseButton from '../../components/base/BaseButton.vue'

describe('BaseButton', () => {
  it('renders a <button type="button"> by default with default-slot content', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Guardar' } })
    const btn = wrapper.find('button')
    expect(btn.exists()).toBe(true)
    expect(btn.attributes('type')).toBe('button')
    expect(btn.text()).toBe('Guardar')
  })

  it.each([
    ['primary', 'bg-primary'],
    ['secondary', 'bg-surface'],
    ['ghost', 'bg-transparent'],
    ['danger', 'bg-danger-strong'],
    ['accent', 'bg-accent'],
  ])('applies %s variant tokens', (variant, expected) => {
    const wrapper = mount(BaseButton, { props: { variant }, slots: { default: 'x' } })
    expect(wrapper.find('button').classes()).toContain(expected)
  })

  it.each([
    ['sm', 'text-xs'],
    ['md', 'text-sm'],
    ['lg', 'text-base'],
  ])('applies %s size', (size, expected) => {
    const wrapper = mount(BaseButton, { props: { size }, slots: { default: 'x' } })
    expect(wrapper.find('button').classes()).toContain(expected)
  })

  it('emits click when pressed', async () => {
    const wrapper = mount(BaseButton, { slots: { default: 'x' } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('disables the button when disabled prop is true', () => {
    const wrapper = mount(BaseButton, { props: { disabled: true }, slots: { default: 'x' } })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('renders a spinner and disables the button when loading is true', () => {
    const wrapper = mount(BaseButton, { props: { loading: true }, slots: { default: 'Guardando' } })
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('svg').classes()).toContain('animate-spin')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('renders the spinner only when loading is true', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'x' } })
    expect(wrapper.find('svg').exists()).toBe(false)
  })

  it('respects type prop on button element', () => {
    const wrapper = mount(BaseButton, { props: { type: 'submit' }, slots: { default: 'x' } })
    expect(wrapper.find('button').attributes('type')).toBe('submit')
  })

  it('renders as a different element when "as" prop is used and omits type', () => {
    const wrapper = mount(BaseButton, {
      props: { as: 'a', type: 'submit' },
      slots: { default: 'x' },
    })
    expect(wrapper.element.tagName).toBe('A')
    expect(wrapper.attributes('type')).toBeUndefined()
  })

  it('always includes focus-ring token class', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'x' } })
    const cls = wrapper.find('button').attributes('class') || ''
    expect(cls).toContain('focus:ring-focus-ring/40')
  })
})
