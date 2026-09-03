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
