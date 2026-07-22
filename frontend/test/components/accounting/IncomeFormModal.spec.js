import { mount } from '@vue/test-utils';
import IncomeFormModal from '../../../components/accounting/IncomeFormModal.vue';

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
  return mount(IncomeFormModal, {
    props: {
      open: true,
      record: null,
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
    expect(wrapper.find('input[type="month"]').element.value).toBe('');
    expect(wrapper.find('textarea').element.value).toBe('');
    expect(wrapper.find('[data-testid="split-total"]').element.value).toBe('');
    expect(wrapper.find('[data-testid="income-form-submit"]').exists()).toBe(true);
  });

  const EDIT_RECORD = {
    concept: 'Página web Acme',
    kind: 'liquid',
    period: '2026-05',
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
    expect(wrapper.find('input[type="month"]').element.value).toBe('2026-05');
    expect(wrapper.find('textarea').element.value).toBe('Pago parcial');
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
    await wrapper.find('input[type="month"]').setValue('2026-06');
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
      notes: 'Con nota',
    });
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
    await wrapper.find('input[type="month"]').setValue('2026-06');
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
    await wrapper.find('input[type="month"]').setValue('2026-06');
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
    await wrapper.find('input[type="month"]').setValue('2026-07');
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
    await wrapper.find('input[type="month"]').setValue('2026-07');
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
