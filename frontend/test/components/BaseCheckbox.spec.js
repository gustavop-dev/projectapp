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

  // ── Array model (checkbox group) ──────────────────────────────────────────
  it('reflects membership when modelValue is an array', () => {
    const inArray = mount(BaseCheckbox, { props: { modelValue: [1, 2], value: 2 } })
    expect(inArray.find('input').element.checked).toBe(true)

    const notInArray = mount(BaseCheckbox, { props: { modelValue: [1, 2], value: 3 } })
    expect(notInArray.find('input').element.checked).toBe(false)
  })

  it('adds its value to the array when checked', async () => {
    const wrapper = mount(BaseCheckbox, { props: { modelValue: [1], value: 2 } })
    await wrapper.find('input').setValue(true)
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([[1, 2]])
  })

  it('removes its value from the array when unchecked', async () => {
    const wrapper = mount(BaseCheckbox, { props: { modelValue: [1, 2], value: 2 } })
    await wrapper.find('input').setValue(false)
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([[1]])
  })
})
