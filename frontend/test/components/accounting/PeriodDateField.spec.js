import { mount } from '@vue/test-utils';
import PeriodDateField from '../../../components/accounting/PeriodDateField.vue';

// Host with real v-model wiring — the field's contract is two-way.
const Host = {
  components: { PeriodDateField },
  data: () => ({ value: '', exact: true }),
  template: `
    <PeriodDateField
      v-model="value"
      v-model:exact="exact"
      label-exact="Fecha"
      label-month="Mes"
      required
      input-testid="pf-input"
      toggle-testid="pf-toggle"
    />
  `,
};

function mountField(data = {}) {
  return mount(Host, {
    data: () => ({ value: '', exact: true, ...data }),
    global: {
      stubs: {
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
        BaseToggle: {
          props: ['modelValue', 'size', 'disabled', 'ariaLabel'],
          emits: ['update:modelValue'],
          template:
            '<button type="button" role="switch" :aria-checked="modelValue" @click="$emit(\'update:modelValue\', !modelValue)" />',
        },
      },
    },
  });
}

describe('PeriodDateField', () => {
  it('renders a date input with the exact label by default', () => {
    const wrapper = mountField();

    expect(wrapper.find('[data-testid="pf-input"]').attributes('type'))
      .toBe('date');
    expect(wrapper.text()).toContain('Fecha');
    expect(wrapper.text()).not.toContain('Mes');
  });

  it('downgrades to month-only keeping the typed value and back to day 1', async () => {
    const wrapper = mountField();

    await wrapper.find('[data-testid="pf-input"]').setValue('2026-11-17');
    await wrapper.find('[data-testid="pf-toggle"]').trigger('click');

    const monthInput = wrapper.find('[data-testid="pf-input"]');
    expect(monthInput.attributes('type')).toBe('month');
    expect(monthInput.element.value).toBe('2026-11');
    // quality: allow-implementation-coupling (wrapper is the v-model host, not the SUT)
    expect(wrapper.vm.value).toBe('2026-11');
    expect(wrapper.text()).toContain('Mes');

    await wrapper.find('[data-testid="pf-toggle"]').trigger('click');
    // Back to exact mode: the month is kept as its day-1 date.
    // quality: allow-implementation-coupling (wrapper is the v-model host, not the SUT)
    expect(wrapper.vm.value).toBe('2026-11-01');
    expect(wrapper.find('[data-testid="pf-input"]').element.value)
      .toBe('2026-11-01');
  });

  it('starts in month mode when the parent hands a month-only value', () => {
    const wrapper = mountField({ value: '2026-07', exact: false });

    const input = wrapper.find('[data-testid="pf-input"]');
    expect(input.attributes('type')).toBe('month');
    expect(input.element.value).toBe('2026-07');
  });

  it('leaves an empty value untouched when flipping modes', async () => {
    const wrapper = mountField();

    await wrapper.find('[data-testid="pf-toggle"]').trigger('click');

    // quality: allow-implementation-coupling (wrapper is the v-model host, not the SUT)
    expect(wrapper.vm.value).toBe('');
    expect(wrapper.find('[data-testid="pf-input"]').attributes('type'))
      .toBe('month');
  });
});

  it('keeps a full date intact when exact mode is re-enabled', async () => {
    // A parent re-syncing `exact` on open must never reset a real day to 01.
    const wrapper = mountField({ value: '2026-07-15', exact: false });

    await wrapper.find('[data-testid="pf-toggle"]').trigger('click');

    // quality: allow-implementation-coupling (wrapper is the v-model host, not the SUT)
    expect(wrapper.vm.value).toBe('2026-07-15');
    expect(wrapper.find('[data-testid="pf-input"]').element.value)
      .toBe('2026-07-15');
  });
