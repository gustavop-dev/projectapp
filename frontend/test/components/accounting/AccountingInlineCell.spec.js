/**
 * Tests for AccountingInlineCell.
 *
 * Covers: display by default, a single click opens the editor, Enter saves the
 * changed value, unchanged blur emits nothing, Esc cancels, money type emits
 * numbers (including negative ones), the merchant combobox and the structured
 * installments pair.
 */
import { mount } from '@vue/test-utils';
import AccountingInlineCell from '../../../components/accounting/AccountingInlineCell.vue';

function mountCell(props = {}) {
  return mount(AccountingInlineCell, {
    props: { value: 'Acme', ...props },
  });
}

async function openEditor(wrapper) {
  await wrapper.find('[data-testid="inline-cell-display"]').trigger('click');
  return wrapper.find('input');
}

describe('AccountingInlineCell', () => {
  it('renders the value (or slot) as plain display', () => {
    const wrapper = mountCell();

    expect(wrapper.find('[data-testid="inline-cell-display"]').text()).toBe('Acme');
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('contains an unbroken value inside the editable cell', () => {
    const wrapper = mountCell({ value: 'Levantamiento_Fase_4_Multi-Tenant_24082026' });
    const display = wrapper.get('[data-testid="inline-cell-display"]');
    const value = display.get('span');

    expect(display.classes()).toEqual(expect.arrayContaining([
      'w-full', 'max-w-full', 'overflow-hidden',
    ]));
    expect(value.classes()).toEqual(expect.arrayContaining([
      'min-w-0', 'max-w-full', '[overflow-wrap:anywhere]',
    ]));
  });

  it('opens an input on a single click', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    expect(input.exists()).toBe(true);
    expect(input.element.value).toBe('Acme');
  });

  it('opens the editor from the keyboard so the cell is not mouse-only', async () => {
    const wrapper = mountCell();
    const display = wrapper.find('[data-testid="inline-cell-display"]');

    expect(display.attributes('role')).toBe('button');
    expect(display.attributes('tabindex')).toBe('0');

    await display.trigger('keydown.enter');

    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('emits save with the trimmed value on Enter', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    await input.setValue('  Acme Corp  ');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([['Acme Corp']]);
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('emits nothing when the value did not change on blur', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    await input.trigger('blur');

    expect(wrapper.emitted('save')).toBeUndefined();
  });

  it('cancels on Esc without saving', async () => {
    const wrapper = mountCell();
    const input = await openEditor(wrapper);

    await input.setValue('Otro');
    await input.trigger('keydown.esc');

    expect(wrapper.emitted('save')).toBeUndefined();
    expect(wrapper.find('[data-testid="inline-cell-display"]').exists()).toBe(true);
  });

  it('money type edits through the currency input and emits a number', async () => {
    const wrapper = mountCell({ type: 'money', value: '91667.00' });
    const input = await openEditor(wrapper);

    expect(input.element.value).toBe('91.667');

    await input.setValue('120000');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[120000]]);
  });

  it('money type does not emit when the amount is unchanged', async () => {
    const wrapper = mountCell({ type: 'money', value: '91667.00' });
    const input = await openEditor(wrapper);

    await input.trigger('blur');

    expect(wrapper.emitted('save')).toBeUndefined();
  });

  it('date type opens a date input and commits the changed date on Enter', async () => {
    const wrapper = mountCell({ type: 'date', value: '2026-06-15' });
    const input = await openEditor(wrapper);

    expect(input.attributes('type')).toBe('date');
    expect(input.element.value).toBe('2026-06-15');

    await input.setValue('2026-06-20');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([['2026-06-20']]);
  });

  const CATEGORY_OPTIONS = [
    { value: 'software', label: 'Software y suscripciones' },
    { value: 'fuel', label: 'Gasolina' },
  ];

  async function openSelect(wrapper) {
    await wrapper.find('[data-testid="inline-cell-display"]').trigger('click');
    return wrapper.find('select');
  }

  it('select type emits the option value as soon as it changes', async () => {
    const wrapper = mountCell({
      type: 'select', value: 'software', options: CATEGORY_OPTIONS,
    });
    const select = await openSelect(wrapper);

    expect(select.exists()).toBe(true);
    await select.setValue('fuel');

    expect(wrapper.emitted('save')).toEqual([['fuel']]);
    expect(wrapper.find('select').exists()).toBe(false);
  });

  it('select type does not emit when re-picking the current value', async () => {
    const wrapper = mountCell({
      type: 'select', value: 'software', options: CATEGORY_OPTIONS,
    });
    const select = await openSelect(wrapper);

    await select.setValue('software');

    expect(wrapper.emitted('save')).toBeUndefined();
  });

  it('select type cancels on Esc without saving', async () => {
    const wrapper = mountCell({
      type: 'select', value: 'software', options: CATEGORY_OPTIONS,
    });
    const select = await openSelect(wrapper);

    await select.trigger('keydown.esc');

    expect(wrapper.emitted('save')).toBeUndefined();
    expect(wrapper.find('[data-testid="inline-cell-display"]').exists()).toBe(true);
  });

  // ── Negative money (refunds / chargebacks) ──

  it('money type keeps the sign when allowNegative is set', async () => {
    const wrapper = mountCell({ type: 'money', value: '-40000', allowNegative: true });
    const input = await openEditor(wrapper);

    expect(input.element.value).toBe('-40.000');

    await input.setValue('-55000');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[-55000]]);
  });

  it('money type still strips the sign when allowNegative is off', async () => {
    const wrapper = mountCell({ type: 'money', value: '1000' });
    const input = await openEditor(wrapper);

    await input.setValue('-2000');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[2000]]);
  });

  // ── Installments ──

  async function openInstallments(value) {
    const wrapper = mountCell({ type: 'installments', value });
    await wrapper.find('[data-testid="inline-cell-display"]').trigger('click');
    return {
      wrapper,
      number: wrapper.find('[data-testid="inline-cell-installment-number"]'),
      total: wrapper.find('[data-testid="inline-cell-installment-total"]'),
    };
  }

  it('installments type seeds both inputs from the "n/total" label', async () => {
    const { number, total } = await openInstallments('3/12');

    expect(number.element.value).toBe('3');
    expect(total.element.value).toBe('12');
  });

  it('installments type emits the structured pair on Enter', async () => {
    const { wrapper, number, total } = await openInstallments('3/12');

    await number.setValue('4');
    await total.setValue('12');
    await number.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[{ number: 4, total: 12 }]]);
  });

  it('installments type emits null when both fields are cleared', async () => {
    const { wrapper, number, total } = await openInstallments('3/12');

    await number.setValue('');
    await total.setValue('');
    await number.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[null]]);
  });

  it('installments type emits nothing when the pair is unchanged', async () => {
    const { wrapper, number } = await openInstallments('3/12');

    await number.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toBeUndefined();
  });

  // ── Merchant combobox ──

  const MERCHANT_OPTIONS = [
    { value: 'Netflix', category: 'software', categoryLabel: 'Software y suscripciones' },
    { value: 'Terpel', category: 'fuel', categoryLabel: 'Gasolina' },
  ];

  it('merchant type saves free text that is not in the catalog', async () => {
    const wrapper = mountCell({
      type: 'merchant', value: 'Netflix', options: MERCHANT_OPTIONS,
    });
    const input = await openEditor(wrapper);

    await input.setValue('Comercio Nuevo');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([['Comercio Nuevo']]);
  });

  it('merchant type carries the default category of a picked option', async () => {
    const wrapper = mountCell({
      type: 'merchant', value: '', options: MERCHANT_OPTIONS,
    });
    await wrapper.find('[data-testid="inline-cell-display"]').trigger('click');
    // Focusing the combobox is what reveals the catalog.
    await wrapper.find('input').trigger('focus');

    await wrapper.find('[data-testid="merchant-input-option-1"]').trigger('mousedown');

    expect(wrapper.emitted('save')).toEqual([['Terpel', { category: 'fuel' }]]);
  });

  it('number type emits a number, not the typed string', async () => {
    const wrapper = mountCell({ type: 'number', value: 20 });
    const input = await openEditor(wrapper);

    await input.setValue('80');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[80]]);
  });

  it('number type clamps to its bounds', async () => {
    const wrapper = mountCell({ type: 'number', value: 10, min: 0, max: 100 });
    const input = await openEditor(wrapper);

    await input.setValue('250');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toEqual([[100]]);
  });

  it('number type keeps the previous value when the cell is blanked', async () => {
    // Emitting 0 here would silently zero out an hours or discount cell.
    const wrapper = mountCell({ type: 'number', value: 20 });
    const input = await openEditor(wrapper);

    await input.setValue('');
    await input.trigger('keydown.enter');

    expect(wrapper.emitted('save')).toBeUndefined();
  });
});
