import { mount } from '@vue/test-utils';
import ExpenseFormModal from '../../../components/accounting/ExpenseFormModal.vue';

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
  return mount(ExpenseFormModal, {
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
        BaseTextarea: {
          props: ['modelValue', 'rows', 'size', 'error', 'placeholder', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BaseSelect: {
          props: ['modelValue', 'options', 'size', 'error', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option></select>',
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

describe('ExpenseFormModal', () => {
  it('emits submit with the company ledger and split amounts by default', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="text"]').setValue('Windsurf, Marzo');
    await wrapper.find('input[type="month"]').setValue('2026-03');
    await wrapper.find('[data-testid="split-total"]').setValue('3000000');
    await wrapper.find('[data-testid="split-gustavo"]').setValue('1500000');
    await wrapper.find('[data-testid="split-carlos"]').setValue('1500000');

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')).toHaveLength(1);
    expect(wrapper.emitted('submit')[0][0]).toEqual({
      concept: 'Windsurf, Marzo',
      period_date: '2026-03',
      category: 'business',
      ledger: 'company',
      total_amount: '3000000',
      gustavo_amount: '1500000',
      carlos_amount: '1500000',
      notes: '',
    });
  });

  it('personal ledger hides split and omits split amounts', async () => {
    const wrapper = mountModal();

    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(true);

    await segmentedButton(wrapper, 'Personal Gustavo').trigger('click');

    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('Valor');

    await wrapper.find('input[type="text"]').setValue('Aporte Carro Onix');
    await wrapper.find('input[type="month"]').setValue('2026-06');
    await wrapper.find('input[type="number"]').setValue('3000000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload.ledger).toBe('gustavo');
    expect(payload.total_amount).toBe('3000000');
    expect(payload).not.toHaveProperty('gustavo_amount');
    expect(payload).not.toHaveProperty('carlos_amount');
  });

  it('prefills the ledger from the record in edit mode', () => {
    const wrapper = mountModal({
      record: {
        concept: 'Aporte Interes Credito',
        period: '2026-06',
        category: 'personal',
        ledger: 'gustavo',
        total_amount: '2616581',
        gustavo_amount: '2616581',
        carlos_amount: '0',
        notes: '',
      },
    });

    expect(wrapper.text()).toContain('Editar Gasto');
    expect(segmentedButton(wrapper, 'Personal Gustavo').attributes('aria-selected')).toBe('true');
    expect(wrapper.find('[data-testid="partner-split-stub"]').exists()).toBe(false);
  });
});
