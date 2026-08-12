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
    expect(get_request).toHaveBeenCalledWith('document-folders/?scope=all')
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

  describe('archive scope', () => {
    it('fetchFolders brings both states in one list', async () => {
      get_request.mockResolvedValueOnce({
        data: [{ id: 1, name: 'Activa' }, { id: 9, name: 'Vieja', is_archived: true }],
      })

      await store.fetchFolders()

      expect(get_request).toHaveBeenCalledWith('document-folders/?scope=all')
      expect(store.activeFolders.map((f) => f.id)).toEqual([1])
      expect(store.archivedFolders.map((f) => f.id)).toEqual([9])
    })

    it('fetchFolders passes the oldest-first order in the archived scope', async () => {
      get_request.mockResolvedValueOnce({ data: [] })

      await store.fetchFolders({ scope: 'archived', order: 'oldest' })

      expect(get_request).toHaveBeenCalledWith('document-folders/?scope=archived&order=oldest')
    })

    it('searchFolders reaches both states without touching the tree', async () => {
      store.folders = [{ id: 1, name: 'Activa' }]
      get_request.mockResolvedValueOnce({ data: [{ id: 9, name: 'temp', is_archived: true }] })

      const result = await store.searchFolders('temp')

      expect(get_request).toHaveBeenCalledWith('document-folders/?scope=all&search=temp')
      expect(result.data).toEqual([{ id: 9, name: 'temp', is_archived: true }])
      expect(store.folders).toEqual([{ id: 1, name: 'Activa' }])
    })

    it('archiveFolder patches the archive route and returns the cascade counts', async () => {
      patch_request.mockResolvedValueOnce({
        data: { folder: { id: 4 }, archived_folders: 2, archived_documents: 7 },
      })

      const result = await store.archiveFolder(4)

      expect(patch_request).toHaveBeenCalledWith('document-folders/4/archive/', {})
      expect(result.success).toBe(true)
      expect(result.archivedFolders).toBe(2)
      expect(result.archivedDocuments).toBe(7)
    })

    it('unarchiveFolder reports the ancestor chain it reopened', async () => {
      patch_request.mockResolvedValueOnce({
        data: {
          folder: { id: 4 },
          restored_folders: 1,
          restored_documents: 3,
          restored_chain: [{ id: 2, name: 'Clientes' }],
        },
      })

      const result = await store.unarchiveFolder(4)

      expect(patch_request).toHaveBeenCalledWith('document-folders/4/unarchive/', {})
      expect(result.restoredDocuments).toBe(3)
      expect(result.restoredChain).toEqual([{ id: 2, name: 'Clientes' }])
    })

    it('deleteFolder removes the row whatever its state', async () => {
      store.folders = [{ id: 4, name: 'Contratos', is_archived: true }]
      delete_request.mockResolvedValueOnce({})

      await store.deleteFolder(4)

      expect(store.folders).toEqual([])
    })
  })

  describe('hierarchy across states', () => {
    beforeEach(() => {
      store.folders = [
        { id: 1, name: 'Clientes', parent: null },
        { id: 2, name: '2026', parent: 1 },
        { id: 3, name: 'temp', parent: null, is_archived: true },
        { id: 4, name: 'Actas', parent: 3, is_archived: true },
      ]
    })

    it('rootFolders only offers the active tree', () => {
      expect(store.rootFolders.map((f) => f.id)).toEqual([1])
    })

    it('scopedRootFolders tops the archive at the folders whose parent is out of scope', () => {
      expect(store.scopedRootFolders('archived').map((f) => f.id)).toEqual([3])
    })

    it('surfaces an archived folder whose parent is active, so it stays reachable', () => {
      store.folders = [
        { id: 1, name: 'Clientes', parent: null },
        { id: 2, name: 'Vieja', parent: 1, is_archived: true },
      ]

      expect(store.scopedRootFolders('archived').map((f) => f.id)).toEqual([2])
    })

    it('childrenOf filters by scope, defaulting to active', () => {
      expect(store.childrenOf(3).map((f) => f.id)).toEqual([])
      expect(store.childrenOf(3, 'archived').map((f) => f.id)).toEqual([4])
    })

    it('ancestorsOf resolves a chain that runs through archived folders', () => {
      expect(store.ancestorsOf(4).map((f) => f.name)).toEqual(['temp', 'Actas'])
    })

    it('totalContentCount counts archived content, matching the delete 409', () => {
      const folder = {
        active_document_count: 0,
        active_children_count: 0,
        archived_document_count: 2,
        archived_children_count: 1,
      }

      expect(store.archivedContentCount(folder)).toBe(3)
      expect(store.totalContentCount(folder)).toBe(3)
    })
  })
})
