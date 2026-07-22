import { mount } from '@vue/test-utils'

import DeliveryStructureForm from '../../components/WebAppDiagnostic/admin/sections/DeliveryStructureForm.vue'

const MODEL = {
  index: '02',
  title: 'Estructura',
  intro: 'Tres bloques.',
  blocks: [
    { title: 'Informe', paragraphsText: 'PDF final', example: 'Ver anexo' },
    { title: 'Sesión', paragraphsText: 'Videollamada', example: '' },
  ],
}

const mountForm = () => mount(DeliveryStructureForm, { props: { modelValue: { ...MODEL } } })

describe('WebAppDiagnostic admin DeliveryStructureForm', () => {
  it('prefills the fields and renders one card per block', () => {
    const wrapper = mountForm()
    expect(wrapper.findAll('input')[1].element.value).toBe('Estructura')
    expect(wrapper.findAll('[placeholder="Título del bloque"]')).toHaveLength(2)
    expect(wrapper.findAll('[placeholder="Ejemplo (opcional)"]')[0].element.value).toBe('Ver anexo')
  })

  it('emits the updated model when editing a block title', async () => {
    const wrapper = mountForm()
    await wrapper.findAll('[placeholder="Título del bloque"]')[0].setValue('Informe final')
    expect(wrapper.emitted('update:modelValue').at(-1)[0].blocks[0].title).toBe('Informe final')
  })

  it('appends an empty block from the add button', async () => {
    const wrapper = mountForm()
    await wrapper.get('button').trigger('click')
    expect(wrapper.findAll('[placeholder="Título del bloque"]')).toHaveLength(3)
    expect(wrapper.emitted('update:modelValue').at(-1)[0].blocks).toHaveLength(3)
  })

  it('removes a block from its Quitar button', async () => {
    const wrapper = mountForm()
    await wrapper.findAll('button').at(-1).trigger('click')
    expect(wrapper.findAll('[placeholder="Título del bloque"]')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue').at(-1)[0].blocks).toHaveLength(1)
  })
})
