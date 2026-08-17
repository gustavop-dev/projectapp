/**
 * Tests for the bulk abono action of the accounting store: one payment
 * distributed across several expected incomes. The action must post the
 * confirmed distribution untouched, replace the refreshed rows in place and
 * hand the page the exact ids of a stale selection (409) so it can drop
 * them instead of clearing everything.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useAccountingStore } from '../../stores/accounting';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { create_request } = require('../../stores/services/request_http');

function apiError(status, data) {
  return { response: { status, data } };
}

const PAYLOAD = {
  total_amount: 800000,
  period_date: '2026-08-15',
  notes: 'Transferencia Bancolombia',
  allocations: [
    { income_id: 21, amount: 500000 },
    { income_id: 22, amount: 300000 },
  ],
};

describe('accounting store — bulk settle (abono)', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useAccountingStore();
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('posts the abono and replaces the refreshed rows in place', async () => {
    store.incomes = [
      { id: 21, concept: 'Kore - Fase 2', payment_status: 'pending' },
      { id: 9, concept: 'Otro', payment_status: 'pending' },
    ];
    create_request.mockResolvedValue({
      data: {
        updated: 2,
        results: [{ id: 21, concept: 'Kore - Fase 2', payment_status: 'paid' }],
        movement: { id: 7, amount: '800000.00' },
      },
    });

    const result = await store.bulkSettleIncomes(PAYLOAD);

    expect(create_request).toHaveBeenCalledWith(
      'accounting/incomes/bulk-settle/', PAYLOAD,
    );
    expect(result.success).toBe(true);
    expect(result.data.movement.id).toBe(7);
    expect(store.incomes[0].payment_status).toBe('paid');
    expect(store.incomes[1].concept).toBe('Otro');
  });

  it('surfaces the backend message on a business rejection', async () => {
    create_request.mockRejectedValue(apiError(400, {
      error: 'La imputación a "Kore - Fase 2" supera su saldo pendiente.',
    }));

    const result = await store.bulkSettleIncomes(PAYLOAD);

    expect(result.success).toBe(false);
    expect(result.message).toBe(
      'La imputación a "Kore - Fase 2" supera su saldo pendiente.',
    );
    expect(result.missingIds).toEqual([]);
  });

  it('hands back the ids of a stale selection', async () => {
    create_request.mockRejectedValue(apiError(409, {
      error: '1 de los ingresos seleccionados ya no existe.',
      code: 'records_not_found',
      missing_ids: [22],
    }));

    const result = await store.bulkSettleIncomes(PAYLOAD);

    expect(result.success).toBe(false);
    expect(result.code).toBe('records_not_found');
    expect(result.missingIds).toEqual([22]);
  });
});
