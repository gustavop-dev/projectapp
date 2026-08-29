import { createPinia, setActivePinia } from 'pinia'
import { useAdditionalModulesStore } from '../../stores/additional_modules'

jest.mock('../../stores/services/request_http', () => ({
  create_request: jest.fn(),
  get_request: jest.fn(),
  patch_request: jest.fn(),
}))

const {
  create_request,
  get_request,
} = require('../../stores/services/request_http')

const CATALOG = {
  categories: [{ id: 1, name_es: 'Pagos', is_active: true }],
  modules: [{ id: 10, category: 1, name_es: 'Facturación', is_active: true }],
  revision: 'revision-1',
}

describe('useAdditionalModulesStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAdditionalModulesStore()
    jest.clearAllMocks()
  })

  it('loads the complete admin catalog', async () => {
    get_request.mockResolvedValue({ data: CATALOG })

    const result = await store.fetchCatalog()

    expect(result.success).toBe(true)
    expect(store.categories).toEqual(CATALOG.categories)
    expect(store.modules).toEqual(CATALOG.modules)
    expect(store.revision).toBe('revision-1')
    expect(get_request).toHaveBeenCalledWith('additional-modules/admin/')
  })

  it('sends the current revision when reordering', async () => {
    store.revision = 'revision-1'
    create_request.mockResolvedValue({ data: { revision: 'revision-2' } })
    get_request.mockResolvedValue({ data: { ...CATALOG, revision: 'revision-2' } })

    const result = await store.reorderCatalog({
      category_ids: [1],
      module_groups: [{ category_id: 1, module_ids: [10] }],
    })

    expect(result.success).toBe(true)
    expect(create_request).toHaveBeenCalledWith('additional-modules/admin/reorder/', {
      revision: 'revision-1',
      category_ids: [1],
      module_groups: [{ category_id: 1, module_ids: [10] }],
    })
    expect(store.revision).toBe('revision-2')
  })

  it('refreshes the catalog after an optimistic-lock conflict', async () => {
    store.revision = 'stale'
    create_request.mockRejectedValue({
      response: { status: 409, data: { detail: 'El catálogo cambió.' } },
    })
    get_request.mockResolvedValue({ data: CATALOG })

    const result = await store.reorderCatalog({
      category_ids: [1],
      module_groups: [{ category_id: 1, module_ids: [10] }],
    })

    expect(result.success).toBe(false)
    expect(result.errors.detail).toBe('El catálogo cambió.')
    expect(get_request).toHaveBeenCalledWith('additional-modules/admin/')
    expect(store.revision).toBe('revision-1')
  })

  it('prepends a newly generated share link', async () => {
    const link = { uuid: 'share-1', public_path: '/es-co/additional-modules/share/share-1' }
    create_request.mockResolvedValue({ data: link })

    const result = await store.createShareLink({
      recipient_label: 'Acme',
      language: 'es',
      module_ids: [10],
    })

    expect(result.success).toBe(true)
    expect(store.shareLinks).toEqual([link])
  })

  it('requests the PDF as a blob', async () => {
    const blob = new Blob(['pdf'], { type: 'application/pdf' })
    create_request.mockResolvedValue({ data: blob })

    const result = await store.downloadPdf({ language: 'es', module_ids: [10] })

    expect(result).toEqual({ success: true, data: blob })
    expect(create_request).toHaveBeenCalledWith(
      'additional-modules/admin/pdf/',
      { language: 'es', module_ids: [10] },
      { responseType: 'blob' },
    )
  })

  it('decodes a JSON error returned as a PDF blob', async () => {
    const errorBlob = new Blob(
      [JSON.stringify({ detail: 'No se pudo generar el PDF.' })],
      { type: 'application/json' },
    )
    create_request.mockRejectedValue({ response: { status: 500, data: errorBlob } })

    const result = await store.downloadPdf({ language: 'es', module_ids: [10] })

    expect(result).toEqual({
      success: false,
      errors: { detail: 'No se pudo generar el PDF.' },
    })
  })
})
