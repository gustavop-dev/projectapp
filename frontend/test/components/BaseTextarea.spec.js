import { mount } from '@vue/test-utils'
import BaseTextarea from '../../components/base/BaseTextarea.vue'

describe('BaseTextarea', () => {
  it('renders a <textarea> with semantic token classes', () => {
    const wrapper = mount(BaseTextarea, { props: { modelValue: '' } })
    const ta = wrapper.find('textarea')
    expect(ta.exists()).toBe(true)
    const cls = ta.attributes('class') || ''
    expect(cls).toContain('bg-input-bg')
    expect(cls).toContain('text-input-text')
    expect(cls).toContain('border-input-border')
  })

  it('binds modelValue to the textarea value', () => {
    const wrapper = mount(BaseTextarea, { props: { modelValue: 'hola\nmundo' } })
    expect(wrapper.find('textarea').element.value).toBe('hola\nmundo')
  })

  it('emits update:modelValue when the user types', async () => {
    const wrapper = mount(BaseTextarea, { props: { modelValue: '' } })
    await wrapper.find('textarea').setValue('nuevo')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['nuevo'])
  })

  it('forwards rows and placeholder', () => {
    const wrapper = mount(BaseTextarea, {
      props: { modelValue: '', rows: 8, placeholder: 'Escribe aquí…' },
    })
    const ta = wrapper.find('textarea')
    expect(ta.attributes('rows')).toBe('8')
    expect(ta.attributes('placeholder')).toBe('Escribe aquí…')
  })

  it('applies error styling when error prop is true', () => {
    const wrapper = mount(BaseTextarea, { props: { modelValue: '', error: true } })
    expect(wrapper.find('textarea').attributes('class')).toContain('border-danger-strong')
  })

  it('respects size="sm" with smaller padding/text', () => {
    const wrapper = mount(BaseTextarea, { props: { modelValue: '', size: 'sm' } })
    const cls = wrapper.find('textarea').attributes('class') || ''
    expect(cls).toContain('text-xs')
    expect(cls).toContain('py-1.5')
  })
})
