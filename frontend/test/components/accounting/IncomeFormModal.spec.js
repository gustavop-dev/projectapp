import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import IncomeFormModal from '../../../components/accounting/IncomeFormModal.vue';

jest.mock('../../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const ClientAutocompleteStub = {
  name: 'ClientAutocomplete',
  props: ['modelValue', 'initialLabel', 'testId', 'placeholder'],
  emits: ['update:modelValue', 'select', 'create-new'],
  template: '<div data-testid="client-autocomplete-stub" />',
};

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

function mountModal(props = {}) {
  setActivePinia(createPinia());
  return mount(IncomeFormModal, {
    props: {
      open: true,
      record: null,
      saving: false,
      ...props,
    },
    global: {
      stubs: {
        ClientAutocomplete: ClientAutocompleteStub,
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
            '<div><button v-for="o in options" :key="o.value" type="button" :aria-selected="modelValue === o.value" @click="$emit(\'update:modelValue\', o.value)">{{ o.label }}</button></div>',
        },
        BaseButton: {
          props: ['variant', 'size', 'type', 'loading', 'disabled'],
          emits: ['click'],
          template:
            '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
        },
        BaseToggle: {
          props: ['modelValue', 'size', 'disabled', 'ariaLabel'],
          emits: ['update:modelValue'],
          template:
            '<button type="button" role="switch" :aria-checked="modelValue" @click="$emit(\'update:modelValue\', !modelValue)" />',
        },
        BaseSelect: {
          props: ['modelValue', 'options', 'size', 'error', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option></select>',
        },
        PartnerSplitInput: PartnerSplitInputStub,
      },
    },
  });
}

function segmentedButton(wrapper, label) {
  return wrapper.findAll('button').find((b) => b.text() === label);
}

describe('IncomeFormModal', () => {
  it('renders an empty form in create mode', () => {
    const wrapper = mountModal();

    expect(wrapper.text()).toContain('Nuevo Ingreso');
    expect(wrapper.find('input[type="text"]').element.value).toBe('');
    // The period is the exception: it prefills with today's exact date.
    expect(wrapper.find('[data-testid="income-form-period"]').attributes('type'))
      .toBe('date');
    expect(wrapper.find('textarea').element.value).toBe('');
    expect(wrapper.find('[data-testid="split-total"]').element.value).toBe('');
    expect(wrapper.find('[data-testid="income-form-submit"]').exists()).toBe(true);
  });

  it('defaults to the exact date prefilled with today', () => {
    // 20:00 local: toISOString() would already be tomorrow in Bogotá
    // (UTC-5) — this pins the local-date formatting.
    jest.useFakeTimers().setSystemTime(new Date('2026-07-27T20:00:00'));
    try {
      const wrapper = mountModal();

      const input = wrapper.find('[data-testid="income-form-period"]');
      expect(input.attributes('type')).toBe('date');
      expect(input.element.value).toBe('2026-07-27');
    } finally {
      jest.useRealTimers();
    }
  });

  it('downgrades to month-only via the toggle keeping the typed value', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="income-form-period"]').setValue('2026-11-17');
    await wrapper.find('[data-testid="income-form-exact-date"]').trigger('click');

    const input = wrapper.find('[data-testid="income-form-period"]');
    expect(input.attributes('type')).toBe('month');
    expect(input.element.value).toBe('2026-11');
  });

  const EDIT_RECORD = {
    concept: 'Página web Acme',
    kind: 'liquid',
    period: '2026-05',
    period_date: '2026-05-01',
    destination: 'pocket',
    total_amount: '1000000',
    gustavo_amount: '600000',
    carlos_amount: '400000',
    notes: 'Pago parcial',
  };

  it('prefills the form from record in edit mode', () => {
    const wrapper = mountModal({ record: { ...EDIT_RECORD } });

    expect(wrapper.text()).toContain('Editar Ingreso');
    expect(wrapper.find('input[type="text"]').element.value).toBe('Página web Acme');
    // Edits always open as a full date; day 01 is the month-only sentinel.
    const period = wrapper.find('[data-testid="income-form-period"]');
    expect(period.attributes('type')).toBe('date');
    expect(period.element.value).toBe('2026-05-01');
    expect(wrapper.find('textarea').element.value).toBe('Pago parcial');
  });

  it('prefills the exact day from period_date in edit mode', () => {
    // `period` would truncate to the month and silently reset the day.
    const wrapper = mountModal({
      record: { ...EDIT_RECORD, period_date: '2026-05-17' },
    });

    const period = wrapper.find('[data-testid="income-form-period"]');
    expect(period.attributes('type')).toBe('date');
    expect(period.element.value).toBe('2026-05-17');
  });

  it('prefills the split amounts and pocket destination in edit mode', () => {
    const wrapper = mountModal({ record: { ...EDIT_RECORD } });

    expect(wrapper.find('[data-testid="split-total"]').element.value).toBe('1000000');
    expect(wrapper.find('[data-testid="split-gustavo"]').element.value).toBe('600000');
    expect(wrapper.find('[data-testid="split-carlos"]').element.value).toBe('400000');
    // kind=liquid makes the destination segmented visible
    expect(wrapper.text()).toContain('Destino');
    expect(segmentedButton(wrapper, 'Bolsillo ProjectApp').attributes('aria-selected')).toBe('true');
  });

  it('emits submit with backend field names including split amounts', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="text"]').setValue('Anticipo cliente');
    // Month-only entry is still possible through the toggle.
    await wrapper.find('[data-testid="income-form-exact-date"]').trigger('click');
    await wrapper.find('[data-testid="income-form-period"]').setValue('2026-06');
    await segmentedButton(wrapper, 'Líquido').trigger('click');
    await segmentedButton(wrapper, 'Bolsillo ProjectApp').trigger('click');
    await wrapper.find('[data-testid="split-total"]').setValue('1500');
    await wrapper.find('[data-testid="split-gustavo"]').setValue('900');
    await wrapper.find('[data-testid="split-carlos"]').setValue('600');
    await wrapper.find('textarea').setValue('Con nota');

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')).toHaveLength(1);
    expect(wrapper.emitted('submit')[0][0]).toEqual({
      concept: 'Anticipo cliente',
      kind: 'liquid',
      period_date: '2026-06',
      destination: 'pocket',
      ledger: 'company',
      total_amount: '1500',
      gustavo_amount: '900',
      carlos_amount: '600',
      client: null,
      project: null,
      origin: '',
      // Nulls on purpose: an edit away from hosting clears its window.
      period_start: null,
      period_end: null,
      period_cadence: '',
      notes: 'Con nota',
    });
  });

  const DUPLICATE_SEED = {
    concept: 'Kore - Hosting anual',
    kind: 'expected',
    period_date: '2027-03-01',
    period_date_source: 'hosting_cycle',
    destination: 'partners',
    ledger: 'company',
    client: 7,
    client_name: 'Ana Cliente',
    project: 3,
    project_name: 'Kore',
    origin: 'hosting',
    total_amount: '1200000.00',
    gustavo_amount: '600000.00',
    carlos_amount: '600000.00',
    notes: 'Renovar antes del corte',
  };

  it('opens as a duplicate prefilled from the seed', () => {
    const wrapper = mountModal({ seed: { ...DUPLICATE_SEED } });

    expect(wrapper.text()).toContain('Duplicar Ingreso');
    expect(wrapper.find('input[type="text"]').element.value)
      .toBe('Kore - Hosting anual');
    // A hosting seed shows the window block: the proposed date is the start.
    expect(wrapper.find('[data-testid="income-form-period-start"]').element.value)
      .toBe('2027-03-01');
    expect(wrapper.find('[data-testid="split-total"]').element.value)
      .toBe('1200000.00');
    expect(wrapper.find('textarea').element.value)
      .toBe('Renovar antes del corte');
  });

  it('leaves the date empty when the seed has no cycle to propose', () => {
    const wrapper = mountModal({
      seed: { ...DUPLICATE_SEED, period_date: null, period_date_source: null },
    });

    const period = wrapper.find('[data-testid="income-form-period-start"]');
    expect(period.element.value).toBe('');
    // Required is what forces a date before the duplicate can be saved.
    expect(period.attributes('required')).toBeDefined();
    expect(wrapper.find('[data-testid="income-form-period-hint"]').exists())
      .toBe(false);
  });

  // Counted from an original dated 2026-07-01. The server computes them so
  // the day is clamped once, in one place.
  const CYCLE_OPTIONS = [
    { months: 1, date: '2026-08-01' },
    { months: 3, date: '2026-10-01' },
    { months: 6, date: '2027-01-01' },
    { months: 12, date: '2027-07-01' },
  ];

  function seedWithCycles(overrides = {}) {
    return {
      ...DUPLICATE_SEED,
      period_date: null,
      period_date_source: null,
      cycle_options: CYCLE_OPTIONS,
      ...overrides,
    };
  }

  it('shortcuts on a hosting duplicate pick the cadence and propose the end', async () => {
    // One mechanism, not two: the shortcut writes the selector, and the end
    // fills from start + cadence (inclusive: the next cycle starts after it).
    const wrapper = mountModal({
      seed: seedWithCycles({ period_date: '2026-07-01' }),
    });

    const shortcuts = wrapper.findAll('[data-testid^="income-form-cycle-"]');
    expect(shortcuts.map((b) => b.text()))
      .toEqual(['+1 mes', '+3 meses', '+6 meses', '+1 año']);

    await wrapper.get('[data-testid="income-form-cycle-3"]').trigger('click');

    expect(wrapper.find('[data-testid="income-form-period-cadence"]').element.value)
      .toBe('quarterly');
    expect(wrapper.find('[data-testid="income-form-period-end"]').element.value)
      .toBe('2026-09-30');
  });

  it('marks the chosen cadence and moves the mark when another is picked', async () => {
    const wrapper = mountModal({ seed: seedWithCycles() });
    const pressed = () => wrapper
      .findAll('[data-testid^="income-form-cycle-"]')
      .map((b) => b.attributes('aria-pressed'));

    expect(pressed()).toEqual(['false', 'false', 'false', 'false']);

    await wrapper.get('[data-testid="income-form-cycle-1"]').trigger('click');
    expect(pressed()).toEqual(['true', 'false', 'false', 'false']);

    await wrapper.get('[data-testid="income-form-cycle-12"]').trigger('click');
    expect(pressed()).toEqual(['false', 'false', 'false', 'true']);
  });

  it('writes the shortcut in month granularity when the day is not tracked', async () => {
    // Outside hosting the shortcuts keep their original job: writing the
    // single date, in whichever granularity the toggle is on.
    const wrapper = mountModal({ seed: seedWithCycles({ origin: 'development' }) });

    await wrapper.get('[data-testid="income-form-exact-date"]').trigger('click');
    await wrapper.get('[data-testid="income-form-cycle-3"]').trigger('click');

    const period = wrapper.find('[data-testid="income-form-period"]');
    expect(period.attributes('type')).toBe('month');
    expect(period.element.value).toBe('2026-10');
  });

  it('offers no shortcuts outside a duplicate', async () => {
    const created = mountModal();
    expect(created.find('[data-testid="income-form-cycles"]').exists()).toBe(false);

    const edited = mountModal({
      record: { ...EDIT_RECORD },
      seed: seedWithCycles(),
    });
    expect(edited.find('[data-testid="income-form-cycles"]').exists()).toBe(false);
  });

  it('says where a proposed date came from, and stops once it is changed', async () => {
    const wrapper = mountModal({ seed: { ...DUPLICATE_SEED } });

    expect(wrapper.get('[data-testid="income-form-period-hint"]').text())
      .toContain('hosting');

    await wrapper.find('[data-testid="income-form-period-start"]').setValue('2027-04-15');

    expect(wrapper.find('[data-testid="income-form-period-hint"]').exists())
      .toBe(false);
  });

  it('submits the duplicate as a plain create payload', async () => {
    const wrapper = mountModal({ seed: { ...DUPLICATE_SEED } });

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')[0][0]).toEqual({
      concept: 'Kore - Hosting anual',
      kind: 'expected',
      destination: 'partners',
      ledger: 'company',
      total_amount: '1200000.00',
      gustavo_amount: '600000.00',
      carlos_amount: '600000.00',
      client: 7,
      project: 3,
      origin: 'hosting',
      // Hosting sends the window and lets the backend derive period_date
      // from its start — two values would be two chances to disagree.
      period_start: '2027-03-01',
      period_end: '',
      period_cadence: '',
      notes: 'Renovar antes del corte',
    });
  });

  describe('hosting period block', () => {
    it('swaps the single date for the window when the origin turns to hosting', async () => {
      const wrapper = mountModal();

      expect(wrapper.find('[data-testid="income-form-period"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="income-form-period-start"]').exists()).toBe(false);

      await segmentedButton(wrapper, 'Hosting').trigger('click');

      expect(wrapper.find('[data-testid="income-form-period"]').exists()).toBe(false);
      expect(wrapper.find('[data-testid="income-form-period-start"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="income-form-period-end"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="income-form-period-cadence"]').exists()).toBe(true);
    });

    it('keeps what was typed and seeds the start when switching origin', async () => {
      const wrapper = mountModal();

      await wrapper.find('input[type="text"]').setValue('Acme - Hosting');
      await wrapper.find('[data-testid="income-form-period"]').setValue('2026-11-17');
      await segmentedButton(wrapper, 'Hosting').trigger('click');

      // Only the date block changes shape; nothing already written is lost.
      expect(wrapper.find('input[type="text"]').element.value).toBe('Acme - Hosting');
      expect(wrapper.find('[data-testid="income-form-period-start"]').element.value)
        .toBe('2026-11-17');
    });

    it('proposes the inclusive end from start + cadence, editable after', async () => {
      const wrapper = mountModal();
      await segmentedButton(wrapper, 'Hosting').trigger('click');

      await wrapper.find('[data-testid="income-form-period-start"]').setValue('2026-08-15');
      await wrapper.find('[data-testid="income-form-period-cadence"]').setValue('annual');

      // Inclusive: the next cycle starts the day after this end.
      const end = wrapper.find('[data-testid="income-form-period-end"]');
      expect(end.element.value).toBe('2027-08-14');

      await end.setValue('2027-08-20');
      expect(end.element.value).toBe('2027-08-20');
    });

    it('a custom cadence proposes nothing — both dates are handwritten', async () => {
      const wrapper = mountModal();
      await segmentedButton(wrapper, 'Hosting').trigger('click');

      await wrapper.find('[data-testid="income-form-period-start"]').setValue('2026-08-15');
      await wrapper.find('[data-testid="income-form-period-cadence"]').setValue('custom');

      expect(wrapper.find('[data-testid="income-form-period-end"]').element.value).toBe('');
    });

    it('submits the window instead of the single date for hosting', async () => {
      const wrapper = mountModal();
      await segmentedButton(wrapper, 'Hosting').trigger('click');

      await wrapper.find('input[type="text"]').setValue('Acme - Hosting');
      await wrapper.find('[data-testid="income-form-period-start"]').setValue('2026-08-15');
      await wrapper.find('[data-testid="income-form-period-cadence"]').setValue('semiannual');
      await wrapper.find('form').trigger('submit');

      const payload = wrapper.emitted('submit')[0][0];
      expect(payload.period_start).toBe('2026-08-15');
      expect(payload.period_end).toBe('2027-02-14');
      expect(payload.period_cadence).toBe('semiannual');
      expect(payload.period_date).toBeUndefined();
    });

    it('hints when the seed proposed the window from the recorded period', async () => {
      const wrapper = mountModal({
        seed: {
          ...DUPLICATE_SEED,
          period_date: '2027-03-01',
          period_date_source: 'income_period',
          period_start: '2027-03-01',
          period_end: '2028-02-29',
          period_cadence: 'annual',
        },
      });

      expect(wrapper.get('[data-testid="income-form-period-hint"]').text())
        .toContain('periodicidad registrada');

      await wrapper.find('[data-testid="income-form-period-start"]').setValue('2027-04-01');

      expect(wrapper.find('[data-testid="income-form-period-hint"]').exists())
        .toBe(false);
    });
  });

  it('prefers the record over the seed, so an edit is never seeded', () => {
    const wrapper = mountModal({
      record: { ...EDIT_RECORD },
      seed: { ...DUPLICATE_SEED },
    });

    expect(wrapper.text()).toContain('Editar Ingreso');
    expect(wrapper.find('input[type="text"]').element.value).toBe('Página web Acme');
  });

  it('personal ledger hides the split and destination controls', async () => {
    const wrapper = mountModal();

    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(true);

    await segmentedButton(wrapper, 'Líquido').trigger('click');
    await segmentedButton(wrapper, 'Personal Gustavo').trigger('click');

    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Destino');
    expect(wrapper.text()).toContain('Valor');
  });

  it('personal ledger submit omits the split amounts', async () => {
    const wrapper = mountModal();

    await segmentedButton(wrapper, 'Líquido').trigger('click');
    await segmentedButton(wrapper, 'Personal Gustavo').trigger('click');
    await wrapper.find('input[type="text"]').setValue('Ingreso personal');
    await wrapper.find('[data-testid="income-form-period"]').setValue('2026-06-15');
    await wrapper.find('input[inputmode="numeric"]').setValue('54099');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.ledger).toBe('gustavo');
    expect(payload.destination).toBe('partners');
    expect(payload.total_amount).toBe(54099);
    expect(payload).not.toHaveProperty('gustavo_amount');
    expect(payload).not.toHaveProperty('carlos_amount');
  });

  it('prefills ledger from record and switching back to company restores split', async () => {
    const wrapper = mountModal({
      record: {
        concept: 'Universidad Nacional',
        kind: 'liquid',
        period: '2026-02',
        period_date: '2026-02-01',
        destination: 'partners',
        ledger: 'gustavo',
        total_amount: '1400000',
        gustavo_amount: '1400000',
        carlos_amount: '0',
        notes: '',
      },
    });

    expect(segmentedButton(wrapper, 'Personal Gustavo').attributes('aria-selected')).toBe('true');
    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(false);

    await segmentedButton(wrapper, 'Empresa').trigger('click');
    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(true);
  });

  it('always includes notes so edits can clear them', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="text"]').setValue('Sin nota');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.notes).toBe('');
  });

  it('hides destination when kind is expected and forces it back to partners', async () => {
    const wrapper = mountModal();

    // default kind is expected -> destination hidden
    expect(wrapper.text()).not.toContain('Destino');

    await segmentedButton(wrapper, 'Líquido').trigger('click');
    expect(wrapper.text()).toContain('Destino');

    await segmentedButton(wrapper, 'Bolsillo ProjectApp').trigger('click');
    await segmentedButton(wrapper, 'Esperado').trigger('click');
    expect(wrapper.text()).not.toContain('Destino');

    await wrapper.find('input[type="text"]').setValue('Ingreso esperado');
    await wrapper.find('[data-testid="income-form-period"]').setValue('2026-07-15');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.kind).toBe('expected');
    expect(payload.destination).toBe('partners');
    expect(payload.ledger).toBe('company');
  });

  it('offers Perdido as a kind', () => {
    const wrapper = mountModal();

    expect(segmentedButton(wrapper, 'Perdido')).toBeTruthy();
  });

  it('drops a pocket destination when switching to Perdido', async () => {
    // Pocket is liquid-only server-side: a stale destination would 400.
    const wrapper = mountModal();

    await segmentedButton(wrapper, 'Líquido').trigger('click');
    await segmentedButton(wrapper, 'Bolsillo ProjectApp').trigger('click');
    await segmentedButton(wrapper, 'Perdido').trigger('click');
    expect(wrapper.text()).not.toContain('Destino');

    await wrapper.find('input[type="text"]').setValue('Catherine Ruiz Candles');
    await wrapper.find('[data-testid="income-form-period"]').setValue('2026-07-15');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.kind).toBe('lost');
    expect(payload.destination).toBe('partners');
  });

  it('emits close when Cancelar is clicked', async () => {
    const wrapper = mountModal();

    const cancel = wrapper.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancel.trigger('click');

    expect(wrapper.emitted('close')).toHaveLength(1);
  });

  it('disables submit and shows Guardando... while saving', () => {
    const wrapper = mountModal({ saving: true });

    const submit = wrapper.find('[data-testid="income-form-submit"]');
    expect(submit.attributes('disabled')).toBeDefined();
    expect(submit.text()).toContain('Guardando...');
  });
});
