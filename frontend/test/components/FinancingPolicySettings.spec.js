import { mount } from '@vue/test-utils'

import FinancingPolicySettings from '../../components/Financing/PolicySettings.vue'

const mockPublishSettings = jest.fn()
const mockRequestConfirm = jest.fn()

jest.mock('../../stores/financing_agreements', () => ({
  useFinancingAgreementsStore: () => ({
    isSaving: false,
    publishSettings: mockPublishSettings,
  }),
}))

jest.mock('../../composables/useConfirmModal', () => ({
  useConfirmModal: () => ({
    confirmState: { open: false },
    requestConfirm: mockRequestConfirm,
    handleConfirmed: jest.fn(),
    handleCancelled: jest.fn(),
  }),
}))

jest.mock('../../composables/usePanelNotify', () => ({
  usePanelNotify: () => ({ success: jest.fn(), error: jest.fn() }),
}))

global.useI18n = jest.fn(() => ({
  locale: { value: 'es-co' },
  t: (key, params = {}) => `${key}${params.version ? ` ${params.version}` : ''}`,
}))

const current = {
  id: 2,
  version: 2,
  minimum_project_value_cop: '20000000.00',
  maximum_project_value_cop: '140000000.00',
  financing_months: 12,
  maximum_financed_percent: '80.00',
  minimum_initial_payment_percent: '20.00',
  late_hosting_increase_percent: '2.00',
  installment_due_day_start: 1,
  installment_due_day_end: 5,
  created_by_name: 'Sistema',
  created_at: '2026-09-01T12:00:00Z',
}

const BaseInput = {
  inheritAttrs: false,
  props: ['modelValue', 'type', 'readonly'],
  emits: ['update:modelValue'],
  template: '<input v-bind="$attrs" :type="type" :value="modelValue" :readonly="readonly" @input="$emit(\'update:modelValue\', $event.target.value)">',
}

const BaseFormField = {
  props: ['error'],
  template: '<label><slot /><span v-if="error" role="alert">{{ error }}</span></label>',
}

const BaseButton = {
  inheritAttrs: false,
  props: ['type'],
  emits: ['click'],
  template: '<button v-bind="$attrs" :type="type || \'button\'" @click="$emit(\'click\', $event)"><slot /></button>',
}

function mountSettings() {
  return mount(FinancingPolicySettings, {
    props: {
      settings: {
        current,
        history: [current],
        usd_exchange_rate: '4000.00',
      },
    },
    global: {
      stubs: {
        ConfirmModal: { template: '<div />' },
        BaseAlert: { template: '<div><slot /></div>' },
        BaseBadge: { template: '<span><slot /></span>' },
        BaseInput,
        BaseFormField,
        BaseButton,
      },
    },
  })
}

describe('FinancingPolicySettings', () => {
  beforeEach(() => {
    mockPublishSettings.mockReset()
    mockRequestConfirm.mockReset().mockResolvedValue(true)
  })

  it('shows the derived minimum contribution', () => {
    const wrapper = mountSettings()

    expect(wrapper.get('[data-testid="financing-settings-minimum-initial"]')
      .element.value).toBe('20.00%')
  })

  it('shows a range error after an invalid publication attempt', async () => {
    const wrapper = mountSettings()
    await wrapper.get('[data-testid="financing-settings-maximum"]').setValue('10000000')

    await wrapper.get('form').trigger('submit')

    expect(wrapper.get('[role="alert"]').text())
      .toContain('financing.settings.validation.maximum')
    expect(mockPublishSettings).not.toHaveBeenCalled()
  })

  it('emits the published revision returned by the server', async () => {
    const response = {
      current: { ...current, id: 3, version: 3, financing_months: 18 },
      history: [],
    }
    mockPublishSettings.mockResolvedValue({ success: true, data: response })
    const wrapper = mountSettings()
    await wrapper.get('[data-testid="financing-settings-months"]').setValue('18')

    await wrapper.get('form').trigger('submit')
    await Promise.resolve()

    expect(mockPublishSettings).toHaveBeenCalledWith(expect.objectContaining({
      financing_months: '18',
    }))
    expect(wrapper.emitted('published')).toEqual([[response]])
  })
})
