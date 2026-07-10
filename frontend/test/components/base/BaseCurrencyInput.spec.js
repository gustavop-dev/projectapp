/**
 * Tests for BaseCurrencyInput.
 *
 * Covers: live es-CO thousands formatting, numeric emit, null on empty,
 * decimal comma support, external modelValue prefill/reset.
 */
import { mount } from '@vue/test-utils';
import BaseCurrencyInput from '../../../components/base/BaseCurrencyInput.vue';

function mountInput(props = {}) {
  return mount(BaseCurrencyInput, { props });
}

async function type(wrapper, value) {
  const input = wrapper.find('input');
  await input.setValue(value);
  return input;
}

describe('BaseCurrencyInput', () => {
  it('formats thousands while typing and emits the number', async () => {
    const wrapper = mountInput();
    const input = await type(wrapper, '1234567');

    expect(input.element.value).toBe('1.234.567');
    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted[emitted.length - 1]).toEqual([1234567]);
  });

  it('strips non-numeric characters', async () => {
    const wrapper = mountInput();
    const input = await type(wrapper, '12a3.4b5');

    expect(input.element.value).toBe('12.345');
    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted[emitted.length - 1]).toEqual([12345]);
  });

  it('emits null when cleared', async () => {
    const wrapper = mountInput({ modelValue: 5000 });
    await type(wrapper, '');

    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted[emitted.length - 1]).toEqual([null]);
  });

  it('ignores commas when decimals is 0', async () => {
    const wrapper = mountInput();
    const input = await type(wrapper, '1234,56');

    expect(input.element.value).toBe('123.456');
    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted[emitted.length - 1]).toEqual([123456]);
  });

  it('accepts one decimal comma when decimals > 0', async () => {
    const wrapper = mountInput({ decimals: 2 });
    const input = await type(wrapper, '1234,56');

    expect(input.element.value).toBe('1.234,56');
    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted[emitted.length - 1]).toEqual([1234.56]);
  });

  it('prefills a formatted value from modelValue', () => {
    const wrapper = mountInput({ modelValue: '2616581' });

    expect(wrapper.find('input').element.value).toBe('2.616.581');
  });

  it('reformats when modelValue changes externally', async () => {
    const wrapper = mountInput({ modelValue: 1000 });
    await wrapper.setProps({ modelValue: 2500000 });

    expect(wrapper.find('input').element.value).toBe('2.500.000');
  });

  it('clears the display when modelValue resets to null', async () => {
    const wrapper = mountInput({ modelValue: 1000 });
    await wrapper.setProps({ modelValue: null });

    expect(wrapper.find('input').element.value).toBe('');
  });
});
