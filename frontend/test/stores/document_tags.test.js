/**
 * Tests for document_tags store (panel admin).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentTagStore } from '../../stores/document_tags'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const {
  get_request,
  create_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http')

describe('useDocumentTagStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useDocumentTagStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('fetchTags stores list on success', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 1, name: 'Urgente', color: 'red' }] })
    await store.fetchTags()
    expect(store.tags).toEqual([{ id: 1, name: 'Urgente', color: 'red' }])
    expect(get_request).toHaveBeenCalledWith('document-tags/')
  })

  it('fetchTags sets error on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.fetchTags()
    expect(result.success).toBe(false)
    expect(store.error).toBe('fetch_tags_failed')
  })

  it('createTag appends and sorts alphabetically', async () => {
    store.tags = [{ id: 1, name: 'Zulu', color: 'gray' }]
    create_request.mockResolvedValueOnce({ data: { id: 2, name: 'Alpha', color: 'blue' } })
    await store.createTag({ name: 'Alpha', color: 'blue' })
    expect(create_request).toHaveBeenCalledWith(
      'document-tags/create/', { name: 'Alpha', color: 'blue' },
    )
    expect(store.tags.map((t) => t.name)).toEqual(['Alpha', 'Zulu'])
  })

  it('createTag sets error on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.createTag({ name: 'X' })
    expect(result.success).toBe(false)
    expect(store.error).toBe('create_tag_failed')
  })

  it('updateTag replaces entry', async () => {
    store.tags = [{ id: 9, name: 'Old', color: 'gray' }]
    patch_request.mockResolvedValueOnce({ data: { id: 9, name: 'New', color: 'red' } })
    await store.updateTag(9, { name: 'New', color: 'red' })
    expect(patch_request).toHaveBeenCalledWith(
      'document-tags/9/update/', { name: 'New', color: 'red' },
    )
    expect(store.tags[0]).toEqual({ id: 9, name: 'New', color: 'red' })
  })

  it('updateTag sets error on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.updateTag(1, {})
    expect(result.success).toBe(false)
    expect(store.error).toBe('update_tag_failed')
  })

  it('deleteTag removes the entry', async () => {
    store.tags = [{ id: 1 }, { id: 2 }]
    delete_request.mockResolvedValueOnce({})
    await store.deleteTag(1)
    expect(delete_request).toHaveBeenCalledWith('document-tags/1/delete/')
    expect(store.tags).toEqual([{ id: 2 }])
  })

  it('deleteTag sets error on failure', async () => {
    delete_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.deleteTag(1)
    expect(result.success).toBe(false)
    expect(store.error).toBe('delete_tag_failed')
  })
})
