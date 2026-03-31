import { setActivePinia, createPinia } from 'pinia'
import { usePlatformDeliverablesStore } from '../../stores/platform-deliverables'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  const mockPatch = jest.fn()
  const mockDelete = jest.fn()
  return {
    usePlatformApi: () => ({
      get: mockGet,
      post: mockPost,
      patch: mockPatch,
      delete: mockDelete,
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
    __mockDelete: mockDelete,
  }
})

const {
  __mockGet: mockGet,
  __mockPost: mockPost,
  __mockPatch: mockPatch,
  __mockDelete: mockDelete,
} = require('../../composables/usePlatformApi')

describe('usePlatformDeliverablesStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformDeliverablesStore()
    jest.clearAllMocks()
  })

  it('totalCount returns length', () => {
    store.deliverables = [{ id: 1 }, { id: 2 }]
    expect(store.totalCount).toBe(2)
  })

  it('groupedByCategory orders known categories', () => {
    store.deliverables = [
      { id: 1, category: 'documents' },
      { id: 2, category: 'designs' },
    ]
    const groups = store.groupedByCategory
    expect(groups.map((g) => g.category)).toEqual(['designs', 'documents'])
  })

  it('groupedByCategory omits empty categories', () => {
    store.deliverables = [{ id: 1, category: 'other' }]
    expect(store.groupedByCategory).toHaveLength(1)
  })

  it('fetchDeliverables sets projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchDeliverables(4, null)
    expect(store.projectId).toBe(4)
  })

  it('fetchDeliverables appends category query', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchDeliverables(1, 'apks')
    expect(mockGet).toHaveBeenCalledWith('projects/1/deliverables/?category=apks')
  })

  it('fetchAllDeliverables clears projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchAllDeliverables()
    expect(store.projectId).toBeNull()
  })

  it('fetchDeliverable sets current', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 9 } })
    const result = await store.fetchDeliverable(2, 9)
    expect(result.success).toBe(true)
    expect(store.currentDeliverable).toEqual({ id: 9 })
  })

  it('createDeliverable prepends with multipart', async () => {
    const fd = new FormData()
    mockPost.mockResolvedValueOnce({ data: { id: 3 } })
    await store.createDeliverable(1, fd)
    expect(mockPost).toHaveBeenCalledWith(
      'projects/1/deliverables/',
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    expect(store.deliverables[0].id).toBe(3)
  })

  it('updateDeliverable merges into list and current', async () => {
    store.deliverables = [{ id: 5, name: 'a' }]
    store.currentDeliverable = { id: 5, name: 'a' }
    mockPatch.mockResolvedValueOnce({ data: { id: 5, name: 'b' } })
    await store.updateDeliverable(1, 5, { name: 'b' })
    expect(store.deliverables[0].name).toBe('b')
    expect(store.currentDeliverable.name).toBe('b')
  })

  it('deleteDeliverable removes id', async () => {
    store.deliverables = [{ id: 1 }]
    mockDelete.mockResolvedValueOnce({})
    await store.deleteDeliverable(1, 1)
    expect(store.deliverables).toEqual([])
  })

  it('uploadNewVersion merges response', async () => {
    store.deliverables = [{ id: 8, v: 1 }]
    store.currentDeliverable = { id: 8, v: 1 }
    const fd = new FormData()
    mockPost.mockResolvedValueOnce({ data: { id: 8, v: 2 } })
    await store.uploadNewVersion(1, 8, fd)
    expect(store.deliverables[0].v).toBe(2)
  })

  it('fetchDeliverables returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'e' } } })
    expect((await store.fetchDeliverables(1)).success).toBe(false)
  })

  it('fetchAllDeliverables returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'f' } } })
    expect((await store.fetchAllDeliverables()).success).toBe(false)
  })

  it('fetchDeliverable returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'g' } } })
    expect((await store.fetchDeliverable(1, 1)).success).toBe(false)
  })

  it('createDeliverable returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'h' } } })
    expect((await store.createDeliverable(1, new FormData())).success).toBe(false)
  })

  it('updateDeliverable returns failure on error', async () => {
    mockPatch.mockRejectedValueOnce({ response: { data: { detail: 'i' } } })
    expect((await store.updateDeliverable(1, 1, {})).success).toBe(false)
  })

  it('deleteDeliverable returns failure on error', async () => {
    mockDelete.mockRejectedValueOnce({ response: { data: { detail: 'j' } } })
    expect((await store.deleteDeliverable(1, 1)).success).toBe(false)
  })

  it('uploadNewVersion returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'k' } } })
    expect((await store.uploadNewVersion(1, 1, new FormData())).success).toBe(false)
  })
})
