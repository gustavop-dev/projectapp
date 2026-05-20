/**
 * Tests for document_folders store (panel admin).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentFolderStore } from '../../stores/document_folders'

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

describe('useDocumentFolderStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useDocumentFolderStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('fetchFolders stores list on success', async () => {
    get_request.mockResolvedValueOnce({ data: [{ id: 1, name: 'X', order: 0 }] })
    const result = await store.fetchFolders()
    expect(result.success).toBe(true)
    expect(store.folders).toEqual([{ id: 1, name: 'X', order: 0 }])
    expect(get_request).toHaveBeenCalledWith('document-folders/')
  })

  it('fetchFolders sets error on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: { detail: 'x' } } })
    const result = await store.fetchFolders()
    expect(result.success).toBe(false)
    expect(store.error).toBe('fetch_folders_failed')
  })

  it('createFolder appends and keeps sort order', async () => {
    store.folders = [{ id: 1, name: 'Alpha', order: 0 }]
    create_request.mockResolvedValueOnce({ data: { id: 2, name: 'Zeta', order: 0 } })
    const result = await store.createFolder({ name: 'Zeta' })
    expect(create_request).toHaveBeenCalledWith('document-folders/create/', { name: 'Zeta' })
    expect(result.success).toBe(true)
    expect(store.folders.map((f) => f.name)).toEqual(['Alpha', 'Zeta'])
  })

  it('createFolder returns errors on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { name: ['required'] } } })
    const result = await store.createFolder({})
    expect(result.success).toBe(false)
    expect(store.error).toBe('create_folder_failed')
  })

  it('updateFolder replaces the entry', async () => {
    store.folders = [{ id: 3, name: 'Old', order: 0 }]
    patch_request.mockResolvedValueOnce({ data: { id: 3, name: 'New', order: 0 } })
    await store.updateFolder(3, { name: 'New' })
    expect(patch_request).toHaveBeenCalledWith('document-folders/3/update/', { name: 'New' })
    expect(store.folders[0].name).toBe('New')
  })

  it('updateFolder sets error on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.updateFolder(1, { name: 'x' })
    expect(result.success).toBe(false)
    expect(store.error).toBe('update_folder_failed')
  })

  it('deleteFolder removes the entry', async () => {
    store.folders = [{ id: 1, name: 'A' }, { id: 2, name: 'B' }]
    delete_request.mockResolvedValueOnce({})
    await store.deleteFolder(1)
    expect(delete_request).toHaveBeenCalledWith('document-folders/1/delete/')
    expect(store.folders).toEqual([{ id: 2, name: 'B' }])
  })

  it('deleteFolder sets error on failure', async () => {
    delete_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.deleteFolder(1)
    expect(result.success).toBe(false)
    expect(store.error).toBe('delete_folder_failed')
  })

  it('deleteFolder propagates 409 detail and keeps folders unchanged', async () => {
    store.folders = [{ id: 1, name: 'A' }, { id: 2, name: 'B' }]
    delete_request.mockRejectedValueOnce({
      response: {
        status: 409,
        data: { detail: 'La carpeta tiene 2 documento(s).', document_count: 2 },
      },
    })
    const result = await store.deleteFolder(1)
    expect(result.success).toBe(false)
    expect(result.errors).toEqual({
      detail: 'La carpeta tiene 2 documento(s).',
      document_count: 2,
    })
    expect(store.folders).toEqual([{ id: 1, name: 'A' }, { id: 2, name: 'B' }])
  })

  describe('hierarchy getters', () => {
    // Árbol: 1 (raíz) -> 2 -> 4 ; 1 -> 3 ; 5 (raíz)
    beforeEach(() => {
      store.folders = [
        { id: 1, name: 'Root A', parent: null },
        { id: 2, name: 'Child', parent: 1 },
        { id: 3, name: 'Child 2', parent: 1 },
        { id: 4, name: 'Grandchild', parent: 2 },
        { id: 5, name: 'Root B', parent: null },
      ]
    })

    it('rootFolders returns only folders without a parent', () => {
      expect(store.rootFolders.map((f) => f.id)).toEqual([1, 5])
    })

    it('folderById finds a folder or returns null', () => {
      expect(store.folderById(4).name).toBe('Grandchild')
      expect(store.folderById(999)).toBeNull()
    })

    it('childrenOf returns direct children only', () => {
      expect(store.childrenOf(1).map((f) => f.id)).toEqual([2, 3])
      expect(store.childrenOf(4)).toEqual([])
    })

    it('ancestorsOf returns the chain from root to the folder', () => {
      expect(store.ancestorsOf(4).map((f) => f.id)).toEqual([1, 2, 4])
      expect(store.ancestorsOf(1).map((f) => f.id)).toEqual([1])
    })

    it('ancestorsOf does not loop forever on cyclic data', () => {
      store.folders = [
        { id: 10, name: 'X', parent: 11 },
        { id: 11, name: 'Y', parent: 10 },
      ]
      expect(store.ancestorsOf(10).length).toBeLessThanOrEqual(2)
    })

    it('descendantIdsOf collects all nested subfolder ids', () => {
      expect([...store.descendantIdsOf(1)].sort()).toEqual([2, 3, 4])
      expect([...store.descendantIdsOf(4)]).toEqual([])
    })
  })
})
