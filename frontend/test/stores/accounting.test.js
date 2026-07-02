/**
 * Tests for accounting store (panel, superuser-only module).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useAccountingStore } from '../../stores/accounting'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const {
  get_request,
  create_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http')

function apiError(status, data) {
  return { response: { status, data } }
}

describe('useAccountingStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAccountingStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty records and no summary', () => {
      expect(store.incomes).toEqual([])
      expect(store.pocketMovements).toEqual([])
      expect(store.summary).toBeNull()
      expect(store.settings).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.isUpdating).toBe(false)
    })
  })

  describe('fetchRecords', () => {
    it('fills the entity array and meta on success', async () => {
      get_request.mockResolvedValue({
        data: { results: [{ id: 1, concept: 'Kore' }], meta: { balance: '10.00' } },
      })
      const result = await store.fetchRecords('pocket', { year: 2026 })
      expect(get_request).toHaveBeenCalledWith('accounting/pocket/?year=2026')
      expect(result.success).toBe(true)
      expect(store.pocketMovements).toEqual([{ id: 1, concept: 'Kore' }])
      expect(store.metas.pocket).toEqual({ balance: '10.00' })
    })

    it('omits empty params from the query string', async () => {
      get_request.mockResolvedValue({ data: { results: [], meta: {} } })
      await store.fetchRecords('incomes', { kind: '', q: null })
      expect(get_request).toHaveBeenCalledWith('accounting/incomes/')
    })

    it('normalizes API errors on failure', async () => {
      get_request.mockRejectedValue(
        apiError(400, { error: 'Fecha inválida', code: 'bad_date' }),
      )
      const result = await store.fetchRecords('incomes')
      expect(result.success).toBe(false)
      expect(result.message).toBe('Fecha inválida')
      expect(store.error).toBe('fetch_failed')
    })

    it('throws for unknown entities', async () => {
      await expect(store.fetchRecords('nope')).rejects.toThrow(
        'Unknown accounting entity',
      )
    })
  })

  describe('mutations', () => {
    it('createRecord posts to create/ and prepends the record', async () => {
      store.incomes = [{ id: 1 }]
      create_request.mockResolvedValue({ data: { id: 2, concept: 'Nuevo' } })
      const result = await store.createRecord('incomes', { concept: 'Nuevo' })
      expect(create_request).toHaveBeenCalledWith(
        'accounting/incomes/create/', { concept: 'Nuevo' },
      )
      expect(result.success).toBe(true)
      expect(store.incomes[0]).toEqual({ id: 2, concept: 'Nuevo' })
    })

    it('updateRecord patches update/ and replaces the record', async () => {
      store.expenses = [{ id: 5, concept: 'Viejo' }, { id: 6 }]
      patch_request.mockResolvedValue({ data: { id: 5, concept: 'Nuevo' } })
      const result = await store.updateRecord('expenses', 5, { concept: 'Nuevo' })
      expect(patch_request).toHaveBeenCalledWith(
        'accounting/expenses/5/update/', { concept: 'Nuevo' },
      )
      expect(result.success).toBe(true)
      expect(store.expenses[0].concept).toBe('Nuevo')
      expect(store.expenses[1]).toEqual({ id: 6 })
    })

    it('deleteRecord removes the record from the list', async () => {
      store.hostings = [{ id: 7 }, { id: 8 }]
      delete_request.mockResolvedValue({})
      const result = await store.deleteRecord('hostings', 7)
      expect(delete_request).toHaveBeenCalledWith(
        'accounting/hostings/7/delete/',
      )
      expect(result.success).toBe(true)
      expect(store.hostings).toEqual([{ id: 8 }])
    })

    it('surfaces the backend message on mutation failure', async () => {
      create_request.mockRejectedValue(
        apiError(400, {
          error: 'Este movimiento del bolsillo es gestionado automáticamente.',
          code: 'auto_managed_movement',
        }),
      )
      const result = await store.createRecord('pocket', {})
      expect(result.success).toBe(false)
      expect(result.code).toBe('auto_managed_movement')
    })
  })

  describe('summary, changelog and settings', () => {
    it('fetchSummary queries the dashboard for the given year', async () => {
      get_request.mockResolvedValue({ data: { year: 2026, expected_total: 100 } })
      const result = await store.fetchSummary(2026)
      expect(get_request).toHaveBeenCalledWith('accounting/dashboard/?year=2026')
      expect(result.success).toBe(true)
      expect(store.summary.year).toBe(2026)
      expect(store.selectedYear).toBe(2026)
    })

    it('fetchChangelog maps pagination fields', async () => {
      get_request.mockResolvedValue({
        data: { results: [{ id: 1 }], count: 25, page: 2, num_pages: 3 },
      })
      await store.fetchChangelog({ page: 2, entity_type: 'income' })
      expect(get_request).toHaveBeenCalledWith(
        'accounting/change-logs/?page=2&entity_type=income',
      )
      expect(store.changelog).toEqual({
        results: [{ id: 1 }], count: 25, page: 2, numPages: 3,
      })
    })

    it('fetchSettings and updateSettings hit the settings endpoints', async () => {
      get_request.mockResolvedValue({
        data: { notification_recipients: [], notifications_enabled: true },
      })
      await store.fetchSettings()
      expect(get_request).toHaveBeenCalledWith('accounting/settings/')

      patch_request.mockResolvedValue({
        data: {
          notification_recipients: ['gustavo@test.com'],
          notifications_enabled: true,
        },
      })
      const result = await store.updateSettings({
        notification_recipients: ['gustavo@test.com'],
      })
      expect(patch_request).toHaveBeenCalledWith(
        'accounting/settings/update/',
        { notification_recipients: ['gustavo@test.com'] },
      )
      expect(result.success).toBe(true)
      expect(store.settings.notification_recipients).toEqual([
        'gustavo@test.com',
      ])
    })
  })

  describe('getters', () => {
    it('pocketBalance subtracts outgoing from incoming amounts', () => {
      store.pocketMovements = [
        { direction: 'in', amount: '100.00' },
        { direction: 'out', amount: '40.00' },
      ]
      expect(store.pocketBalance).toBe(60)
    })

    it('pocketWithRunningBalance orders chronologically with running sum', () => {
      store.pocketMovements = [
        {
          id: 2, movement_date: '2026-05-06', created_at: '2026-05-06T10:00:00Z',
          direction: 'out', amount: '40.00',
        },
        {
          id: 1, movement_date: '2026-04-29', created_at: '2026-04-29T10:00:00Z',
          direction: 'in', amount: '100.00',
        },
      ]
      const ledger = store.pocketWithRunningBalance
      expect(ledger.map((m) => m.id)).toEqual([1, 2])
      expect(ledger[0].running_balance).toBe(100)
      expect(ledger[1].running_balance).toBe(60)
    })

    it('recurringTotalsByFrequency sums active payments only', () => {
      store.recurringPayments = [
        {
          is_active: true, frequency: 'monthly', frequency_label: 'Mensual',
          payment_method_label: 'T.C', cop_equivalent: '800000.00',
        },
        {
          is_active: true, frequency: 'monthly', frequency_label: 'Mensual',
          payment_method_label: 'Efectivo', cop_equivalent: '400000.00',
        },
        {
          is_active: false, frequency: 'monthly', frequency_label: 'Mensual',
          payment_method_label: 'T.C', cop_equivalent: '99999.00',
        },
      ]
      expect(store.recurringTotalsByFrequency).toEqual({ Mensual: 1200000 })
      expect(store.recurringTotalsByMethod).toEqual({
        'T.C': 800000, Efectivo: 400000,
      })
    })
  })
})
