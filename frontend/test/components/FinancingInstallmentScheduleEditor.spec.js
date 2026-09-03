import { mount } from '@vue/test-utils'

import FinancingInstallmentScheduleEditor from '../../components/Financing/InstallmentScheduleEditor.vue'

global.useI18n = jest.fn(() => ({
  locale: { value: 'es-co' },
  t: (key, params = {}) => (key.endsWith('.total') ? `Total: ${params.amount}` : key),
}))


const BaseFormField = {
  template: '<label><slot /></label>',
}

const BaseInput = {
  inheritAttrs: false,
  props: ['modelValue', 'disabled', 'type', 'min', 'step', 'size'],
  emits: ['update:modelValue'],
  template: `
    <input
      v-bind="$attrs"
      :value="modelValue"
      :disabled="disabled"
      :type="type"
      :min="min"
      :step="step"
      @input="$emit('update:modelValue', $event.target.value)"
    >
  `,
}

const schedule = [
  { number: 1, due_date: '2026-03-05', amount: '40.00' },
  { number: 2, due_date: '2026-04-05', amount: '60.00' },
]

function mountSchedule(props = {}) {
  return mount(FinancingInstallmentScheduleEditor, {
    props: { modelValue: schedule, currency: 'COP', ...props },
    global: { components: { BaseFormField, BaseInput } },
  })
}

describe('FinancingInstallmentScheduleEditor', () => {
  it('displays the exact installment total', () => {
    const wrapper = mountSchedule()

    expect(wrapper.get('[data-testid="financing-schedule-total"]').text())
      .toContain('100')
  })

  it('emits an immutable row update after editing an amount', async () => {
    const wrapper = mountSchedule()

    await wrapper.get('[data-testid="financing-installment-amount-1"]')
      .setValue('45.00')

    expect(wrapper.emitted('update:modelValue')).toEqual([[
      [
        { number: 1, due_date: '2026-03-05', amount: '45.00' },
        { number: 2, due_date: '2026-04-05', amount: '60.00' },
      ],
    ]])
    expect(schedule[0].amount).toBe('40.00')
  })

  it('renders a schedule validation error', () => {
    const wrapper = mountSchedule({ error: ['La suma debe coincidir con el saldo.'] })

    expect(wrapper.get('[role="alert"]').text())
      .toContain('La suma debe coincidir con el saldo.')
  })
})
