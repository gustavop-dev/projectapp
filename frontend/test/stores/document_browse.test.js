import { createPinia, setActivePinia } from 'pinia'
import { useDocumentStore } from '../../stores/documents'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const { get_request } = require('../../stores/services/request_http')

function page(results, overrides = {}) {
  return {
    data: {
      results,
      count: results.length,
      page: 1,
      page_size: 10,
      total_pages: 1,
      ...overrides,
    },
  }
}

describe('document manager server browsing', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useDocumentStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    store.cancelDocumentBrowse()
    store.cancelDocumentSearch()
    jest.restoreAllMocks()
  })

  it('stores rows and authoritative pagination from the browse envelope', async () => {
    get_request.mockResolvedValueOnce(page([{ id: 7 }], {
      count: 21, page: 2, total_pages: 3,
    }))

    const result = await store.browseDocuments({ page: 2 })

    expect(result.success).toBe(true)
    expect(store.documents).toEqual([{ id: 7 }])
    expect(store.browsePagination).toEqual({
      page: 2, page_size: 10, count: 21, total_pages: 3,
    })
    expect(get_request).toHaveBeenCalledWith(
      'documents/browse/?scope=active&page=2&page_size=10',
      { signal: expect.any(AbortSignal) },
    )
  })

  it('sends the contextual root and every active manager filter', async () => {
    store.activeFolderId = 'root'
    store.activeProjectId = 4
    store.activeStateIds = [8]
    store.withoutStateIds = [9]
    store.browsePageSize = 12
    get_request.mockResolvedValueOnce(page([], { page_size: 12 }))

    await store.browseDocuments()

    expect(get_request.mock.calls[0][0]).toBe(
      'documents/browse/?scope=active&page=1&page_size=12&folder=root'
      + '&states=8&without_states=9&project=4',
    )
  })

  it('resets a project-root browse to page one', async () => {
    store.browsePageSize = 12
    store.browsePagination.page = 4
    get_request.mockResolvedValueOnce(page([], { page_size: 12 }))

    await store.setBrowseFilters({ folder: 'root', project: 4 })

    expect(get_request.mock.calls[0][0]).toBe(
      'documents/browse/?scope=active&page=1&page_size=12&folder=root&project=4',
    )
  })

  it('keeps only the latest response when folder requests overlap', async () => {
    let resolveFirst
    const firstResponse = new Promise((resolve) => { resolveFirst = resolve })
    get_request
      .mockReturnValueOnce(firstResponse)
      .mockResolvedValueOnce(page([{ id: 2 }]))

    const first = store.browseDocuments({ folder: 1 })
    const second = store.browseDocuments({ folder: 2 })
    const secondResult = await second
    resolveFirst(page([{ id: 1 }]))
    const firstResult = await first

    expect(secondResult.success).toBe(true)
    expect(firstResult.cancelled).toBe(true)
    expect(store.documents).toEqual([{ id: 2 }])
  })

  it('aborts a superseded folder browse request', async () => {
    let resolveFirst
    const firstResponse = new Promise((resolve) => { resolveFirst = resolve })
    get_request
      .mockReturnValueOnce(firstResponse)
      .mockResolvedValueOnce(page([{ id: 2 }]))

    const first = store.browseDocuments({ folder: 1 })
    const firstSignal = get_request.mock.calls[0][1].signal
    const second = store.browseDocuments({ folder: 2 })

    expect(firstSignal.aborted).toBe(true)
    await second
    resolveFirst(page([{ id: 1 }]))
    await first
    expect(store.documents).toEqual([{ id: 2 }])
  })

  it('paginates global search through the same compact endpoint', async () => {
    get_request.mockResolvedValueOnce(page([{ id: 11 }], {
      count: 14, page: 2, total_pages: 2,
    }))

    await store.searchDocuments('Acme', { page: 2, order: 'oldest' })

    expect(store.searchResults).toEqual([{ id: 11 }])
    expect(store.searchPagination.count).toBe(14)
    expect(get_request).toHaveBeenCalledWith(
      'documents/browse/?scope=all&search=Acme&page=2&page_size=10&order=oldest',
      { signal: expect.any(AbortSignal) },
    )
  })
})
