import { setActivePinia, createPinia } from 'pinia'
import { usePlatformChangeRequestsStore } from '../../stores/platform-change-requests'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  const mockDelete = jest.fn()
  return {
    usePlatformApi: () => ({
      get: mockGet,
      post: mockPost,
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
    __mockDelete: mockDelete,
  }
})

const {
  __mockGet: mockGet,
  __mockPost: mockPost,
  __mockDelete: mockDelete,
} = require('../../composables/usePlatformApi')

describe('usePlatformChangeRequestsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformChangeRequestsStore()
    jest.clearAllMocks()
  })

  it('status count getters aggregate list', () => {
    store.changeRequests = [
      { status: 'pending' },
      { status: 'pending' },
      { status: 'evaluating' },
      { status: 'approved' },
      { status: 'rejected' },
    ]
    expect(store.pendingCount).toBe(2)
    expect(store.evaluatingCount).toBe(1)
    expect(store.approvedCount).toBe(1)
    expect(store.rejectedCount).toBe(1)
  })

  it('filteredByStatus returns full list for all', () => {
    store.changeRequests = [{ id: 1 }]
    expect(store.filteredByStatus('all')).toEqual([{ id: 1 }])
  })

  it('fetchChangeRequests sets projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchChangeRequests(8, null)
    expect(store.projectId).toBe(8)
  })

  it('fetchChangeRequest loads single item', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 4 } })
    const result = await store.fetchChangeRequest(1, 4)
    expect(result.success).toBe(true)
    expect(store.currentChangeRequest).toEqual({ id: 4 })
  })

  it('createChangeRequest posts JSON payload', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 2 } })
    const body = { title: 't' }
    await store.createChangeRequest(3, body)
    expect(mockPost).toHaveBeenCalledWith('projects/3/change-requests/', body, {})
  })

  it('createChangeRequest uses multipart for FormData', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 3 } })
    const fd = new FormData()
    await store.createChangeRequest(3, fd)
    expect(mockPost).toHaveBeenCalledWith(
      'projects/3/change-requests/',
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  })

  it('fetchAllChangeRequests clears projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchAllChangeRequests()
    expect(store.projectId).toBeNull()
  })

  it('evaluateChangeRequest updates current when ids match', async () => {
    store.changeRequests = [{ id: 10, status: 'pending' }]
    store.currentChangeRequest = { id: 10, status: 'pending' }
    mockPost.mockResolvedValueOnce({ data: { id: 10, status: 'approved' } })
    await store.evaluateChangeRequest(1, 10, {})
    expect(store.currentChangeRequest.status).toBe('approved')
  })

  it('deleteChangeRequest filters list', async () => {
    store.changeRequests = [{ id: 1 }]
    mockDelete.mockResolvedValueOnce({})
    await store.deleteChangeRequest(2, 1)
    expect(store.changeRequests).toEqual([])
  })

  it('addComment appends when current matches', async () => {
    store.currentChangeRequest = { id: 7, comments: [] }
    mockPost.mockResolvedValueOnce({ data: { id: 20 } })
    await store.addComment(1, 7, 'note', true)
    expect(store.currentChangeRequest.comments).toHaveLength(1)
  })

  it('convertToRequirement updates list entry', async () => {
    store.changeRequests = [{ id: 5, status: 'pending' }]
    mockPost.mockResolvedValueOnce({ data: { id: 5, status: 'converted' } })
    const result = await store.convertToRequirement(1, 5)
    expect(result.success).toBe(true)
    expect(store.changeRequests[0].status).toBe('converted')
  })

  it('fetchChangeRequests returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'x' } } })
    expect((await store.fetchChangeRequests(1)).success).toBe(false)
  })

  it('fetchChangeRequest returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'y' } } })
    expect((await store.fetchChangeRequest(1, 1)).success).toBe(false)
  })

  it('createChangeRequest returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'z' } } })
    expect((await store.createChangeRequest(1, {})).success).toBe(false)
  })

  it('fetchAllChangeRequests returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'a' } } })
    expect((await store.fetchAllChangeRequests()).success).toBe(false)
  })

  it('evaluateChangeRequest returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'b' } } })
    expect((await store.evaluateChangeRequest(1, 1, {})).success).toBe(false)
  })

  it('deleteChangeRequest returns failure on error', async () => {
    mockDelete.mockRejectedValueOnce({ response: { data: { detail: 'c' } } })
    expect((await store.deleteChangeRequest(1, 1)).success).toBe(false)
  })

  it('addComment returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'd' } } })
    expect((await store.addComment(1, 1, 'x', false)).success).toBe(false)
  })

  it('convertToRequirement returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'e' } } })
    expect((await store.convertToRequirement(1, 1)).success).toBe(false)
  })
})
