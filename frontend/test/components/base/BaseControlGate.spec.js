import { mount } from '@vue/test-utils'
import BaseControlGate from '../../../components/base/BaseControlGate.vue'

jest.mock('@vueuse/core', () => ({ onClickOutside: jest.fn() }))

function mountGate(props = {}) {
  return mount(BaseControlGate, {
    props: {
      label: 'Previsualizar no disponible',
      testid: 'preview-gate',
      ...props,
    },
    slots: {
      default: '<button disabled>Previsualizar</button>',
    },
    global: {
      stubs: { Transition: false },
    },
  })
}

describe('BaseControlGate', () => {
  it('shows every distinct blocker next to the control', () => {
    const wrapper = mountGate({
      reasons: ['Selecciona un cliente.', '', 'Selecciona un ingreso.', 'Selecciona un cliente.'],
    })

    const reasons = wrapper.get('[data-testid="preview-gate-reasons"]')
    expect(reasons.text()).toContain('Selecciona un cliente.')
    expect(reasons.text()).toContain('Selecciona un ingreso.')
    expect(reasons.findAll('li')).toHaveLength(2)
  })

  it('makes a native disabled control explanation keyboard reachable', () => {
    const wrapper = mountGate({ reasons: ['Agrega un correo válido.'] })
    const trigger = wrapper.get('[data-testid="preview-gate-trigger"]')

    expect(trigger.attributes('tabindex')).toBe('0')
    expect(trigger.attributes('aria-label')).toContain('Agrega un correo válido.')
    expect(trigger.attributes('aria-describedby')).toBe(
      wrapper.get('[data-testid="preview-gate-reasons"]').attributes('id'),
    )
  })

  it('keeps non-resolvable reasons accessible without showing adjacent copy', () => {
    const wrapper = mountGate({
      reasons: ['El documento emitido es de solo lectura.'],
      visible: false,
    })

    expect(wrapper.get('[data-testid="preview-gate-reasons"]').classes()).toContain('sr-only')
    expect(wrapper.get('[data-testid="preview-gate-trigger"]').attributes('aria-label'))
      .toContain('El documento emitido es de solo lectura.')
  })

  it('removes the focus proxy semantics when the control is available', () => {
    const wrapper = mountGate({ reasons: [] })
    const trigger = wrapper.get('[data-testid="preview-gate-trigger"]')

    expect(trigger.attributes('tabindex')).toBeUndefined()
    expect(trigger.attributes('aria-label')).toBeUndefined()
    expect(trigger.attributes('aria-describedby')).toBeUndefined()
    expect(wrapper.get('button').text()).toBe('Previsualizar')
  })

  it('keeps the same control element when its blockers are resolved', async () => {
    const wrapper = mountGate({ reasons: ['Agrega un correo válido.'] })
    const blockedButton = wrapper.get('button').element

    await wrapper.setProps({ reasons: [] })

    expect(wrapper.get('button').element).toBe(blockedButton)
  })
})
