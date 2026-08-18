import { mount } from '@vue/test-utils';
import BaseSegmentedMulti from '~/components/base/BaseSegmentedMulti.vue';

const OPTIONS = [
  { value: '', label: 'Todos' },
  { value: 'pending', label: 'Sin pagos' },
  { value: 'partial', label: 'Parcial' },
  { value: 'paid', label: 'Pagado' },
];

function mountControl(props = {}) {
  return mount(BaseSegmentedMulti, {
    props: { options: OPTIONS, label: 'Cobro', testIdPrefix: 'cobro', ...props },
  });
}

const buttonFor = (wrapper, label) =>
  wrapper.findAll('button').find((b) => b.text() === label);

describe('BaseSegmentedMulti', () => {
  it('is a toggle group, not a tablist', () => {
    // A tablist reporting two selected tabs lies to a screen reader; that is
    // the whole reason this is a separate component from BaseSegmented.
    const wrapper = mountControl();
    expect(wrapper.find('[role="group"]').exists()).toBe(true);
    expect(wrapper.find('[role="tablist"]').exists()).toBe(false);
    expect(wrapper.find('[role="group"]').attributes('aria-label')).toBe('Cobro');
  });

  it('marks a value without dropping the one already marked', async () => {
    const wrapper = mountControl({ modelValue: ['pending'] });
    await buttonFor(wrapper, 'Parcial').trigger('click');
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual(['pending', 'partial']);
  });

  it('unmarks a value that was already marked', async () => {
    const wrapper = mountControl({ modelValue: ['pending', 'partial'] });
    await buttonFor(wrapper, 'Sin pagos').trigger('click');
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual(['partial']);
  });

  it('emits in options order regardless of click order', async () => {
    // Saved tabs are compared with a deep equal, so a click-ordered array
    // would show the "drifted" dot purely because of how it was clicked.
    const wrapper = mountControl({ modelValue: ['paid'] });
    await buttonFor(wrapper, 'Sin pagos').trigger('click');
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual(['pending', 'paid']);
  });

  it('"Todos" clears the dimension instead of being a value in it', async () => {
    const wrapper = mountControl({ modelValue: ['pending', 'partial'] });
    await buttonFor(wrapper, 'Todos').trigger('click');
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual([]);
  });

  it('shows "Todos" as the active one when nothing is marked', () => {
    const wrapper = mountControl({ modelValue: [] });
    expect(buttonFor(wrapper, 'Todos').attributes('aria-pressed')).toBe('true');
    expect(buttonFor(wrapper, 'Parcial').attributes('aria-pressed')).toBe('false');
  });

  it('reports every marked value as pressed', () => {
    const wrapper = mountControl({ modelValue: ['pending', 'partial'] });
    expect(buttonFor(wrapper, 'Todos').attributes('aria-pressed')).toBe('false');
    expect(buttonFor(wrapper, 'Sin pagos').attributes('aria-pressed')).toBe('true');
    expect(buttonFor(wrapper, 'Parcial').attributes('aria-pressed')).toBe('true');
    expect(buttonFor(wrapper, 'Pagado').attributes('aria-pressed')).toBe('false');
  });

  it('emits nothing when "Todos" is clicked with nothing marked', async () => {
    const wrapper = mountControl({ modelValue: [] });
    await buttonFor(wrapper, 'Todos').trigger('click');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
  });

  it('derives a testid per option and calls the clear one "all"', () => {
    const wrapper = mountControl();
    expect(wrapper.find('[data-testid="cobro-all"]').text()).toBe('Todos');
    expect(wrapper.find('[data-testid="cobro-partial"]').text()).toBe('Parcial');
  });

  it('ignores clicks while disabled', async () => {
    const wrapper = mountControl({ disabled: true });
    await buttonFor(wrapper, 'Parcial').trigger('click');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
  });

  it('locks a single option without locking the rest', async () => {
    const wrapper = mountControl({
      options: [{ value: '', label: 'Todos' }, { value: 'a', label: 'A', disabled: true }],
    });
    await buttonFor(wrapper, 'A').trigger('click');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    expect(buttonFor(wrapper, 'A').attributes('disabled')).toBe('');
    expect(buttonFor(wrapper, 'Todos').attributes('disabled')).toBeUndefined();
  });

  it('accepts bare string options', () => {
    const wrapper = mountControl({ options: ['uno', 'dos'], modelValue: ['dos'] });
    expect(buttonFor(wrapper, 'dos').attributes('aria-pressed')).toBe('true');
  });
});
