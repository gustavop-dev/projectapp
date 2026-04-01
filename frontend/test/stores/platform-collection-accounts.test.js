import { setActivePinia, createPinia } from 'pinia'
import { usePlatformCollectionAccountsStore } from '../../stores/platform-collection-accounts'

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

describe('usePlatformCollectionAccountsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformCollectionAccountsStore()
    jest.clearAllMocks()
  })

  it('fetchList stores response data on success', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1, title: 'A' }] })
    const result = await store.fetchList({ project_id: 5 })
    expect(result.success).toBe(true)
    expect(mockGet).toHaveBeenCalledWith('collection-accounts/', { params: { project_id: 5 } })
    expect(store.accounts).toEqual([{ id: 1, title: 'A' }])
  })

  it('fetchList returns failure with message on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'bad' } } })
    const result = await store.fetchList()
    expect(result.success).toBe(false)
    expect(result.message).toBe('bad')
  })

  it('fetchByProject passes deliverable_id in params', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await store.fetchByProject(3, 99)
    expect(mockGet).toHaveBeenCalledWith('projects/3/collection-accounts/', {
      params: { deliverable_id: 99 },
    })
  })

  it('fetchByProject omits deliverable_id when null', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1 }] })
    await store.fetchByProject(3, null)
    expect(mockGet).toHaveBeenCalledWith('projects/3/collection-accounts/', { params: {} })
  })

  it('fetchDetail sets currentAccount', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 7 } })
    const result = await store.fetchDetail(7)
    expect(result.success).toBe(true)
    expect(store.currentAccount).toEqual({ id: 7 })
  })

  it('create sets currentAccount from response', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 2 } })
    const result = await store.create({ title: 'x' })
    expect(result.success).toBe(true)
    expect(mockPost).toHaveBeenCalledWith('collection-accounts/', { title: 'x' })
  })

  it('create uses string message when detail is missing', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { field: ['x'] } } })
    const result = await store.create({})
    expect(result.success).toBe(false)
    expect(store.error).toBe('Could not create.')
  })

  it('update patches account', async () => {
    mockPatch.mockResolvedValueOnce({ data: { id: 1, status: 'draft' } })
    const result = await store.update(1, { status: 'draft' })
    expect(result.success).toBe(true)
    expect(store.currentAccount).toEqual({ id: 1, status: 'draft' })
  })

  it('update returns errors object on failure', async () => {
    mockPatch.mockRejectedValueOnce({ response: { data: { detail: 'nope' } } })
    const result = await store.update(1, {})
    expect(result.success).toBe(false)
    expect(result.errors).toEqual({ detail: 'nope' })
  })

  it('issue calls post endpoint', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1, commercial_status: 'issued' } })
    const result = await store.issue(1)
    expect(result.success).toBe(true)
    expect(mockPost).toHaveBeenCalledWith('collection-accounts/1/issue/')
  })

  it('markPaid posts mark-paid', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1, paid: true } })
    const result = await store.markPaid(1)
    expect(result.success).toBe(true)
    expect(mockPost).toHaveBeenCalledWith('collection-accounts/1/mark-paid/')
  })

  it('markCancelled posts mark-cancelled', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1, cancelled: true } })
    const result = await store.markCancelled(1)
    expect(result.success).toBe(true)
  })

  it('downloadPdf creates object URL and clicks link', async () => {
    const prevCreate = window.URL.createObjectURL
    const prevRevoke = window.URL.revokeObjectURL
    window.URL.createObjectURL = jest.fn(() => 'blob:x')
    window.URL.revokeObjectURL = jest.fn()
    const link = { href: '', setAttribute: jest.fn(), click: jest.fn(), remove: jest.fn() }
    jest.spyOn(document, 'createElement').mockReturnValue(link)
    jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    mockGet.mockResolvedValueOnce({ data: new Blob(['p']) })

    const result = await store.downloadPdf(5, 'My Title Here')

    expect(result.success).toBe(true)
    expect(mockGet).toHaveBeenCalledWith(
      'collection-accounts/5/pdf/',
      { responseType: 'blob' },
    )
    expect(link.setAttribute).toHaveBeenCalledWith('download', 'My-Title-Here.pdf')
    expect(link.click).toHaveBeenCalled()
    window.URL.createObjectURL = prevCreate
    window.URL.revokeObjectURL = prevRevoke
    document.createElement.mockRestore()
    document.body.appendChild.mockRestore()
  })

  it('downloadPdf returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'pdf bad' } } })
    const result = await store.downloadPdf(1)
    expect(result.success).toBe(false)
    expect(result.message).toBe('pdf bad')
  })

  it('fetchByProject returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'proj' } } })
    const result = await store.fetchByProject(1)
    expect(result.success).toBe(false)
  })

  it('fetchDetail returns failure on error', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { detail: 'nf' } } })
    const result = await store.fetchDetail(1)
    expect(result.success).toBe(false)
  })

  it('issue returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'iss' } } })
    const result = await store.issue(1)
    expect(result.success).toBe(false)
  })

  it('markPaid returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'mp' } } })
    const result = await store.markPaid(1)
    expect(result.success).toBe(false)
  })

  it('markCancelled returns failure on error', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'mc' } } })
    const result = await store.markCancelled(1)
    expect(result.success).toBe(false)
  })
})
