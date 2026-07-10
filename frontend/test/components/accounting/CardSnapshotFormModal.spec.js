import { mount } from '@vue/test-utils';
import CardSnapshotFormModal from '../../../components/accounting/CardSnapshotFormModal.vue';

function mountModal(props = {}) {
  return mount(CardSnapshotFormModal, {
    props: {
      open: true,
      record: null,
      saving: false,
      knownCards: ['T.C 0064', 'T.C 0655'],
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
          props: ['modelValue', 'type', 'size', 'error', 'placeholder', 'disabled', 'list'],
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
        BaseButton: {
          props: ['variant', 'size', 'type', 'loading', 'disabled'],
          emits: ['click'],
          template:
            '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
        },
      },
    },
  });
}

describe('CardSnapshotFormModal', () => {
  it('defaults the snapshot date to today in create mode', () => {
    const wrapper = mountModal();
    expect(wrapper.text()).toContain('Nuevo Registro de Tarjeta');
    const today = new Date().toISOString().slice(0, 10);
    expect(wrapper.find('input[type="date"]').element.value).toBe(today);
  });

  it('prefills from the record in edit mode', () => {
    const wrapper = mountModal({
      record: {
        snapshot_date: '2026-06-17',
        card_name: 'T.C 0064',
        available_amount: '413226.00',
        debt_amount: '7586774.00',
        notes: 'Corte de junio',
      },
    });
    expect(wrapper.text()).toContain('Editar Registro de Tarjeta');
    expect(wrapper.find('input[type="date"]').element.value).toBe('2026-06-17');
    expect(wrapper.find('input[type="text"]').element.value).toBe('T.C 0064');
    expect(wrapper.find('textarea').element.value).toBe('Corte de junio');
  });

  it('emits submit with the backend field names', async () => {
    const wrapper = mountModal();
    await wrapper.find('input[type="text"]').setValue('T.C 0655');
    await wrapper.find('input[type="date"]').setValue('2026-07-03');
    const numbers = wrapper.findAll('input[inputmode="numeric"]');
    await numbers[0].setValue('500000');
    await numbers[1].setValue('2500000');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')[0][0]).toEqual({
      snapshot_date: '2026-07-03',
      card_name: 'T.C 0655',
      available_amount: 500000,
      debt_amount: 2500000,
      notes: '',
    });
  });
});
