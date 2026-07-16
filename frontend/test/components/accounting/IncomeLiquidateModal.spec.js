import { mount } from '@vue/test-utils';
import IncomeLiquidateModal from '../../../components/accounting/IncomeLiquidateModal.vue';

const PartnerSplitInputStub = {
  name: 'PartnerSplitInput',
  props: ['total', 'gustavoAmount', 'carlosAmount'],
  emits: ['update:total', 'update:gustavoAmount', 'update:carlosAmount'],
  template: `
    <div data-testid="partner-split-stub">
      <input data-testid="split-total" :value="total" @input="$emit('update:total', $event.target.value)" />
      <input data-testid="split-gustavo" :value="gustavoAmount" @input="$emit('update:gustavoAmount', $event.target.value)" />
      <input data-testid="split-carlos" :value="carlosAmount" @input="$emit('update:carlosAmount', $event.target.value)" />
    </div>
  `,
};

const expectedRecord = {
  id: 42,
  concept: 'Kore v2 (Fase 1) - Inicio 40%',
  kind: 'expected',
  ledger: 'company',
  period_label: 'Agosto 2026',
  period: '2026-08',
  total_amount: '1000000.00',
  paid_amount: '400000.00',
  pending_amount: '600000.00',
  payment_status: 'partial',
};

function mountModal(props = {}) {
  return mount(IncomeLiquidateModal, {
    props: {
      open: true,
      record: expectedRecord,
      saving: false,
      ...props,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['update:modelValue', 'close'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        BaseFormField: {
          props: ['label', 'hint', 'error', 'required', 'for', 'size'],
          template: '<div><label v-if="label">{{ label }}</label><slot /></div>',
        },
        BaseInput: {
          props: ['modelValue', 'type', 'size', 'error', 'placeholder', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<input :type="type || \'text\'" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseCurrencyInput: {
          props: ['modelValue', 'decimals', 'size', 'error', 'placeholder', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<input type="text" inputmode="numeric" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseTextarea: {
          props: ['modelValue', 'rows', 'size', 'error', 'placeholder', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseSegmented: {
          props: ['modelValue', 'options', 'size', 'fullWidth'],
          emits: ['update:modelValue'],
          template:
            '<div><button v-for="o in options" :key="o.value" type="button" @click="$emit(\'update:modelValue\', o.value)">{{ o.label }}</button></div>',
        },
        BaseButton: {
          props: ['variant', 'size', 'type', 'loading', 'disabled'],
          emits: ['click'],
          template:
            '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
        },
        PartnerSplitInput: PartnerSplitInputStub,
      },
    },
  });
}

describe('IncomeLiquidateModal', () => {
  it('names the expected income being settled', () => {
    const wrapper = mountModal();

    expect(wrapper.text()).toContain('Liquidar ingreso esperado');
    expect(wrapper.text()).toContain('Kore v2 (Fase 1) - Inicio 40%');
    expect(wrapper.text()).toContain('Agosto 2026');
  });

  it('prefills the amount with what is still owed, not the full projection', () => {
    // They often pay late AND short, so the remainder is the useful default.
    const wrapper = mountModal();

    expect(wrapper.find('[data-testid="split-total"]').element.value)
      .toBe('600000.00');
    expect(wrapper.find('[data-testid="income-liquidate-pending"]').text())
      .toContain('600.000');
  });

  it('leaves the month empty so the real payment month is chosen', () => {
    const wrapper = mountModal();

    expect(wrapper.find('input[type="month"]').element.value).toBe('');
  });

  it('submits a liquid record linked to the expected one', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="month"]').setValue('2026-11');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.kind).toBe('liquid');
    expect(payload.expected_income).toBe(42);
    expect(payload.period_date).toBe('2026-11');
    expect(payload.total_amount).toBe('600000.00');
    expect(payload.ledger).toBe('company');
  });

  it('allows overriding the amount for a partial payment', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="split-total"]').setValue('250000');
    await wrapper.find('input[type="month"]').setValue('2026-09');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.total_amount).toBe('250000');
  });

  it('falls back to the total when the record has no pending amount', () => {
    const wrapper = mountModal({
      record: { ...expectedRecord, pending_amount: null },
    });

    expect(wrapper.find('[data-testid="split-total"]').element.value)
      .toBe('1000000.00');
  });

  it('omits the split and hides destination for a personal ledger', async () => {
    const wrapper = mountModal({
      record: { ...expectedRecord, ledger: 'gustavo' },
    });

    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Destino');

    await wrapper.find('input[type="month"]').setValue('2026-11');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.ledger).toBe('gustavo');
    expect(payload.gustavo_amount).toBeUndefined();
    expect(payload.carlos_amount).toBeUndefined();
  });

  it('emits close when Cancelar is clicked', async () => {
    const wrapper = mountModal();

    const cancel = wrapper.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancel.trigger('click');

    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
