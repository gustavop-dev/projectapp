import { mount } from '@vue/test-utils'
import BaseFormField from '../../components/base/BaseFormField.vue'

describe('BaseFormField', () => {
  it('renders the label and links it via for', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: 'Nombre', for: 'name-input' },
      slots: { default: '<input id="name-input" />' },
    })
    const label = wrapper.find('label')
    expect(label.text()).toContain('Nombre')
    expect(label.attributes('for')).toBe('name-input')
  })

  it('renders the slotted control', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: 'X' },
      slots: { default: '<input data-testid="ctl" />' },
    })
    expect(wrapper.find('[data-testid="ctl"]').exists()).toBe(true)
  })

  it('shows hint when no error is set', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: 'X', hint: 'Algo de ayuda' },
      slots: { default: '<input />' },
    })
    expect(wrapper.text()).toContain('Algo de ayuda')
    expect(wrapper.find('p').classes()).toContain('text-text-muted')
  })

  it('shows error and hides hint when error is set', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: 'X', hint: 'Hint', error: 'Es obligatorio' },
      slots: { default: '<input />' },
    })
    const para = wrapper.find('p')
    expect(para.text()).toBe('Es obligatorio')
    expect(para.classes()).toContain('text-danger-strong')
    expect(wrapper.text()).not.toContain('Hint')
  })

  it('renders required marker when required is true', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: 'Email', required: true },
      slots: { default: '<input />' },
    })
    expect(wrapper.find('label').text()).toContain('*')
    expect(wrapper.find('label .text-danger-strong').exists()).toBe(true)
  })

  it('omits the label element when no label prop is given', () => {
    const wrapper = mount(BaseFormField, { slots: { default: '<input />' } })
    expect(wrapper.find('label').exists()).toBe(false)
  })

  it('uses smaller label sizing when size="sm"', () => {
    const wrapper = mount(BaseFormField, {
      props: { label: 'X', size: 'sm' },
      slots: { default: '<input />' },
    })
    expect(wrapper.find('label').classes()).toContain('text-xs')
  })
})
