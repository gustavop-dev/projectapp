/**
 * Tests for PocketMovementFormModal.
 *
 * Covers: the ledger selector visibility (create vs linked vs historical
 * edit), forcing company ledger on IN movements, the locked direction on
 * linked records, and the submitted payload shape.
 */
import { mount } from '@vue/test-utils';
import PocketMovementFormModal from '../../../components/accounting/PocketMovementFormModal.vue';

function mountModal(props = {}) {
  return mount(PocketMovementFormModal, {
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
          props: ['modelValue', 'options', 'size', 'fullWidth', 'disabled'],
          emits: ['update:modelValue'],
          template:
            '<div :data-disabled="disabled ? \'true\' : \'false\'"><button v-for="o in options" :key="o.value" type="button" :disabled="disabled" :aria-selected="modelValue === o.value" @click="!disabled && $emit(\'update:modelValue\', o.value)">{{ o.label }}</button></div>',
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

function segmentedButton(wrapper, label) {
  return wrapper.findAll('button').find((b) => b.text() === label);
}

const LINKED_RECORD = {
  id: 4,
  concept: 'Pago dominio',
  movement_date: '2026-04-17',
  direction: 'out',
  amount: '150000.00',
  is_auto_managed: true,
  linked_ledger: 'gustavo',
  notes: '',
};

describe('PocketMovementFormModal', () => {
  it('shows the ledger selector in create mode', () => {
    const wrapper = mountModal();

    expect(wrapper.text()).toContain('Contabilidad');
    expect(segmentedButton(wrapper, 'Personal Gustavo')).toBeTruthy();
  });

  it('forces the company ledger while the direction is IN', async () => {
    const wrapper = mountModal();

    // Default direction is 'in': the ledger segmented is disabled.
    expect(wrapper.text()).toContain(
      'Los ingresos al bolsillo siempre son de la empresa.',
    );

    await segmentedButton(wrapper, 'Egreso').trigger('click');
    await segmentedButton(wrapper, 'Personal Carlos').trigger('click');
    await segmentedButton(wrapper, 'Ingreso').trigger('click');

    // Flipping back to IN resets the ledger to company.
    expect(
      segmentedButton(wrapper, 'Empresa').attributes('aria-selected'),
    ).toBe('true');
  });

  it('locks the direction and prefills the ledger on linked records', () => {
    const wrapper = mountModal({ record: LINKED_RECORD });

    expect(wrapper.text()).toContain(
      'La dirección se fija al crear el movimiento vinculado.',
    );
    expect(segmentedButton(wrapper, 'Egreso').attributes('disabled'))
      .toBeDefined();
    expect(
      segmentedButton(wrapper, 'Personal Gustavo').attributes('aria-selected'),
    ).toBe('true');
  });

  it('hides the ledger selector when editing an unlinked movement', () => {
    const wrapper = mountModal({
      record: { ...LINKED_RECORD, is_auto_managed: false, linked_ledger: null },
    });

    expect(wrapper.text()).not.toContain('Contabilidad');
  });

  it('includes the ledger in the submitted payload for egresos', async () => {
    const wrapper = mountModal();

    await wrapper.find('input[type="text"]').setValue('Pago hosting');
    await wrapper.find('input[type="date"]').setValue('2026-05-02');
    await segmentedButton(wrapper, 'Egreso').trigger('click');
    await segmentedButton(wrapper, 'Personal Carlos').trigger('click');
    await wrapper.find('input[inputmode="numeric"]').setValue('90000');
    await wrapper.find('form').trigger('submit');

    const payload = wrapper.emitted('submit')[0][0];
    expect(payload).toMatchObject({
      concept: 'Pago hosting',
      movement_date: '2026-05-02',
      direction: 'out',
      amount: 90000,
      ledger: 'carlos',
    });
  });
});
