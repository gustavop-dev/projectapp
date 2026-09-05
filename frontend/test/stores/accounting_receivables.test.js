import { createPinia, setActivePinia } from 'pinia';
import { useAccountingStore } from '../../stores/accounting';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request, patch_request } = require('../../stores/services/request_http');

const greenRow = (overrides = {}) => ({
  id: 3,
  concept: 'Proyecto Acme',
  kind: 'expected',
  ledger: 'company',
  payment_status: 'partial',
  is_receivable_candidate: true,
  collection_confidence: 'high',
  total_amount: '1200.00',
  paid_amount: '200.00',
  pending_amount: '1000.00',
  ...overrides,
});

describe('accounting receivables store', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useAccountingStore();
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => jest.restoreAllMocks());

  it('loads the global receivables endpoint', async () => {
    const summary = { high_total: '1200.00', high_count: 1 };
    get_request.mockResolvedValue({ data: { results: [greenRow()], summary } });

    const result = await store.fetchReceivables();

    expect(get_request).toHaveBeenCalledWith('accounting/receivables/');
    expect(result.success).toBe(true);
    expect(store.receivablesSummary).toEqual(summary);
  });

  it('recomputes the green original total after an update', async () => {
    store.receivables = [greenRow()];
    store.receivablesSummary = { high_total: 1200, high_count: 1 };
    patch_request.mockResolvedValue({
      data: greenRow({ collection_confidence: 'low' }),
    });

    await store.updateReceivableState(3, { collection_confidence: 'low' });

    expect(store.receivablesSummary.high_total).toBe(0);
    expect(store.receivablesSummary.by_confidence.low.total_amount).toBe(1200);
  });

  it('hydrates the global summary after a direct table edit', async () => {
    store.incomes = [greenRow({ is_receivable_candidate: false, collection_confidence: '' })];
    patch_request.mockResolvedValue({
      data: greenRow({ is_receivable_candidate: false }),
    });
    get_request.mockResolvedValue({
      data: {
        results: [greenRow({ is_receivable_candidate: false })],
        summary: { high_total: '0.00', high_count: 0 },
      },
    });

    await store.updateReceivableState(3, { collection_confidence: 'high' });

    expect(get_request).toHaveBeenCalledWith('accounting/receivables/');
    expect(store.incomes[0].collection_confidence).toBe('high');
    expect(store.incomes[0].is_receivable_candidate).toBe(false);
    expect(store.receivablesSummary.high_total).toBe('0.00');
  });

  it('releases the row lock after a failed update', async () => {
    store.receivablesSummary = { high_total: 0, high_count: 0 };
    patch_request.mockRejectedValue({ response: { data: { error: 'No permitido' } } });

    const result = await store.updateReceivableState(3, { is_receivable_candidate: true });

    expect(result.success).toBe(false);
    expect(store.receivableUpdatingIds).toEqual([]);
  });
});
