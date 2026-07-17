/**
 * Error-path tests for the accounting store: every action catch block
 * returns {success: false} and, where the UI relies on it, sets the
 * store error code. Also covers the pocket running-balance tiebreak.
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

describe('useAccountingStore — error paths', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAccountingStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
    const rejection = apiError(500, { detail: 'boom' })
    get_request.mockRejectedValue(rejection)
    create_request.mockRejectedValue(rejection)
    patch_request.mockRejectedValue(rejection)
    delete_request.mockRejectedValue(rejection)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('pocket running balance', () => {
    it('breaks same-day ties by created_at', () => {
      store.pocketMovements = [
        {
          id: 2,
          movement_date: '2026-03-10',
          created_at: '2026-03-10T12:00:00Z',
          direction: 'out',
          amount: '30000.00',
        },
        {
          id: 1,
          movement_date: '2026-03-10',
          created_at: '2026-03-10T08:00:00Z',
          direction: 'in',
          amount: '100000.00',
        },
      ]

      const rows = store.pocketWithRunningBalance

      expect(rows.map((row) => row.id)).toEqual([1, 2])
    })
  })

  describe('generic record actions', () => {
    it('updateRecord reports update_failed', async () => {
      const result = await store.updateRecord('incomes', 1, {})

      expect(result.success).toBe(false)
      expect(store.error).toBe('update_failed')
    })

    it('deleteRecord reports delete_failed', async () => {
      const result = await store.deleteRecord('incomes', 1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('delete_failed')
    })
  })

  describe('actions that flag the store error code', () => {
    const CASES = [
      ['fetchStatementStatus', () => store.fetchStatementStatus(2026), 'fetch_failed'],
      ['fetchStatementDetail', () => store.fetchStatementDetail(5), 'fetch_failed'],
      ['reopenStatement', () => store.reopenStatement(5), 'update_failed'],
      [
        'uploadStatementPdf',
        () => store.uploadStatementPdf(5, new File(['%PDF'], 'x.pdf')),
        'update_failed',
      ],
      ['deleteStatementPdf', () => store.deleteStatementPdf(5), 'delete_failed'],
      [
        'updateStatementTransaction',
        () => store.updateStatementTransaction(5, 2, {}),
        'update_failed',
      ],
      ['fetchChangelog', () => store.fetchChangelog(), 'changelog_failed'],
      ['fetchSettings', () => store.fetchSettings(), 'settings_failed'],
      ['fetchCollectionAccounts', () => store.fetchCollectionAccounts(), 'fetch_failed'],
    ]

    test.each(CASES)('%s fails with its error code', async (_name, run, code) => {
      const result = await run()

      expect(result.success).toBe(false)
      expect(store.error).toBe(code)
    })
  })

  describe('actions that only report the failure', () => {
    const CASES = [
      ['sendHostingCollectionAccount', () => store.sendHostingCollectionAccount(7)],
      ['fetchHostingCycles', () => store.fetchHostingCycles(1)],
      ['createHostingCycle', () => store.createHostingCycle(1, { amount: '1.00' })],
      ['deleteHostingCycle', () => store.deleteHostingCycle(1, 50)],
      ['resendCollectionAccount', () => store.resendCollectionAccount(3)],
      ['cancelCollectionAccount', () => store.cancelCollectionAccount(3)],
    ]

    test.each(CASES)('%s resolves with success false', async (_name, run) => {
      const result = await run()

      expect(result.success).toBe(false)
      expect(store.isUpdating).toBe(false)
    })
  })
})
