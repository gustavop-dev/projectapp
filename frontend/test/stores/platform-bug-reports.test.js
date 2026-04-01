import { setActivePinia, createPinia } from 'pinia'
import { usePlatformBugReportsStore } from '../../stores/platform-bug-reports'

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

describe('usePlatformBugReportsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformBugReportsStore()
    jest.clearAllMocks()
  })

  it('count getters group by status', () => {
    store.bugReports = [
      { status: 'reported' },
      { status: 'reported' },
      { status: 'confirmed' },
      { status: 'fixing' },
      { status: 'resolved' },
    ]
    expect(store.reportedCount).toBe(2)
    expect(store.confirmedCount).toBe(1)
    expect(store.fixingCount).toBe(1)
    expect(store.resolvedCount).toBe(1)
  })

  it('filteredByStatus returns all when filter is all', () => {
    store.bugReports = [{ id: 1 }]
    expect(store.filteredByStatus('all')).toEqual([{ id: 1 }])
  })

  it('filteredByStatus returns empty when filter null', () => {
    store.bugReports = [{ id: 1 }]
    expect(store.filteredByStatus(null)).toEqual([{ id: 1 }])
  })

  it('filteredByStatus filters by status', () => {
    store.bugReports = [{ id: 1, status: 'open' }, { id: 2, status: 'closed' }]
    expect(store.filteredByStatus('open')).toEqual([{ id: 1, status: 'open' }])
  })

  it('fetchBugReports appends status query', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchBugReports(5, 'reported')
    expect(mockGet).toHaveBeenCalledWith('projects/5/bug-reports/?status=reported')
    expect(store.projectId).toBe(5)
  })

  it('fetchBugReports adds include_archived when requested', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchBugReports(5, null, true)
    expect(mockGet).toHaveBeenCalledWith('projects/5/bug-reports/?include_archived=1')
  })

  it('fetchAllBugReports adds include_archived when requested', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchAllBugReports(null, true)
    expect(mockGet).toHaveBeenCalledWith('bug-reports/?include_archived=1')
  })

  it('fetchAllBugReports clears projectId', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1 }] })
    await store.fetchAllBugReports()
    expect(store.projectId).toBeNull()
    expect(store.bugReports).toEqual([{ id: 1 }])
  })

  it('fetchBugReport sets currentBugReport', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 9 } })
    const result = await store.fetchBugReport(1, 9)
    expect(result.success).toBe(true)
    expect(store.currentBugReport).toEqual({ id: 9 })
  })

  it('createBugReport posts JSON without multipart header', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 3 } })
    const payload = { deliverable_id: 10, title: 'x' }
    const result = await store.createBugReport(2, payload)
    expect(mockPost).toHaveBeenCalledWith('projects/2/bug-reports/', payload, {})
    expect(store.bugReports[0]).toEqual({ id: 3 })
    expect(result.success).toBe(true)
  })

  it('createBugReport sends multipart header for FormData', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 4 } })
    const fd = new FormData()
    await store.createBugReport(2, fd)
    expect(mockPost).toHaveBeenCalledWith(
      'projects/2/bug-reports/',
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  })

  it('evaluateBugReport merges into list and current', async () => {
    store.bugReports = [{ id: 7, status: 'reported' }]
    store.currentBugReport = { id: 7, status: 'reported', comments: [] }
    mockPost.mockResolvedValueOnce({ data: { id: 7, status: 'confirmed' } })
    const result = await store.evaluateBugReport(1, 7, { ok: true })
    expect(result.success).toBe(true)
    expect(store.bugReports[0].status).toBe('confirmed')
    expect(store.currentBugReport.status).toBe('confirmed')
  })

  it('deleteBugReport removes from list', async () => {
    store.bugReports = [{ id: 1 }]
    mockDelete.mockResolvedValueOnce({})
    const result = await store.deleteBugReport(3, 1)
    expect(result.success).toBe(true)
    expect(store.bugReports).toEqual([])
  })

  it('addComment pushes onto currentBugReport comments', async () => {
    store.currentBugReport = { id: 5, comments: [] }
    mockPost.mockResolvedValueOnce({ data: { id: 99, text: 'hi' } })
    const result = await store.addComment(1, 5, 'hi', false)
    expect(result.success).toBe(true)
    expect(store.currentBugReport.comments).toHaveLength(1)
  })

  it('addComment skips push when current id differs', async () => {
    store.currentBugReport = { id: 5, comments: [] }
    mockPost.mockResolvedValueOnce({ data: { id: 99 } })
    await store.addComment(1, 6, 'x', false)
    expect(store.currentBugReport.comments).toEqual([])
  })

  it('fetchBugReports sets error on failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'e' } } })
    const result = await store.fetchBugReports(1)
    expect(result.success).toBe(false)
  })

  it('createBugReport sets error on failure', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'c' } } })
    const result = await store.createBugReport(1, {})
    expect(result.success).toBe(false)
  })

  it('evaluateBugReport sets error on failure', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'ev' } } })
    const result = await store.evaluateBugReport(1, 1, {})
    expect(result.success).toBe(false)
  })

  it('deleteBugReport sets error on failure', async () => {
    mockDelete.mockRejectedValueOnce({ response: { data: { detail: 'd' } } })
    const result = await store.deleteBugReport(1, 1)
    expect(result.success).toBe(false)
  })

  it('addComment returns failure when post rejects', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'cm' } } })
    const result = await store.addComment(1, 1, 'x', true)
    expect(result.success).toBe(false)
  })
})
