import { setActivePinia, createPinia } from 'pinia'
import { usePlatformPaymentsStore } from '../../stores/platform-payments'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  const mockPatch = jest.fn()
  return {
    usePlatformApi: () => ({
      get: mockGet,
      post: mockPost,
      patch: mockPatch,
    }),
    readPlatformSession: jest.fn(() => ({
      accessToken: '',
      refreshToken: '',
      user: null,
      verificationToken: '',
      pendingEmail: '',
    })),
    writePlatformSession: jest.fn(),
    clearPlatformSession: jest.fn(),
    __mockGet: mockGet,
    __mockPost: mockPost,
    __mockPatch: mockPatch,
  }
})

const {
  __mockGet: mockGet,
  __mockPost: mockPost,
  __mockPatch: mockPatch,
} = require('../../composables/usePlatformApi')

describe('usePlatformPaymentsStore', () => {
  let store

  beforeEach(() => {
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2025-06-10T12:00:00.000Z'))
    setActivePinia(createPinia())
    store = usePlatformPaymentsStore()
    jest.clearAllMocks()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('nextRenewalDate is null without subscription', () => {
    expect(store.nextRenewalDate).toBeNull()
  })

  it('nextRenewalDate reads next_billing_date', () => {
    store.currentSubscription = { next_billing_date: '2025-07-01' }
    expect(store.nextRenewalDate).toBe('2025-07-01')
  })

  it('currentPeriodPayment picks overdue over pending', () => {
    store.payments = [
      { id: 1, status: 'pending', due_date: '2025-06-11' },
      { id: 2, status: 'overdue', due_date: '2025-06-01' },
    ]
    expect(store.currentPeriodPayment.id).toBe(2)
  })

  it('currentPeriodPayment picks failed before processing', () => {
    store.payments = [
      { id: 1, status: 'processing' },
      { id: 2, status: 'failed' },
    ]
    expect(store.currentPeriodPayment.id).toBe(2)
  })

  it('currentPeriodPayment ignores pending due far in future', () => {
    store.payments = [{ id: 1, status: 'pending', due_date: '2025-08-01' }]
    expect(store.currentPeriodPayment).toBeNull()
  })

  it('currentPeriodPayment includes pending due within seven days', () => {
    store.payments = [{ id: 1, status: 'pending', due_date: '2025-06-12' }]
    expect(store.currentPeriodPayment).not.toBeNull()
  })

  it('currentPeriodPayment returns null when no urgent payments', () => {
    store.payments = [{ id: 1, status: 'paid' }]
    expect(store.currentPeriodPayment).toBeNull()
  })

  it('pastPayments lists paid and failed sorted newest first', () => {
    store.payments = [
      { id: 1, status: 'paid', billing_period_start: '2025-01-01' },
      { id: 2, status: 'paid', billing_period_start: '2025-03-01' },
      { id: 3, status: 'pending', billing_period_start: '2025-04-01' },
    ]
    const past = store.pastPayments
    expect(past).toHaveLength(2)
    expect(past[0].id).toBe(2)
  })

  it('subscriptionUpToDate is false without subscription', () => {
    expect(store.subscriptionUpToDate).toBe(false)
  })

  it('subscriptionUpToDate is false when status not active', () => {
    store.currentSubscription = { status: 'paused' }
    store.payments = []
    expect(store.subscriptionUpToDate).toBe(false)
  })

  it('subscriptionUpToDate is false when urgent payment exists', () => {
    store.currentSubscription = { status: 'active' }
    store.payments = [{ id: 1, status: 'overdue' }]
    expect(store.subscriptionUpToDate).toBe(false)
  })

  it('subscriptionUpToDate is true when active and no urgent payment', () => {
    store.currentSubscription = { status: 'active' }
    store.payments = []
    expect(store.subscriptionUpToDate).toBe(true)
  })

  it('fetchProposals fills proposals', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1 }] })
    const result = await store.fetchProposals()
    expect(result.success).toBe(true)
    expect(store.proposals).toEqual([{ id: 1 }])
  })

  it('fetchProposals returns message on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'e' } } })
    const result = await store.fetchProposals()
    expect(result.success).toBe(false)
    expect(result.message).toBe('e')
  })

  it('fetchSubscriptions sets list', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchSubscriptions()
    expect(store.isLoading).toBe(false)
    expect(store.subscriptions).toEqual([])
  })

  it('fetchSubscriptions adds include_archived when requested', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchSubscriptions(true)
    expect(mockGet).toHaveBeenCalledWith('subscriptions/?include_archived=1')
  })

  it('fetchProjectSubscription clears state on 404', async () => {
    store.currentSubscription = { id: 1 }
    store.payments = [{ id: 1 }]
    mockGet.mockRejectedValueOnce({ response: { status: 404 } })
    const result = await store.fetchProjectSubscription(9)
    expect(result.success).toBe(true)
    expect(store.currentSubscription).toBeNull()
    expect(store.payments).toEqual([])
  })

  it('fetchProjectSubscription sets subscription and payments', async () => {
    mockGet.mockResolvedValueOnce({
      data: { id: 1, payments: [{ id: 10 }] },
    })
    const result = await store.fetchProjectSubscription(3)
    expect(result.success).toBe(true)
    expect(store.payments).toEqual([{ id: 10 }])
  })

  it('fetchProjectPayments sets payments list', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 2 }] })
    const result = await store.fetchProjectPayments(1)
    expect(result.success).toBe(true)
    expect(store.payments).toEqual([{ id: 2 }])
  })

  it('fetchProjectPayments adds include_archived when requested', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchProjectPayments(7, true)
    expect(mockGet).toHaveBeenCalledWith('projects/7/payments/?include_archived=1')
  })

  it('updateSubscription patches current subscription', async () => {
    mockPatch.mockResolvedValueOnce({ data: { id: 5, status: 'active' } })
    const result = await store.updateSubscription(5, { plan: 'pro' })
    expect(result.success).toBe(true)
    expect(store.currentSubscription).toEqual({ id: 5, status: 'active' })
  })

  it('payWithCard returns data on success', async () => {
    mockPost.mockResolvedValueOnce({ data: { ok: true } })
    const result = await store.payWithCard(1, 2, { token: 't' })
    expect(result.success).toBe(true)
    expect(mockPost).toHaveBeenCalledWith('projects/1/payments/2/card-pay/', { token: 't' })
  })

  it('verifyTransaction posts transaction id', async () => {
    mockPost.mockResolvedValueOnce({ data: { verified: true } })
    const result = await store.verifyTransaction(1, 2, 'tx-99')
    expect(result.success).toBe(true)
    expect(mockPost).toHaveBeenCalledWith('projects/1/payments/2/verify/', {
      transaction_id: 'tx-99',
    })
  })

  it('fetchWidgetData returns widget payload', async () => {
    mockGet.mockResolvedValueOnce({ data: { widget: 1 } })
    const result = await store.fetchWidgetData(3, 4)
    expect(result.success).toBe(true)
    expect(result.data).toEqual({ widget: 1 })
  })

  it('generatePaymentLink updates matching payment row', async () => {
    store.payments = [{ id: 7, status: 'pending', wompi_payment_link_url: null }]
    mockPost.mockResolvedValueOnce({ data: { wompi_payment_link_url: 'https://pay' } })
    const result = await store.generatePaymentLink(1, 7)
    expect(result.success).toBe(true)
    expect(store.payments[0].wompi_payment_link_url).toBe('https://pay')
    expect(store.payments[0].status).toBe('processing')
  })

  it('currentPeriodPayment sorts unknown status after known', () => {
    store.payments = [
      { id: 1, status: 'weird' },
      { id: 2, status: 'pending', due_date: '2025-06-11' },
    ]
    expect(store.currentPeriodPayment.id).toBe(2)
  })

  it('fetchSubscriptions sets error on failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'sub' } } })
    const result = await store.fetchSubscriptions()
    expect(result.success).toBe(false)
    expect(store.error).toBe('sub')
  })

  it('fetchProjectSubscription sets error on non-404 failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { status: 500, data: { detail: 'x' } } })
    const result = await store.fetchProjectSubscription(1)
    expect(result.success).toBe(false)
  })

  it('fetchProjectPayments sets error on failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'p' } } })
    const result = await store.fetchProjectPayments(1)
    expect(result.success).toBe(false)
  })

  it('updateSubscription sets error on failure', async () => {
    mockPatch.mockRejectedValueOnce({ response: { data: { detail: 'u' } } })
    const result = await store.updateSubscription(1, {})
    expect(result.success).toBe(false)
  })

  it('payWithCard sets error on failure', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'card' } } })
    const result = await store.payWithCard(1, 2, {})
    expect(result.success).toBe(false)
  })

  it('verifyTransaction returns message on failure', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'v' } } })
    const result = await store.verifyTransaction(1, 2, 'x')
    expect(result.success).toBe(false)
    expect(result.message).toBe('v')
  })

  it('fetchWidgetData returns message on failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'w' } } })
    const result = await store.fetchWidgetData(1, 2)
    expect(result.success).toBe(false)
  })

  it('generatePaymentLink sets error on failure', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'link' } } })
    const result = await store.generatePaymentLink(1, 2)
    expect(result.success).toBe(false)
  })

  describe('error fallback messages', () => {
    it('fetchProposals uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchProposals()
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error cargando propuestas.')
    })

    it('fetchSubscriptions uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchSubscriptions()
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos cargar las suscripciones.')
    })

    it('fetchProjectSubscription uses fallback when non-404 and detail absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchProjectSubscription(1)
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error cargando suscripción.')
    })

    it('fetchProjectPayments uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchProjectPayments(1)
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error cargando pagos.')
    })

    it('updateSubscription uses fallback when detail is absent', async () => {
      mockPatch.mockRejectedValueOnce(new Error('network'))
      const result = await store.updateSubscription(1, {})
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error actualizando suscripción.')
    })

    it('payWithCard uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))
      const result = await store.payWithCard(1, 2, {})
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error procesando el pago con tarjeta.')
    })

    it('verifyTransaction uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))
      const result = await store.verifyTransaction(1, 2, 'tx')
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error verificando transacción.')
    })

    it('fetchWidgetData uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchWidgetData(1, 2)
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error obteniendo datos de pago.')
    })

    it('generatePaymentLink uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))
      const result = await store.generatePaymentLink(1, 2)
      expect(result.success).toBe(false)
      expect(result.message).toBe('Error generando link de pago.')
    })
  })

  describe('fetchProjectSubscription edge cases', () => {
    it('defaults payments to empty array when absent in response', async () => {
      mockGet.mockResolvedValueOnce({ data: { id: 1 } })
      const result = await store.fetchProjectSubscription(3)
      expect(result.success).toBe(true)
      expect(store.payments).toEqual([])
    })
  })

  describe('generatePaymentLink conditional branches', () => {
    it('does not update list when payment id is not found', async () => {
      store.payments = [{ id: 99, status: 'pending' }]
      mockPost.mockResolvedValueOnce({ data: { wompi_payment_link_url: 'https://pay' } })
      const result = await store.generatePaymentLink(1, 7)
      expect(result.success).toBe(true)
      expect(store.payments[0].wompi_payment_link_url).toBeUndefined()
    })
  })

  describe('currentPeriodPayment edge cases', () => {
    it('excludes pending payment without due_date', () => {
      store.payments = [{ id: 1, status: 'pending', due_date: null }]
      expect(store.currentPeriodPayment).toBeNull()
    })
  })
})
