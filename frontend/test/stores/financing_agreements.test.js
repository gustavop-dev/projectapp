import { createPinia, setActivePinia } from 'pinia'

import { useFinancingAgreementsStore } from '../../stores/financing_agreements'

jest.mock('../../stores/services/request_http', () => ({
  create_request: jest.fn(),
  get_request: jest.fn(),
  patch_request: jest.fn(),
}))

const {
  create_request,
  get_request,
  patch_request,
} = require('../../stores/services/request_http')

const agreement = {
  id: 7,
  number: null,
  client_name: 'Ana Semilla',
  project_name: 'Vástago',
  status: 'draft',
}

describe('useFinancingAgreementsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useFinancingAgreementsStore()
    jest.clearAllMocks()
  })

  it('loads filtered agreements with summary data', async () => {
    get_request.mockResolvedValue({
      data: {
        results: [agreement],
        count: 1,
        stats: { by_status: { draft: 1 } },
      },
    })

    const result = await store.fetchAgreements({ status: 'draft', archived: 'false' })

    expect(get_request).toHaveBeenCalledWith(
      'financing/agreements/?status=draft&archived=false',
    )
    expect(result.success).toBe(true)
    expect(store.agreements).toEqual([agreement])
    expect(store.stats.by_status.draft).toBe(1)
  })

  it('prepends a created financing draft', async () => {
    create_request.mockResolvedValue({ data: agreement })

    const result = await store.createAgreement({ client_id: 3 })

    expect(create_request).toHaveBeenCalledWith(
      'financing/agreements/',
      { client_id: 3 },
    )
    expect(result.success).toBe(true)
    expect(store.currentAgreement).toEqual(agreement)
    expect(store.agreements).toEqual([agreement])
  })

  it('loads the current financing policy', async () => {
    const settings = {
      current: { id: 2, version: 2, maximum_financed_percent: '80.00' },
      history: [{ id: 2, version: 2 }],
      usd_exchange_rate: '4000.00',
    }
    get_request.mockResolvedValue({ data: settings })

    const result = await store.fetchSettings()

    expect(get_request).toHaveBeenCalledWith('financing/settings/')
    expect(result.success).toBe(true)
    expect(store.currentPolicy.version).toBe(2)
    expect(store.policyHistory).toHaveLength(1)
  })

  it('publishes a financing policy revision', async () => {
    const payload = { financing_months: '18' }
    const settings = {
      current: { id: 3, version: 3, financing_months: 18 },
      history: [{ id: 3, version: 3 }],
    }
    create_request.mockResolvedValue({ data: settings })

    const result = await store.publishSettings(payload)

    expect(create_request).toHaveBeenCalledWith('financing/settings/', payload)
    expect(result.success).toBe(true)
    expect(store.currentPolicy.financing_months).toBe(18)
    expect(store.isSaving).toBe(false)
  })

  it('returns field errors from an invalid draft update', async () => {
    const errors = { installment_schedule: ['La suma no coincide.'] }
    patch_request.mockRejectedValue({ response: { data: errors } })

    const result = await store.updateAgreement(7, { installment_schedule: [] })

    expect(result).toEqual({ success: false, errors })
    expect(store.isSaving).toBe(false)
  })

  it('updates the current agreement after a lifecycle action', async () => {
    const ready = { ...agreement, number: 'OFIN-2026-001', status: 'ready' }
    create_request.mockResolvedValue({ data: ready })

    const result = await store.runAction(7, 'mark-ready')

    expect(create_request).toHaveBeenCalledWith(
      'financing/agreements/7/mark-ready/',
      {},
    )
    expect(result.success).toBe(true)
    expect(store.currentAgreement).toEqual(ready)
  })

  it('sends the signed PDF as multipart form data', async () => {
    const active = { ...agreement, status: 'active' }
    const file = new File(['%PDF-1.4'], 'firmado.pdf', { type: 'application/pdf' })
    create_request.mockResolvedValue({ data: active })

    const result = await store.uploadSigned(7, file)
    const payload = create_request.mock.calls[0][1]

    expect(create_request).toHaveBeenCalledWith(
      'financing/agreements/7/upload-signed/',
      expect.any(FormData),
    )
    expect(payload.get('signed_document')).toEqual(file)
    expect(result.success).toBe(true)
    expect(store.currentAgreement.status).toBe('active')
  })
})
