import { mount } from '@vue/test-utils'
import BaseSegmented from '../../../components/base/BaseSegmented.vue'
import BaseSegmentedMulti from '../../../components/base/BaseSegmentedMulti.vue'
import BaseResponsiveTabs from '../../../components/base/BaseResponsiveTabs.vue'

describe('disabled control contracts', () => {
  it('exposes a per-option reason in BaseSegmented', () => {
    const wrapper = mount(BaseSegmented, {
      props: {
        modelValue: 'all',
        options: [
          { value: 'all', label: 'Todos' },
          {
            value: 'client',
            label: 'Del cliente',
            disabled: true,
            disabledReason: 'Selecciona un cliente primero.',
          },
        ],
      },
    })

    const option = wrapper.findAll('button')[1]
    expect(option.attributes('title')).toBe('Selecciona un cliente primero.')
    expect(option.attributes('aria-label'))
      .toBe('Del cliente: Selecciona un cliente primero.')
  })

  it('exposes a control-wide reason in BaseSegmentedMulti', () => {
    const wrapper = mount(BaseSegmentedMulti, {
      props: {
        modelValue: [],
        options: [{ value: 'draft', label: 'Borrador' }],
        disabled: true,
        disabledReason: 'Espera a que termine la carga.',
      },
    })

    expect(wrapper.get('button').attributes('title'))
      .toBe('Espera a que termine la carga.')
    expect(wrapper.get('button').attributes('aria-label'))
      .toBe('Borrador: Espera a que termine la carga.')
  })

  it('carries a disabled reason through responsive tab renderings', () => {
    const wrapper = mount(BaseResponsiveTabs, {
      props: {
        modelValue: 'general',
        tabs: [
          { id: 'general', label: 'General' },
          {
            id: 'archive',
            label: 'Archivado',
            disabled: true,
            disabledReason: 'Archiva primero un registro.',
          },
        ],
      },
    })

    expect(wrapper.findAll('[role="tab"]')[1].attributes('title'))
      .toBe('Archiva primero un registro.')
    expect(wrapper.findAll('option')[1].text())
      .toContain('Archiva primero un registro.')
  })
})
