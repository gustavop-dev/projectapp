import { mount } from '@vue/test-utils'

import DocumentSearchInput from '../../components/panel/documents/DocumentSearchInput.vue'
import BaseInput from '../../components/base/BaseInput.vue'

function mountInput(props = {}) {
  return mount(DocumentSearchInput, {
    props: { modelValue: '', ...props },
    global: { components: { BaseInput } },
  })
}

describe('DocumentSearchInput', () => {
  it('emits the typed value', async () => {
    const wrapper = mountInput()
    await wrapper.find('input[type="search"]').setValue('propuesta')
    expect(wrapper.emitted('update:modelValue')).toEqual([['propuesta']])
  })

  it('hides the clear button while empty', () => {
    const wrapper = mountInput()
    expect(wrapper.find('button[aria-label="Limpiar búsqueda"]').exists()).toBe(false)
  })

  it('clears the value from the clear button', async () => {
    const wrapper = mountInput({ modelValue: 'algo' })
    await wrapper.find('button[aria-label="Limpiar búsqueda"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([['']])
  })

  it('honors a custom placeholder', () => {
    const wrapper = mountInput({ placeholder: 'Buscar contratos...' })
    expect(wrapper.find('input[type="search"]').attributes('placeholder')).toBe('Buscar contratos...')
  })
})
