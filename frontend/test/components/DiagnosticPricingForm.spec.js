import { mount } from '@vue/test-utils';
import DiagnosticPricingForm from '../../components/WebAppDiagnostic/DiagnosticPricingForm.vue';

const DEFAULT_MODEL = {
  investment_amount: 5000,
  currency: 'COP',
  duration_label: '2 semanas',
  payment_terms: { initial_pct: 50, final_pct: 50 },
};

function mountForm(props = {}) {
  return mount(DiagnosticPricingForm, {
    props: { modelValue: DEFAULT_MODEL, busy: false, ...props },
  });
}

describe('DiagnosticPricingForm', () => {
  it('renders investment_amount input with value from modelValue', () => {
    const wrapper = mountForm();

    const input = wrapper.find('input[type="number"]');
    expect(input.element.value).toBe('5000');
  });

  it('renders currency dropdown with COP and USD options', () => {
    const wrapper = mountForm();

    const select = wrapper.find('select');
    const options = select.findAll('option').map((o) => o.text());
    expect(options).toContain('COP');
    expect(options).toContain('USD');
  });

  it('update emits update:modelValue with the new investment_amount', async () => {
    const wrapper = mountForm();

    const input = wrapper.find('input[type="number"]');
    await input.setValue('9000');
    await input.trigger('input');

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[0][0].investment_amount).toBe('9000');
  });

  it('updatePayment emits update:modelValue with initial_pct coerced to Number', async () => {
    const wrapper = mountForm();

    const initialPctInput = wrapper.findAll('input[type="number"]')[1];
    await initialPctInput.setValue('30');
    await initialPctInput.trigger('input');

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[0][0].payment_terms.initial_pct).toBe(30);
  });

  it('updatePayment emits update:modelValue with final_pct coerced to Number', async () => {
    const wrapper = mountForm();

    const finalPctInput = wrapper.findAll('input[type="number"]')[2];
    await finalPctInput.setValue('70');
    await finalPctInput.trigger('input');

    const events = wrapper.emitted('update:modelValue');
    expect(events).toBeTruthy();
    expect(events[0][0].payment_terms.final_pct).toBe(70);
  });

  it('submit button emits submit when form is submitted', async () => {
    const wrapper = mountForm();

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('submit')).toBeTruthy();
  });

  it('submit button is disabled when busy is true', () => {
    const wrapper = mountForm({ busy: true });

    const button = wrapper.find('button[type="submit"]');
    expect(button.attributes('disabled')).toBeDefined();
  });

  it('payment computed reflects payment_terms from modelValue', () => {
    const wrapper = mountForm({
      modelValue: { ...DEFAULT_MODEL, payment_terms: { initial_pct: 20, final_pct: 80 } },
    });

    const inputs = wrapper.findAll('input[type="number"]');
    expect(inputs[1].element.value).toBe('20');
    expect(inputs[2].element.value).toBe('80');
  });

  it('updatePayment defaults to 0 when value is not a valid number', async () => {
    const wrapper = mountForm();

    const initialPctInput = wrapper.findAll('input[type="number"]')[1];
    await initialPctInput.setValue('');
    await initialPctInput.trigger('input');

    const events = wrapper.emitted('update:modelValue');
    expect(events[0][0].payment_terms.initial_pct).toBe(0);
  });
});
