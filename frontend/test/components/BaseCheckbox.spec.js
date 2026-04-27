import { mount } from '@vue/test-utils'
import BaseCheckbox from '../../components/base/BaseCheckbox.vue'

describe('BaseCheckbox', () => {
  it('renders an input[type=checkbox] reflecting modelValue', () => {
    const wrapper = mount(BaseCheckbox, { props: { modelValue: true } })
    const input = wrapper.find('input')
    expect(input.attributes('type')).toBe('checkbox')
    expect(input.element.checked).toBe(true)
  })

  it('emits update:modelValue with the new checked value on change', async () => {
    const wrapper = mount(BaseCheckbox, { props: { modelValue: false } })
    await wrapper.find('input').setValue(true)
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])
  })

  it('uses token classes (bg-input-bg, text-primary, focus ring)', () => {
    const wrapper = mount(BaseCheckbox, { props: { modelValue: false } })
    const cls = wrapper.find('input').attributes('class') || ''
    expect(cls).toContain('bg-input-bg')
    expect(cls).toContain('text-primary')
    expect(cls).toContain('ring-focus-ring/40')
  })

  it('renders default slot content as label text', () => {
    const wrapper = mount(BaseCheckbox, {
      props: { modelValue: false },
      slots: { default: 'Acepto los términos' },
    })
    expect(wrapper.text()).toContain('Acepto los términos')
  })

  it('disables the input when disabled prop is true', () => {
    const wrapper = mount(BaseCheckbox, { props: { modelValue: false, disabled: true } })
    expect(wrapper.find('input').attributes('disabled')).toBeDefined()
  })
})
