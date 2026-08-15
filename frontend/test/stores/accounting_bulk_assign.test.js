/**
 * Tests for the two bulk client-assignment actions of the accounting store.
 *
 * They had no store coverage at all, and they are the pair that now has to
 * carry `missing_ids` back to the page: when the server refuses a batch
 * because part of it was deleted meanwhile, the page needs the exact ids to
 * drop, not just a message.
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

const NOT_FOUND = {
  error: '1 de los ingresos seleccionados ya no existe.',
  code: 'records_not_found',
  hint: 'La lista se actualizó. Revisa la selección y vuelve a intentarlo.',
  missing_ids: [2],
};

describe('accounting store — bulk client assignment', () => {
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

  describe('bulkAssignIncomeClient', () => {
    it('posts the ids and replaces the affected rows in place', async () => {
      store.incomes = [
        { id: 1, concept: 'Kore - Inicio', client: null },
        { id: 9, concept: 'Otro', client: null },
      ];
      create_request.mockResolvedValue({
        data: { updated: 1, results: [{ id: 1, concept: 'Kore - Inicio', client: 5 }] },
      });

      const result = await store.bulkAssignIncomeClient([1], 5);

      expect(create_request).toHaveBeenCalledWith(
        'accounting/incomes/bulk-assign-client/',
        { income_ids: [1], client: 5 },
      );
      expect(result.success).toBe(true);
      expect(store.incomes[0].client).toBe(5);
      // Untouched rows keep their object, not a rebuilt copy.
      expect(store.incomes[1].concept).toBe('Otro');
    });

    it('hands the page the ids the server says no longer exist', async () => {
      create_request.mockRejectedValue(apiError(409, NOT_FOUND));

      const result = await store.bulkAssignIncomeClient([1, 2], 5);

      expect(result.success).toBe(false);
      expect(result.code).toBe('records_not_found');
      expect(result.missingIds).toEqual([2]);
      expect(result.message).toBe('1 de los ingresos seleccionados ya no existe.');
    });

    it('reports no missing ids for an ordinary failure', async () => {
      create_request.mockRejectedValue(apiError(400, { error: 'Cliente inválido.' }));

      const result = await store.bulkAssignIncomeClient([1], 5);

      expect(result.success).toBe(false);
      expect(result.missingIds).toEqual([]);
    });
  });

  describe('bulkAssignHostingClient', () => {
    it('posts hosting_ids and replaces the affected rows in place', async () => {
      store.hostings = [{ id: 3, domain_url: 'kore.com.co', client: null }];
      create_request.mockResolvedValue({
        data: { updated: 1, results: [{ id: 3, domain_url: 'kore.com.co', client: 5 }] },
      });

      const result = await store.bulkAssignHostingClient([3], 5);

      expect(create_request).toHaveBeenCalledWith(
        'accounting/hostings/bulk-assign-client/',
        { hosting_ids: [3], client: 5 },
      );
      expect(result.success).toBe(true);
      expect(store.hostings[0].client).toBe(5);
    });

    it('carries the missing ids back too, so the two views cannot drift', async () => {
      create_request.mockRejectedValue(
        apiError(409, { ...NOT_FOUND, missing_ids: [7, 8] }),
      );

      const result = await store.bulkAssignHostingClient([7, 8], null);

      expect(result.missingIds).toEqual([7, 8]);
    });
  });

  describe('bulkAssignIncomeProject', () => {
    it('posts the ids and rebuilds rows from results, cascaded children included', async () => {
      store.incomes = [
        { id: 1, concept: 'Esperado', project: null },
        { id: 2, concept: 'Abono', project: null },
        { id: 9, concept: 'Ajeno', project: null },
      ];
      create_request.mockResolvedValue({
        data: {
          updated: 1,
          results: [
            { id: 1, concept: 'Esperado', project: 40 },
            { id: 2, concept: 'Abono', project: 40 },
          ],
        },
      });

      const result = await store.bulkAssignIncomeProject([1], 40);

      expect(create_request).toHaveBeenCalledWith(
        'accounting/incomes/bulk-assign-project/',
        { income_ids: [1], project: 40 },
      );
      expect(result.success).toBe(true);
      expect(store.incomes.map((row) => row.project)).toEqual([40, 40, null]);
    });

    it('carries the mismatched ids back so the page can drop exactly those', async () => {
      create_request.mockRejectedValue(apiError(409, {
        error: '1 de los ingresos seleccionados no pertenece al cliente del proyecto.',
        code: 'client_mismatch',
        mismatched_ids: [9],
      }));

      const result = await store.bulkAssignIncomeProject([1, 9], 40);

      expect(result.success).toBe(false);
      expect(result.code).toBe('client_mismatch');
      expect(result.missingIds).toEqual([9]);
    });
  });

  describe('bulkAssignHostingProject', () => {
    it('posts hosting_ids and supports clearing with null', async () => {
      store.hostings = [{ id: 3, domain_url: 'kore.com.co', project: 40 }];
      create_request.mockResolvedValue({
        data: {
          updated: 1,
          results: [{ id: 3, domain_url: 'kore.com.co', project: null }],
        },
      });

      const result = await store.bulkAssignHostingProject([3], null);

      expect(create_request).toHaveBeenCalledWith(
        'accounting/hostings/bulk-assign-project/',
        { hosting_ids: [3], project: null },
      );
      expect(result.success).toBe(true);
      expect(store.hostings[0].project).toBeNull();
    });
  });
});
