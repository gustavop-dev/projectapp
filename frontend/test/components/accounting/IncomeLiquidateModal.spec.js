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
          // The real component emits a NUMBER (or null when empty), not the
          // typed string — the payload assertions depend on that contract.
          template:
            '<input type="text" inputmode="numeric" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value === \'\' ? null : Number($event.target.value))" />',
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
        BaseToggle: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
        },
        BaseSelect: {
          props: ['modelValue', 'options', 'size', 'error', 'disabled', 'placeholder'],
          emits: ['update:modelValue'],
          template:
            '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-if="placeholder" value="" disabled>{{ placeholder }}</option><option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option></select>',
        },
        BaseCollapse: {
          props: ['open', 'id'],
          template: '<div v-if="open"><slot /></div>',
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

  it('defaults to the exact payment date prefilled with today', () => {
    // 20:00 local: toISOString() would already be tomorrow in Bogotá
    // (UTC-5) — this pins the local-date formatting.
    jest.useFakeTimers().setSystemTime(new Date('2026-07-27T20:00:00'));
    try {
      const wrapper = mountModal();

      const dateInput = wrapper.find('input[type="date"]');
      expect(dateInput.exists()).toBe(true);
      expect(dateInput.element.value).toBe('2026-07-27');
    } finally {
      jest.useRealTimers();
    }
  });

  it('downgrades to month-only via the toggle and back', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="date"]').setValue('2026-11-17');
    await wrapper
      .find('[data-testid="income-liquidate-exact-date"]')
      .setValue(false);

    // The typed date is kept, reduced to the month the user can fix.
    expect(wrapper.find('input[type="month"]').element.value).toBe('2026-11');

    await wrapper
      .find('[data-testid="income-liquidate-exact-date"]')
      .setValue(true);
    expect(wrapper.find('input[type="date"]').element.value).toBe('2026-11-01');
  });

  it('submits the exact payment date', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="date"]').setValue('2026-11-17');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')[0][0].period_date).toBe('2026-11-17');
  });

  it('submits a month-only settlement with no allocations', async () => {
    // `kind`, `ledger` and the parent link are derived server-side from the
    // record the settle endpoint is called on.
    const wrapper = mountModal();

    await wrapper
      .find('[data-testid="income-liquidate-exact-date"]')
      .setValue(false);
    await wrapper.find('input[type="month"]').setValue('2026-11');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.period_date).toBe('2026-11');
    expect(payload.total_amount).toBe('600000.00');
    expect(payload.deductions).toEqual([]);
    expect(payload.expected_incomes).toEqual([]);
  });

  it('defaults the destination to pocket and omits the untouched split', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="date"]').setValue('2026-11-17');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    // Money defaults into the pocket; distributing to the partners is the
    // explicit choice.
    expect(payload.destination).toBe('pocket');
    // Untouched split is omitted so the server applies its canonical
    // 50/50 (split_half) — the client never re-implements the rounding.
    expect(payload.gustavo_amount).toBeUndefined();
    expect(payload.carlos_amount).toBeUndefined();
  });

  it('sends the split when the user fills it', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="split-gustavo"]').setValue('400000');
    await wrapper.find('[data-testid="split-carlos"]').setValue('200000');
    await wrapper.find('input[type="date"]').setValue('2026-11-17');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.gustavo_amount).toBe('400000');
    expect(payload.carlos_amount).toBe('200000');
  });

  it('allows overriding the amount for a partial payment', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="split-total"]').setValue('250000');
    await wrapper.find('input[type="date"]').setValue('2026-09-15');
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

    await wrapper.find('input[type="date"]').setValue('2026-11-17');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.gustavo_amount).toBeUndefined();
    expect(payload.carlos_amount).toBeUndefined();
  });

  it('emits close when Cancelar is clicked', async () => {
    const wrapper = mountModal();

    const cancel = wrapper.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancel.trigger('click');

    expect(wrapper.emitted('close')).toBeTruthy();
  });

  // ── Shortfall (the money that did not arrive) ──

  const shortfall = (wrapper) =>
    wrapper.find('[data-testid="income-liquidate-shortfall"]');

  /** Receive less than pending so the shortfall section appears. */
  async function receiveShort(wrapper, amount = '550000') {
    await wrapper.find('[data-testid="split-total"]').setValue(amount);
  }

  const submitButton = (wrapper) =>
    wrapper.find('[data-testid="income-liquidate-submit"]');

  it('hides the shortfall section when the full pending amount is received', () => {
    const wrapper = mountModal();

    expect(shortfall(wrapper).exists()).toBe(false);
  });

  it('shows the shortfall as soon as the payment falls short', async () => {
    const wrapper = mountModal();

    await receiveShort(wrapper);

    expect(shortfall(wrapper).exists()).toBe(true);
    expect(shortfall(wrapper).text()).toContain('50.000');
  });

  it('warns that an unallocated balance stays pending', async () => {
    const wrapper = mountModal();

    await receiveShort(wrapper);

    expect(wrapper.find('[data-testid="income-liquidate-remaining"]').text())
      .toContain('quedará pendiente');
    // Not allocating is allowed — that is today's behaviour.
    expect(submitButton(wrapper).element.disabled).toBe(false);
  });

  it('submits the shortfall as a deduction', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    // The concept is an explicit choice now — rows start unselected.
    await wrapper.find('[data-testid="deduction-type-0"]').setValue('gateway_fee');
    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('50000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.deductions).toEqual([
      { type: 'gateway_fee', detail: '', amount: 50000 },
    ]);
  });

  it('submits a residual-only resolution with zero received', async () => {
    // Nothing new arrived — the whole pending was a fee. The server closes
    // the expected without creating a liquid child.
    const wrapper = mountModal();

    await wrapper.find('[data-testid="split-total"]').setValue('0');
    await wrapper.find('[data-testid="deduction-type-0"]').setValue('gateway_fee');
    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('600000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.total_amount).toBe('0');
    expect(payload.deductions).toEqual([
      { type: 'gateway_fee', detail: '', amount: 600000 },
    ]);
  });

  it('coerces an emptied amount to zero', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="split-total"]').setValue('');
    await wrapper.find('[data-testid="deduction-type-0"]').setValue('gateway_fee');
    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('600000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.total_amount).toBe(0);
  });

  it('reports the balance as fully resolved once it is allocated', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('50000');

    expect(wrapper.find('[data-testid="income-liquidate-remaining"]').text())
      .toContain('queda cerrado');
  });

  it('requires the free text when the concept is "Otro"', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    await wrapper.find('[data-testid="deduction-type-0"]').setValue('other');
    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('50000');

    expect(submitButton(wrapper).element.disabled).toBe(true);

    await wrapper
      .find('[data-testid="deduction-detail-0"]').setValue('Descuento pactado');

    expect(submitButton(wrapper).element.disabled).toBe(false);
  });

  it('submits follow-up expected incomes for a balance that will be collected', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    await wrapper
      .find('[data-testid="income-liquidate-followups-toggle"]').trigger('click');
    await wrapper.find('[data-testid="followup-concept-0"]').setValue('Saldo septiembre');
    await wrapper.find('[data-testid="followup-period-0"]').setValue('2026-09');
    await wrapper.find('[data-testid="followup-amount-0"]').setValue('50000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.expected_incomes).toEqual([
      { concept: 'Saldo septiembre', period_date: '2026-09', amount: 50000 },
    ]);
  });

  it('splits the shortfall between a deduction and a follow-up income', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    await wrapper.find('[data-testid="deduction-type-0"]').setValue('gateway_fee');
    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('8000');
    await wrapper
      .find('[data-testid="income-liquidate-followups-toggle"]').trigger('click');
    await wrapper.find('[data-testid="followup-concept-0"]').setValue('Saldo');
    await wrapper.find('[data-testid="followup-period-0"]').setValue('2026-09');
    await wrapper.find('[data-testid="followup-amount-0"]').setValue('42000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.deductions).toHaveLength(1);
    expect(payload.expected_incomes).toHaveLength(1);
  });

  it('blocks the submit when the allocation exceeds the shortfall', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    await wrapper.find('[data-testid="deduction-amount-0"]').setValue('80000');

    expect(wrapper.find('[data-testid="income-liquidate-remaining"]').text())
      .toContain('Te pasaste');
    expect(submitButton(wrapper).element.disabled).toBe(true);

    await wrapper.find('form').trigger('submit');
    expect(wrapper.emitted('submit')).toBeFalsy();
  });

  it('supports more than one follow-up expected income', async () => {
    const wrapper = mountModal();
    await receiveShort(wrapper);

    await wrapper
      .find('[data-testid="income-liquidate-followups-toggle"]').trigger('click');
    await wrapper
      .find('[data-testid="income-liquidate-add-followup"]').trigger('click');

    expect(wrapper.findAll('[data-testid^="income-liquidate-followup-"]'))
      .toHaveLength(2);
  });
});

describe('shortfall discoverability', () => {
  it('shows the hint until a shortfall appears', async () => {
    const wrapper = mountModal();

    expect(
      wrapper.find('[data-testid="income-liquidate-shortfall-hint"]').exists(),
    ).toBe(true);

    await wrapper.find('[data-testid="split-total"]').setValue('550000');

    expect(
      wrapper.find('[data-testid="income-liquidate-shortfall-hint"]').exists(),
    ).toBe(false);
  });

  it('auto-expands the deductions group when the shortfall appears', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="split-total"]').setValue('550000');

    // No toggle click: the group opens itself with a row ready to fill.
    expect(
      wrapper.find('[data-testid="income-liquidate-deduction-0"]').exists(),
    ).toBe(true);
  });

  it('does not re-expand after the user collapses the group', async () => {
    const wrapper = mountModal();
    await wrapper.find('[data-testid="split-total"]').setValue('550000');

    await wrapper
      .find('[data-testid="income-liquidate-deductions-toggle"]').trigger('click');
    expect(
      wrapper.find('[data-testid="income-liquidate-deduction-0"]').exists(),
    ).toBe(false);

    await wrapper.find('[data-testid="split-total"]').setValue('400000');

    expect(
      wrapper.find('[data-testid="income-liquidate-deduction-0"]').exists(),
    ).toBe(false);
  });
});
