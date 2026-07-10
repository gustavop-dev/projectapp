/**
 * Tests for the credit-card statement slice of the accounting store.
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

const STATUS_PAYLOAD = {
  year: 2026,
  cards: ['Visa Bancolombia'],
  months: [{ period: '2026-01', label: 'Enero 2026', statements: [], has_processed: false, has_draft: false }],
}

const DETAIL = {
  id: 7,
  card_name: 'Visa Bancolombia',
  status: 'draft',
  transactions: [
    { id: 1, merchant_name: 'Netflix', amount: '44900.00' },
    { id: 2, merchant_name: '', amount: '99900.00' },
  ],
}

describe('useAccountingStore — statements', () => {
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

  it('exposes the statement entities through the generic CRUD map', async () => {
    get_request.mockResolvedValue({ data: { results: [{ id: 7 }], meta: {} } })
    const result = await store.fetchRecords('statements')
    expect(get_request).toHaveBeenCalledWith('accounting/statements/')
    expect(result.success).toBe(true)
    expect(store.statements).toEqual([{ id: 7 }])

    get_request.mockResolvedValue({ data: { results: [{ id: 1 }], meta: {} } })
    await store.fetchRecords('merchantAliases')
    expect(get_request).toHaveBeenCalledWith('accounting/merchant-aliases/')
    expect(store.merchantAliases).toEqual([{ id: 1 }])
  })

  it('fetchStatementStatus stores the grid with year and card params', async () => {
    get_request.mockResolvedValue({ data: STATUS_PAYLOAD })
    const result = await store.fetchStatementStatus(2026, 'Visa Bancolombia')
    expect(get_request).toHaveBeenCalledWith(
      'accounting/statements/status/?year=2026&card_name=Visa+Bancolombia',
    )
    expect(result.success).toBe(true)
    expect(store.statementStatus).toEqual(STATUS_PAYLOAD)
  })

  it('fetchStatementDetail stores the detail payload', async () => {
    get_request.mockResolvedValue({ data: DETAIL })
    const result = await store.fetchStatementDetail(7)
    expect(get_request).toHaveBeenCalledWith('accounting/statements/7/')
    expect(result.success).toBe(true)
    expect(store.statementDetail).toEqual(DETAIL)
  })

  it('finalizeStatement posts force flag and updates the detail', async () => {
    create_request.mockResolvedValue({ data: { ...DETAIL, status: 'processed' } })
    const result = await store.finalizeStatement(7, true)
    expect(create_request).toHaveBeenCalledWith(
      'accounting/statements/7/finalize/', { force: true },
    )
    expect(result.success).toBe(true)
    expect(store.statementDetail.status).toBe('processed')
  })

  it('finalizeStatement surfaces the backend mismatch message', async () => {
    create_request.mockRejectedValue(apiError(400, {
      error: 'La suma de las transacciones (60000) no cuadra; diferencia: -40000.',
    }))
    const result = await store.finalizeStatement(7)
    expect(result.success).toBe(false)
    expect(result.message).toContain('diferencia')
  })

  it('reopenStatement posts and updates the detail', async () => {
    create_request.mockResolvedValue({ data: { ...DETAIL, status: 'draft' } })
    const result = await store.reopenStatement(7)
    expect(create_request).toHaveBeenCalledWith(
      'accounting/statements/7/reopen/', {},
    )
    expect(result.success).toBe(true)
  })

  it('updateStatementTransaction replaces the row in the loaded detail', async () => {
    store.statementDetail = { ...DETAIL }
    patch_request.mockResolvedValue({
      data: { id: 2, merchant_name: 'Primax', amount: '99900.00' },
    })
    const result = await store.updateStatementTransaction(7, 2, {
      merchant_name: 'Primax',
    })
    expect(patch_request).toHaveBeenCalledWith(
      'accounting/statements/7/transactions/2/update/',
      { merchant_name: 'Primax' },
    )
    expect(result.success).toBe(true)
    expect(store.statementDetail.transactions[1].merchant_name).toBe('Primax')
  })

  it('deleteStatementTransaction drops the row from the loaded detail', async () => {
    store.statementDetail = { ...DETAIL }
    delete_request.mockResolvedValue({})
    const result = await store.deleteStatementTransaction(7, 2)
    expect(delete_request).toHaveBeenCalledWith(
      'accounting/statements/7/transactions/2/delete/',
    )
    expect(result.success).toBe(true)
    expect(store.statementDetail.transactions.map((t) => t.id)).toEqual([1])
  })
})
