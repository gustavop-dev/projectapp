/**
 * Tests for StatementDetail inline row editing.
 *
 * Covers: dblclick edit emits inline-save, category select shows the label
 * but emits the value, processed statements render no editors, negative
 * amounts stay modal-only, and an in-flight save disables its cell.
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
  it('dblclick on the description edits it and emits inline-save', async () => {
    const wrapper = mountDetail();
    const td = cell(wrapper, 'raw_description');

    await td.find('[data-testid="inline-cell-display"]').trigger('dblclick');
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

    await td.find('[data-testid="inline-cell-display"]').trigger('dblclick');
    await td.find('select').setValue('fuel');

    const [, field, value] = wrapper.emitted('inline-save')[0];
    expect(field).toBe('category');
    expect(value).toBe('fuel');
  });

  it('renders no inline editors on a processed statement', () => {
    const wrapper = mountDetail({
      statement: makeStatement({ status: 'processed', status_label: 'Procesado' }),
    });

    expect(wrapper.findAll('[data-testid="inline-cell-display"]')).toHaveLength(0);
    // The plain values still render.
    expect(cell(wrapper, 'raw_description').text()).toContain('PAYU*NETFLIX');
  });

  it('offers no inline editor on a negative amount (refunds are modal-only)', () => {
    const wrapper = mountDetail({
      statement: makeStatement({
        transactions: [makeTx({ id: 6, amount: '-20000.00' })],
      }),
    });

    const amountCell = cell(wrapper, 'amount', 6);
    expect(amountCell.find('[data-testid="inline-cell-display"]').exists()).toBe(false);
    // Other fields of the same row stay editable.
    expect(
      cell(wrapper, 'merchant_name', 6).find('[data-testid="inline-cell-display"]').exists(),
    ).toBe(true);
  });

  it('does not open the editor on the cell whose save is in flight', async () => {
    const wrapper = mountDetail({ inlineSavingKey: '5:raw_description' });
    const td = cell(wrapper, 'raw_description');

    await td.find('[data-testid="inline-cell-display"]').trigger('dblclick');

    expect(td.find('input').exists()).toBe(false);
  });
});
