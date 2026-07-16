/**
 * Tests for the accounting store operational actions: statement transaction
 * edits, summary/changelog/settings, collection accounts and hosting cycles.
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

describe('useAccountingStore — operations', () => {
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

  describe('statement transactions', () => {
    it('createStatementTransactions posts the lines and refreshes the open detail', async () => {
      store.statementDetail = { id: 5, transactions: [] }
      create_request.mockResolvedValue({ data: { created: 2 } })
      get_request.mockResolvedValue({ data: { id: 5, transactions: [{ id: 1 }] } })

      const result = await store.createStatementTransactions(5, [{ raw: 'x' }])

      expect(create_request).toHaveBeenCalledWith(
        'accounting/statements/5/transactions/batch/',
        { transactions: [{ raw: 'x' }] },
      )
      expect(get_request).toHaveBeenCalled()
      expect(result.success).toBe(true)
    })

    it('createStatementTransactions surfaces create_failed on error', async () => {
      create_request.mockRejectedValue(apiError(400, { detail: 'bad' }))

      const result = await store.createStatementTransactions(5, [])

      expect(result.success).toBe(false)
      expect(store.error).toBe('create_failed')
    })

    it('uploadStatementPdf sends a FormData payload and stores the detail', async () => {
      const detail = { id: 5, pdf_url: '/media/x.pdf' }
      create_request.mockResolvedValue({ data: detail })

      const file = new File(['%PDF'], 'extracto.pdf', { type: 'application/pdf' })
      const result = await store.uploadStatementPdf(5, file)

      const [path, body] = create_request.mock.calls[0]
      expect(path).toBe('accounting/statements/5/pdf/upload/')
      expect(body).toBeInstanceOf(FormData)
      expect(store.statementDetail).toEqual(detail)
      expect(result.success).toBe(true)
    })

    it('deleteStatementPdf replaces the detail with the response', async () => {
      const detail = { id: 5, pdf_url: null }
      delete_request.mockResolvedValue({ data: detail })

      const result = await store.deleteStatementPdf(5)

      expect(delete_request).toHaveBeenCalledWith('accounting/statements/5/pdf/delete/')
      expect(store.statementDetail).toEqual(detail)
      expect(result.success).toBe(true)
    })

    it('updateStatementTransaction swaps the edited line in the open detail', async () => {
      store.statementDetail = {
        id: 5,
        transactions: [{ id: 1, merchant: 'A' }, { id: 2, merchant: 'B' }],
      }
      patch_request.mockResolvedValue({ data: { id: 2, merchant: 'Éxito' } })

      await store.updateStatementTransaction(5, 2, { merchant: 'Éxito' })

      expect(store.statementDetail.transactions[1]).toEqual({ id: 2, merchant: 'Éxito' })
    })

    it('updateStatementTransaction leaves an unrelated open detail untouched', async () => {
      store.statementDetail = { id: 9, transactions: [{ id: 2, merchant: 'B' }] }
      patch_request.mockResolvedValue({ data: { id: 2, merchant: 'Éxito' } })

      await store.updateStatementTransaction(5, 2, { merchant: 'Éxito' })

      expect(store.statementDetail.transactions[0].merchant).toBe('B')
    })

    it('deleteStatementTransaction filters the line out of the open detail', async () => {
      store.statementDetail = {
        id: 5,
        transactions: [{ id: 1 }, { id: 2 }],
      }
      delete_request.mockResolvedValue({})

      await store.deleteStatementTransaction(5, 1)

      expect(store.statementDetail.transactions).toEqual([{ id: 2 }])
    })

    it('deleteStatementTransaction surfaces delete_failed on error', async () => {
      delete_request.mockRejectedValue(apiError(500, {}))

      const result = await store.deleteStatementTransaction(5, 1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('delete_failed')
    })
  })

  describe('summary, changelog and settings', () => {
    it('fetchSummary stores the payload and remembers the year', async () => {
      get_request.mockResolvedValue({ data: { incomes: {} } })

      const result = await store.fetchSummary(2025)

      expect(get_request).toHaveBeenCalledWith('accounting/dashboard/?year=2025')
      expect(store.summary).toEqual({ incomes: {} })
      expect(store.selectedYear).toBe(2025)
      expect(result.success).toBe(true)
    })

    it('fetchSummary surfaces summary_failed on error', async () => {
      get_request.mockRejectedValue(apiError(500, {}))

      const result = await store.fetchSummary(2025)

      expect(result.success).toBe(false)
      expect(store.error).toBe('summary_failed')
    })

    it('fetchChangelog maps num_pages into the camelCase shape', async () => {
      get_request.mockResolvedValue({
        data: { results: [{ id: 1 }], count: 21, page: 2, num_pages: 2 },
      })

      await store.fetchChangelog({ page: 2 })

      expect(get_request.mock.calls[0][0]).toContain('page=2')
      expect(store.changelog).toEqual({
        results: [{ id: 1 }],
        count: 21,
        page: 2,
        numPages: 2,
      })
    })

    it('fetchSettings stores the singleton', async () => {
      get_request.mockResolvedValue({ data: { notifications_enabled: true } })

      await store.fetchSettings()

      expect(get_request).toHaveBeenCalledWith('accounting/settings/')
      expect(store.settings).toEqual({ notifications_enabled: true })
    })

    it('updateSettings patches and stores the response', async () => {
      patch_request.mockResolvedValue({ data: { notifications_enabled: false } })

      const result = await store.updateSettings({ notifications_enabled: false })

      expect(patch_request).toHaveBeenCalledWith(
        'accounting/settings/update/',
        { notifications_enabled: false },
      )
      expect(store.settings).toEqual({ notifications_enabled: false })
      expect(result.success).toBe(true)
    })

    it('updateSettings surfaces settings_update_failed on error', async () => {
      patch_request.mockRejectedValue(apiError(400, {}))

      const result = await store.updateSettings({})

      expect(result.success).toBe(false)
      expect(store.error).toBe('settings_update_failed')
    })
  })

  describe('collection accounts', () => {
    it('fetchCollectionAccounts stores results and meta', async () => {
      get_request.mockResolvedValue({
        data: { results: [{ id: 3 }], meta: { issued_count: 1 } },
      })

      await store.fetchCollectionAccounts({ status: 'issued' })

      expect(get_request.mock.calls[0][0]).toContain('status=issued')
      expect(store.collectionAccounts).toEqual([{ id: 3 }])
      expect(store.collectionAccountsMeta).toEqual({ issued_count: 1 })
    })

    it('sendHostingCollectionAccount posts to the hosting endpoint', async () => {
      create_request.mockResolvedValue({
        data: { document: { public_number: 'PA-2026-0007' }, email_sent: true },
      })

      const result = await store.sendHostingCollectionAccount(7)

      expect(create_request).toHaveBeenCalledWith(
        'accounting/hostings/7/send-collection-account/', {},
      )
      expect(result.data.email_sent).toBe(true)
    })

    it('markCollectionAccountPaid replaces the account in place', async () => {
      store.collectionAccounts = [
        { id: 3, status: 'issued' },
        { id: 4, status: 'issued' },
      ]
      create_request.mockResolvedValue({ data: { id: 3, status: 'paid' } })

      await store.markCollectionAccountPaid(3)

      expect(create_request).toHaveBeenCalledWith(
        'accounting/collection-accounts/3/mark-paid/', {},
      )
      expect(store.collectionAccounts[0]).toEqual({ id: 3, status: 'paid' })
      expect(store.collectionAccounts[1]).toEqual({ id: 4, status: 'issued' })
    })
  })

  describe('hosting cycles', () => {
    it('fetchHostingCycles returns the results array', async () => {
      get_request.mockResolvedValue({ data: { results: [{ id: 10 }] } })

      const result = await store.fetchHostingCycles(1)

      expect(get_request).toHaveBeenCalledWith('accounting/hostings/1/cycles/')
      expect(result).toEqual({ success: true, data: [{ id: 10 }] })
    })

    it('createHostingCycle swaps the refreshed hosting row', async () => {
      store.hostings = [{ id: 1, cycles_count: 0 }, { id: 2, cycles_count: 3 }]
      create_request.mockResolvedValue({
        data: { cycle: { id: 50 }, hosting: { id: 1, cycles_count: 1 } },
      })

      await store.createHostingCycle(1, { amount: '90000.00' })

      expect(store.hostings[0]).toEqual({ id: 1, cycles_count: 1 })
      expect(store.hostings[1]).toEqual({ id: 2, cycles_count: 3 })
    })

    it('deleteHostingCycle calls the delete endpoint and reports success', async () => {
      delete_request.mockResolvedValue({})

      const result = await store.deleteHostingCycle(1, 50)

      expect(delete_request).toHaveBeenCalledWith(
        'accounting/hostings/1/cycles/50/delete/',
      )
      expect(result).toEqual({ success: true })
    })
  })
})
