import { mount } from '@vue/test-utils'
import BaseSelect from '../../components/base/BaseSelect.vue'

describe('BaseSelect', () => {
  it('renders a <select> with semantic token classes', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'a', options: ['a', 'b'] },
    })
    const sel = wrapper.find('select')
    expect(sel.exists()).toBe(true)
    const cls = sel.attributes('class') || ''
    expect(cls).toContain('bg-input-bg')
    expect(cls).toContain('text-input-text')
    expect(cls).toContain('border-input-border')
  })

  it('renders one <option> per string in options', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'a', options: ['a', 'b', 'c'] },
    })
    const opts = wrapper.findAll('option')
    expect(opts).toHaveLength(3)
    expect(opts[0].element.value).toBe('a')
    expect(opts[2].text()).toBe('c')
  })

  it('renders one <option> per object in options with value/label', () => {
    const wrapper = mount(BaseSelect, {
      props: {
        modelValue: 'cop',
        options: [
          { value: 'cop', label: 'COP' },
          { value: 'usd', label: 'USD' },
        ],
      },
    })
    const opts = wrapper.findAll('option')
    expect(opts[0].element.value).toBe('cop')
    expect(opts[0].text()).toBe('COP')
    expect(opts[1].text()).toBe('USD')
  })

  it('binds the selected option to modelValue', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'b', options: ['a', 'b', 'c'] },
    })
    expect(wrapper.find('select').element.value).toBe('b')
  })

  it('emits update:modelValue with the new value on change', async () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'a', options: ['a', 'b'] },
    })
    await wrapper.find('select').setValue('b')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['b'])
  })

  it('renders a placeholder option when placeholder prop is set', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: '', options: ['a'], placeholder: 'Selecciona…' },
    })
    const first = wrapper.findAll('option')[0]
    expect(first.text()).toBe('Selecciona…')
    expect(first.attributes('disabled')).toBeDefined()
  })

  it('renders default slot options when provided (overrides options prop)', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'x', options: [] },
      slots: { default: '<option value="x">X</option><option value="y">Y</option>' },
    })
    const opts = wrapper.findAll('option')
    expect(opts).toHaveLength(2)
    expect(opts[1].text()).toBe('Y')
  })

  it('applies error styling when error prop is true', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'a', options: ['a'], error: true },
    })
    expect(wrapper.find('select').attributes('class')).toContain('border-danger-strong')
  })

  it('respects size="sm" with smaller padding/text', () => {
    const wrapper = mount(BaseSelect, {
      props: { modelValue: 'a', options: ['a'], size: 'sm' },
    })
    const cls = wrapper.find('select').attributes('class') || ''
    expect(cls).toContain('text-xs')
    expect(cls).toContain('py-1.5')
  })
})
