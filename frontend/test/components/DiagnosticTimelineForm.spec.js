import { mount } from '@vue/test-utils'

import TimelineForm from '../../components/WebAppDiagnostic/admin/sections/TimelineForm.vue'

const MODEL = {
  index: '06',
  title: 'Cronograma',
  intro: 'Así se reparte.',
  distributionTitle: 'Día a día',
  distribution: [
    { dayRange: 'Día 1-2', description: 'Levantamiento' },
    { dayRange: 'Día 3', description: 'Entrega' },
  ],
}

const mountForm = () => mount(TimelineForm, { props: { modelValue: { ...MODEL } } })

describe('WebAppDiagnostic admin TimelineForm', () => {
  it('prefills the fields and renders one row per distribution item', () => {
    const wrapper = mountForm()
    expect(wrapper.findAll('input')[1].element.value).toBe('Cronograma')
    expect(wrapper.findAll('[placeholder="Día X"]')).toHaveLength(2)
    expect(wrapper.findAll('[placeholder="Descripción"]')[1].element.value).toBe('Entrega')
  })

  it('emits the updated model when editing the title', async () => {
    const wrapper = mountForm()
    await wrapper.findAll('input')[1].setValue('Cronograma ajustado')
    expect(wrapper.emitted('update:modelValue').at(-1)[0].title).toBe('Cronograma ajustado')
  })

  it('appends an empty row from the add button', async () => {
    const wrapper = mountForm()
    await wrapper.get('button').trigger('click')
    expect(wrapper.findAll('[placeholder="Día X"]')).toHaveLength(3)
    expect(wrapper.emitted('update:modelValue').at(-1)[0].distribution).toHaveLength(3)
  })

  it('removes a row from its delete button', async () => {
    const wrapper = mountForm()
    await wrapper.findAll('button').at(-1).trigger('click')
    expect(wrapper.findAll('[placeholder="Día X"]')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue').at(-1)[0].distribution).toHaveLength(1)
  })
})
