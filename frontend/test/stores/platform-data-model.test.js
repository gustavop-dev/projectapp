import { setActivePinia, createPinia } from 'pinia'
import { usePlatformDataModelStore } from '../../stores/platform-data-model'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  return {
    usePlatformApi: () => ({
      get: mockGet,
      post: mockPost,
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
  }
})

const {
  __mockGet: mockGet,
  __mockPost: mockPost,
} = require('../../composables/usePlatformApi')

describe('usePlatformDataModelStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformDataModelStore()
    jest.clearAllMocks()
  })

  // =========================================================================
  // entityCount getter
  // =========================================================================

  it('entityCount returns zero when entities is empty', () => {
    store.entities = []
    expect(store.entityCount).toBe(0)
  })

  it('entityCount returns length of entities array', () => {
    store.entities = [{ id: 1 }, { id: 2 }, { id: 3 }]
    expect(store.entityCount).toBe(3)
  })

  // =========================================================================
  // fetchEntities
  // =========================================================================

  it('fetchEntities sets projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchEntities(7)
    expect(store.projectId).toBe(7)
  })

  it('fetchEntities calls correct endpoint', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchEntities(5)
    expect(mockGet).toHaveBeenCalledWith('projects/5/data-model-entities/')
  })

  it('fetchEntities populates entities on success', async () => {
    const fakeEntities = [{ id: 1, name: 'User' }, { id: 2, name: 'Order' }]
    mockGet.mockResolvedValueOnce({ data: fakeEntities })
    await store.fetchEntities(1)
    expect(store.entities).toEqual(fakeEntities)
  })

  it('fetchEntities returns success true on success', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    const result = await store.fetchEntities(1)
    expect(result.success).toBe(true)
  })

  it('fetchEntities sets isLoading to false after success', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchEntities(1)
    expect(store.isLoading).toBe(false)
  })

  it('fetchEntities clears error before fetching', async () => {
    store.error = 'old error'
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchEntities(1)
    expect(store.error).toBe('')
  })

  it('fetchEntities sets error message on failure', async () => {
    mockGet.mockRejectedValueOnce({
      response: { data: { detail: 'No autorizado' } },
    })
    await store.fetchEntities(1)
    expect(store.error).toBe('No autorizado')
  })

  it('fetchEntities uses fallback error message when no detail', async () => {
    mockGet.mockRejectedValueOnce({})
    await store.fetchEntities(1)
    expect(store.error).toBe('No pudimos cargar el modelo de datos.')
  })

  it('fetchEntities returns success false on failure', async () => {
    mockGet.mockRejectedValueOnce({})
    const result = await store.fetchEntities(1)
    expect(result.success).toBe(false)
  })

  it('fetchEntities leaves entities unchanged on failure', async () => {
    store.entities = [{ id: 99, name: 'Existing' }]
    mockGet.mockRejectedValueOnce({})
    await store.fetchEntities(1)
    expect(store.entities).toEqual([{ id: 99, name: 'Existing' }])
  })

  it('fetchEntities sets isLoading to false after failure', async () => {
    mockGet.mockRejectedValueOnce({})
    await store.fetchEntities(1)
    expect(store.isLoading).toBe(false)
  })

  // =========================================================================
  // uploadEntities
  // =========================================================================

  it('uploadEntities calls correct endpoint with payload', async () => {
    const payload = { entities: [{ name: 'User' }] }
    mockPost.mockResolvedValueOnce({ data: [{ id: 1, name: 'User' }] })
    await store.uploadEntities(3, payload)
    expect(mockPost).toHaveBeenCalledWith('projects/3/data-model-entities/', payload)
  })

  it('uploadEntities updates entities with response data on success', async () => {
    const returned = [{ id: 1, name: 'User' }]
    mockPost.mockResolvedValueOnce({ data: returned })
    await store.uploadEntities(3, { entities: [{ name: 'User' }] })
    expect(store.entities).toEqual(returned)
  })

  it('uploadEntities returns success true on success', async () => {
    mockPost.mockResolvedValueOnce({ data: [] })
    const result = await store.uploadEntities(3, { entities: [] })
    expect(result.success).toBe(true)
  })

  it('uploadEntities sets isUploading to false after success', async () => {
    mockPost.mockResolvedValueOnce({ data: [] })
    await store.uploadEntities(3, { entities: [] })
    expect(store.isUploading).toBe(false)
  })

  it('uploadEntities clears error before uploading', async () => {
    store.error = 'previous error'
    mockPost.mockResolvedValueOnce({ data: [] })
    await store.uploadEntities(3, { entities: [] })
    expect(store.error).toBe('')
  })

  it('uploadEntities sets error message on failure', async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { detail: 'Solo administradores' } },
    })
    await store.uploadEntities(3, { entities: [] })
    expect(store.error).toBe('Solo administradores')
  })

  it('uploadEntities uses fallback error message when no detail', async () => {
    mockPost.mockRejectedValueOnce({})
    await store.uploadEntities(3, { entities: [] })
    expect(store.error).toBe('No pudimos subir el modelo de datos.')
  })

  it('uploadEntities returns success false on failure', async () => {
    mockPost.mockRejectedValueOnce({})
    const result = await store.uploadEntities(3, { entities: [] })
    expect(result.success).toBe(false)
  })

  it('uploadEntities sets isUploading to false after failure', async () => {
    mockPost.mockRejectedValueOnce({})
    await store.uploadEntities(3, { entities: [] })
    expect(store.isUploading).toBe(false)
  })

  // =========================================================================
  // fetchTemplate
  // =========================================================================

  it('fetchTemplate calls correct endpoint', async () => {
    mockGet.mockResolvedValueOnce({ data: { entities: [] } })
    await store.fetchTemplate(4)
    expect(mockGet).toHaveBeenCalledWith('projects/4/data-model-entities/template/')
  })

  it('fetchTemplate returns success true with data on success', async () => {
    const template = { entities: [{ name: 'ExampleEntity' }] }
    mockGet.mockResolvedValueOnce({ data: template })
    const result = await store.fetchTemplate(4)
    expect(result.success).toBe(true)
    expect(result.data).toEqual(template)
  })

  it('fetchTemplate returns success false on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('network'))
    const result = await store.fetchTemplate(4)
    expect(result.success).toBe(false)
  })

  it('fetchTemplate returns message on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('network'))
    const result = await store.fetchTemplate(4)
    expect(result.message).toBe('No pudimos obtener la plantilla.')
  })
})
