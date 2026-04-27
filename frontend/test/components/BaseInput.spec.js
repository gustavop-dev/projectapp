import { mount } from '@vue/test-utils'
import BaseInput from '../../components/base/BaseInput.vue'

describe('BaseInput', () => {
  it('renders an <input> with semantic token classes for bg, text, border', () => {
    const wrapper = mount(BaseInput, { props: { modelValue: '' } })
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
    const cls = input.attributes('class') || ''
    expect(cls).toContain('bg-input-bg')
    expect(cls).toContain('text-input-text')
    expect(cls).toContain('border-input-border')
  })

  it('binds modelValue to the input value', () => {
    const wrapper = mount(BaseInput, { props: { modelValue: 'hola' } })
    expect(wrapper.find('input').element.value).toBe('hola')
  })

  it('emits update:modelValue when the user types', async () => {
    const wrapper = mount(BaseInput, { props: { modelValue: '' } })
    const input = wrapper.find('input')
    await input.setValue('nuevo')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['nuevo'])
  })

  it('applies error styles when error prop is true', () => {
    const wrapper = mount(BaseInput, { props: { modelValue: '', error: true } })
    const cls = wrapper.find('input').attributes('class') || ''
    expect(cls).toContain('border-danger-strong')
  })

  it('respects size="sm" with smaller padding/text', () => {
    const wrapper = mount(BaseInput, { props: { modelValue: '', size: 'sm' } })
    const cls = wrapper.find('input').attributes('class') || ''
    expect(cls).toContain('text-xs')
    expect(cls).toContain('py-1.5')
  })

  it('forwards type and placeholder to the native input', () => {
    const wrapper = mount(BaseInput, {
      props: { modelValue: '', type: 'email', placeholder: 'tu@correo.com' },
    })
    const input = wrapper.find('input')
    expect(input.attributes('type')).toBe('email')
    expect(input.attributes('placeholder')).toBe('tu@correo.com')
  })
})
