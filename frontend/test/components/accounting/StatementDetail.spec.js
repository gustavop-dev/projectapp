/**
 * Tests for StatementDetail inline row editing.
 *
 * Covers: a click edit emits inline-save, category select shows the label but
 * emits the value, processed statements stay editable (the page asks to reopen
 * on save), negative amounts edit inline, the merchant cell forwards the picked
 * category, and an in-flight save disables its cell.
 */
import { mount } from '@vue/test-utils';
import StatementDetail from '../../../components/accounting/StatementDetail.vue';

const CATEGORY_OPTIONS = [
  { value: 'software', label: 'Software y suscripciones' },
  { value: 'fuel', label: 'Gasolina' },
];

function makeTx(overrides = {}) {
  return {
    id: 5,
    transaction_date: '2026-06-15',
    raw_description: 'PAYU*NETFLIX',
    merchant_name: 'Netflix',
    category: 'software',
    category_label: 'Software y suscripciones',
    installment_label: '1/1',
    amount: '44900.00',
    original_amount: null,
    original_currency: null,
    ...overrides,
  };
}

function makeStatement(overrides = {}) {
  return {
    card_name: 'T.C 0064',
    period_label: 'junio 2026',
    status: 'draft',
    status_label: 'Borrador',
    created_at: '2026-07-01T10:00:00Z',
    purchases_total: '44900.00',
    payments_total: '0.00',
    interest_and_fees: '0.00',
    closing_balance: '44900.00',
    minimum_payment: '0.00',
    due_date: null,
    pdf_file_url: null,
    category_totals: [],
    transactions: [makeTx()],
    ...overrides,
  };
}

function mountDetail(props = {}) {
  return mount(StatementDetail, {
    props: {
      statement: makeStatement(),
      categoryOptions: CATEGORY_OPTIONS,
      ...props,
    },
  });
}

function cell(wrapper, field, txId = 5) {
  return wrapper.find(`[data-testid="tx-cell-${field}-${txId}"]`);
}

describe('StatementDetail inline editing', () => {
  it('a click on the description edits it and emits inline-save', async () => {
    const wrapper = mountDetail();
    const td = cell(wrapper, 'raw_description');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    const input = td.find('input');
    await input.setValue('NETFLIX.COM');
    await input.trigger('keydown.enter');

    const emitted = wrapper.emitted('inline-save');
    expect(emitted).toHaveLength(1);
    const [tx, field, value] = emitted[0];
    expect(tx.id).toBe(5);
    expect(field).toBe('raw_description');
    expect(value).toBe('NETFLIX.COM');
  });

  it('category cell shows the label but emits the option value', async () => {
    const wrapper = mountDetail();
    const td = cell(wrapper, 'category');

    expect(td.text()).toContain('Software y suscripciones');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    await td.find('select').setValue('fuel');

    const [, field, value] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('category');
    expect(value).toBe('fuel');
  });

  it('keeps the cells editable on a processed statement', async () => {
    const wrapper = mountDetail({
      statement: makeStatement({ status: 'processed', status_label: 'Procesado' }),
    });

    // Editing is allowed; the page is the one that asks to reopen before saving.
    expect(wrapper.findAll('[data-testid="inline-cell-display"]')).toHaveLength(6);
    expect(wrapper.find('[data-testid="statement-inline-hint"]').text())
      .toContain('finalizado');

    const td = cell(wrapper, 'raw_description');
    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    expect(td.find('input').exists()).toBe(true);
  });

  it('edits a negative amount inline keeping the sign', async () => {
    const wrapper = mountDetail({
      statement: makeStatement({
        transactions: [makeTx({ id: 6, amount: '-20000.00' })],
      }),
    });
    const td = cell(wrapper, 'amount', 6);

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    const input = td.find('input');
    expect(input.element.value).toBe('-20.000');

    await input.setValue('-25000');
    await input.trigger('keydown.enter');

    const [, field, value] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('amount');
    expect(value).toBe(-25000);
  });

  it('forwards the default category of a merchant picked from the catalog', async () => {
    const wrapper = mountDetail({
      // An unidentified row is where the catalog actually gets used.
      statement: makeStatement({ transactions: [makeTx({ merchant_name: '' })] }),
      merchantOptions: [
        { value: 'Terpel', category: 'fuel', categoryLabel: 'Gasolina' },
      ],
    });
    const td = cell(wrapper, 'merchant_name');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    await td.find('input').trigger('focus');
    await td.find('[data-testid="merchant-input-option-0"]').trigger('mousedown');

    const [, field, value, meta] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('merchant_name');
    expect(value).toBe('Terpel');
    expect(meta).toEqual({ category: 'fuel' });
  });

  it('emits the installments pair as a structured object', async () => {
    const wrapper = mountDetail();
    const td = cell(wrapper, 'installment_label');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');
    await td.find('[data-testid="inline-cell-installment-number"]').setValue('3');
    await td.find('[data-testid="inline-cell-installment-total"]').setValue('12');
    await td.find('[data-testid="inline-cell-installment-number"]').trigger('keydown.enter');

    const [, field, value] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('installment_label');
    expect(value).toEqual({ number: 3, total: 12 });
  });

  it('does not open the editor on the cell whose save is in flight', async () => {
    const wrapper = mountDetail({ inlineSavingKey: '5:raw_description' });
    const td = cell(wrapper, 'raw_description');

    await td.find('[data-testid="inline-cell-display"]').trigger('click');

    expect(td.find('input').exists()).toBe(false);
  });
});
