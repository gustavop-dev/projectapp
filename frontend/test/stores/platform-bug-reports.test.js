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

  describe('error fallback messages', () => {
    it('fetchBugReports uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchBugReports(1)
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos cargar los reportes de bugs.')
    })

    it('fetchAllBugReports uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchAllBugReports()
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos cargar los reportes de bugs.')
    })

    it('fetchBugReport uses fallback when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchBugReport(1, 1)
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos cargar el reporte de bug.')
    })

    it('createBugReport uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))
      const result = await store.createBugReport(1, {})
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos crear el reporte de bug.')
    })

    it('evaluateBugReport uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))
      const result = await store.evaluateBugReport(1, 1, {})
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos evaluar el reporte de bug.')
    })

    it('deleteBugReport uses fallback when detail is absent', async () => {
      mockDelete.mockRejectedValueOnce(new Error('network'))
      const result = await store.deleteBugReport(1, 1)
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos archivar el reporte de bug.')
    })

    it('addComment uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))
      const result = await store.addComment(1, 1, 'x', false)
      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos agregar el comentario.')
    })
  })

  describe('fetchAllBugReports with statusFilter', () => {
    it('appends status query when statusFilter is provided', async () => {
      mockGet.mockResolvedValueOnce({ data: [] })
      await store.fetchAllBugReports('reported')
      expect(mockGet).toHaveBeenCalledWith('bug-reports/?status=reported')
    })
  })

  describe('evaluateBugReport conditional branches', () => {
    it('does not update list when bug report id is not found', async () => {
      store.bugReports = [{ id: 99, status: 'reported' }]
      mockPost.mockResolvedValueOnce({ data: { id: 7, status: 'confirmed' } })
      await store.evaluateBugReport(1, 7, {})
      expect(store.bugReports[0].status).toBe('reported')
    })

    it('does not update currentBugReport when id does not match', async () => {
      store.bugReports = []
      store.currentBugReport = { id: 99, status: 'reported' }
      mockPost.mockResolvedValueOnce({ data: { id: 7, status: 'confirmed' } })
      await store.evaluateBugReport(1, 7, {})
      expect(store.currentBugReport.status).toBe('reported')
    })
  })

  describe('addComment conditional branches', () => {
    it('does not push when currentBugReport has no comments array', async () => {
      store.currentBugReport = { id: 5 }
      mockPost.mockResolvedValueOnce({ data: { id: 99 } })
      const result = await store.addComment(1, 5, 'hi', false)
      expect(result.success).toBe(true)
    })
  })

  describe('deleteBugReport detail message', () => {
    it('returns data detail as message when present', async () => {
      store.bugReports = [{ id: 1 }]
      mockDelete.mockResolvedValueOnce({ data: { detail: 'Archived.' } })
      const result = await store.deleteBugReport(1, 1)
      expect(result.success).toBe(true)
      expect(result.message).toBe('Archived.')
    })
  })

  describe('fetchAllBugReports error', () => {
    it('sets error from response detail', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'Bug reports no disponibles.' } } })
      const result = await store.fetchAllBugReports()
      expect(result.success).toBe(false)
      expect(result.message).toBe('Bug reports no disponibles.')
    })
  })

  describe('fetchBugReport error', () => {
    it('sets error from response detail', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'Bug no encontrado.' } } })
      const result = await store.fetchBugReport(1, 99)
      expect(result.success).toBe(false)
      expect(result.message).toBe('Bug no encontrado.')
    })
  })

  it('fetchBugReports uses fallback message when error has no detail', async () => {
    mockGet.mockRejectedValueOnce({})
    const result = await store.fetchBugReports(1)
    expect(result.message).toBe('No pudimos cargar los reportes de bugs.')
  })

  it('fetchAllBugReports uses fallback message when error has no detail', async () => {
    mockGet.mockRejectedValueOnce({})
    const result = await store.fetchAllBugReports()
    expect(result.message).toBe('No pudimos cargar los reportes de bugs.')
  })

  it('fetchAllBugReports appends status query when provided', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchAllBugReports('resolved')
    expect(mockGet).toHaveBeenCalledWith('bug-reports/?status=resolved')
  })

  it('fetchBugReport sets error on failure', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'bug load' } } })
    const result = await store.fetchBugReport(1, 1)
    expect(result.success).toBe(false)
    expect(result.message).toBe('bug load')
  })

  it('fetchBugReport uses fallback message when error has no detail', async () => {
    mockGet.mockRejectedValueOnce({})
    const result = await store.fetchBugReport(1, 1)
    expect(result.message).toBe('No pudimos cargar el reporte de bug.')
  })

  it('createBugReport uses fallback message when error has no detail', async () => {
    mockPost.mockRejectedValueOnce({})
    const result = await store.createBugReport(1, {})
    expect(result.message).toBe('No pudimos crear el reporte de bug.')
  })

  it('evaluateBugReport leaves list intact when bugId not found', async () => {
    store.bugReports = [{ id: 7, status: 'reported' }]
    mockPost.mockResolvedValueOnce({ data: { id: 99, status: 'confirmed' } })
    await store.evaluateBugReport(1, 99, {})
    expect(store.bugReports[0].status).toBe('reported')
  })

  it('evaluateBugReport does not touch currentBugReport when ids differ', async () => {
    store.currentBugReport = { id: 7, status: 'reported' }
    mockPost.mockResolvedValueOnce({ data: { id: 99, status: 'confirmed' } })
    await store.evaluateBugReport(1, 99, {})
    expect(store.currentBugReport.status).toBe('reported')
  })

  it('evaluateBugReport uses fallback message when error has no detail', async () => {
    mockPost.mockRejectedValueOnce({})
    const result = await store.evaluateBugReport(1, 1, {})
    expect(result.message).toBe('No pudimos evaluar el reporte de bug.')
  })

  it('deleteBugReport returns detail message on success when provided', async () => {
    store.bugReports = [{ id: 1 }]
    mockDelete.mockResolvedValueOnce({ data: { detail: 'Archivado.' } })
    const result = await store.deleteBugReport(2, 1)
    expect(result.message).toBe('Archivado.')
  })

  it('deleteBugReport uses fallback message when error has no detail', async () => {
    mockDelete.mockRejectedValueOnce({})
    const result = await store.deleteBugReport(1, 1)
    expect(result.message).toBe('No pudimos archivar el reporte de bug.')
  })

  it('addComment skips push when currentBugReport has no comments array', async () => {
    store.currentBugReport = { id: 5 }
    mockPost.mockResolvedValueOnce({ data: { id: 99 } })
    const result = await store.addComment(1, 5, 'x', false)
    expect(result.success).toBe(true)
    expect(store.currentBugReport.comments).toBeUndefined()
  })

  it('addComment uses fallback message when error has no detail', async () => {
    mockPost.mockRejectedValueOnce({})
    const result = await store.addComment(1, 1, 'x', false)
    expect(result.message).toBe('No pudimos agregar el comentario.')
  })
})
