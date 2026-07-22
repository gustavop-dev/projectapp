import { mount } from '@vue/test-utils'

import ScopeForm from '../../components/WebAppDiagnostic/admin/sections/ScopeForm.vue'

const MODEL = {
  index: '07',
  title: 'Alcance',
  considerationsText: 'Solo web\nSin migración',
}

describe('WebAppDiagnostic admin ScopeForm', () => {
  it('prefills the fields from the model value', () => {
    const wrapper = mount(ScopeForm, { props: { modelValue: { ...MODEL } } })
    const inputs = wrapper.findAll('input')
    expect(inputs[0].element.value).toBe('07')
    expect(inputs[1].element.value).toBe('Alcance')
    expect(wrapper.find('textarea').element.value).toBe('Solo web\nSin migración')
  })

  it('emits the updated model when editing the title', async () => {
    const wrapper = mount(ScopeForm, { props: { modelValue: { ...MODEL } } })
    await wrapper.findAll('input')[1].setValue('Alcance ajustado')
    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted.at(-1)[0].title).toBe('Alcance ajustado')
  })

  it('emits the updated model when editing the considerations text', async () => {
    const wrapper = mount(ScopeForm, { props: { modelValue: { ...MODEL } } })
    await wrapper.find('textarea').setValue('Nueva línea')
    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted.at(-1)[0].considerationsText).toBe('Nueva línea')
  })

  it('syncs external model changes into the form', async () => {
    const wrapper = mount(ScopeForm, { props: { modelValue: { ...MODEL } } })
    await wrapper.setProps({ modelValue: { ...MODEL, title: 'Desde afuera' } })
    expect(wrapper.findAll('input')[1].element.value).toBe('Desde afuera')
  })
})
