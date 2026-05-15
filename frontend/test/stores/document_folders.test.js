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

  // --- Nested-tree getters (added 2026-05-15) -----------------------------

  describe('getById getter', () => {
    it('returns folder when id matches', () => {
      store.folders = [{ id: 1, name: 'A' }, { id: 2, name: 'B' }]
      expect(store.getById(1)).toEqual({ id: 1, name: 'A' })
    })

    it('returns null when id missing', () => {
      store.folders = [{ id: 1, name: 'A' }]
      expect(store.getById(99)).toBeNull()
    })
  })

  describe('tree getter', () => {
    it('builds nested tree from flat parent FKs', () => {
      store.folders = [
        { id: 1, name: 'Root', order: 0, parent: null },
        { id: 2, name: 'Child A', order: 0, parent: 1 },
        { id: 3, name: 'Child B', order: 1, parent: 1 },
        { id: 4, name: 'Grand', order: 0, parent: 2 },
      ]
      const tree = store.tree
      expect(tree).toHaveLength(1)
      expect(tree[0].folder.name).toBe('Root')
      expect(tree[0].children).toHaveLength(2)
      expect(tree[0].children[0].folder.name).toBe('Child A')
      expect(tree[0].children[0].children[0].folder.name).toBe('Grand')
      expect(tree[0].children[1].folder.name).toBe('Child B')
    })

    it('sorts siblings by order then name', () => {
      store.folders = [
        { id: 1, name: 'B', order: 0, parent: null },
        { id: 2, name: 'A', order: 0, parent: null },
        { id: 3, name: 'C', order: 1, parent: null },
      ]
      const tree = store.tree
      expect(tree.map((n) => n.folder.name)).toEqual(['A', 'B', 'C'])
    })

    it('returns empty array when store empty', () => {
      store.folders = []
      expect(store.tree).toEqual([])
    })
  })

  describe('descendantIdsOf getter', () => {
    it('returns all descendants excluding self', () => {
      store.folders = [
        { id: 1, parent: null, name: 'r', order: 0 },
        { id: 2, parent: 1, name: 'a', order: 0 },
        { id: 3, parent: 1, name: 'b', order: 0 },
        { id: 4, parent: 2, name: 'g', order: 0 },
      ]
      expect(store.descendantIdsOf(1)).toEqual(new Set([2, 3, 4]))
    })

    it('returns empty Set for a leaf folder', () => {
      store.folders = [{ id: 1, parent: null, name: 'r', order: 0 }]
      expect(store.descendantIdsOf(1)).toEqual(new Set())
    })
  })

  describe('ancestorsOf getter', () => {
    it('returns ancestors ordered root→parent (excluding self)', () => {
      store.folders = [
        { id: 1, parent: null, name: 'R', order: 0 },
        { id: 2, parent: 1, name: 'M', order: 0 },
        { id: 3, parent: 2, name: 'L', order: 0 },
      ]
      const chain = store.ancestorsOf(3)
      expect(chain.map((f) => f.name)).toEqual(['R', 'M'])
    })

    it('returns empty array for a root folder', () => {
      store.folders = [{ id: 1, parent: null, name: 'R', order: 0 }]
      expect(store.ancestorsOf(1)).toEqual([])
    })
  })

  // --- moveFolder action (added 2026-05-15) -------------------------------

  describe('moveFolder action', () => {
    it('POSTs to move endpoint and refetches', async () => {
      create_request.mockResolvedValueOnce({ data: {} })  // move call
      get_request.mockResolvedValueOnce({ data: [{ id: 1, name: 'r', order: 0, parent: null }] })  // refetch
      const result = await store.moveFolder(5, { parent_id: 2, position: 1 })
      expect(create_request).toHaveBeenCalledWith('document-folders/5/move/', {
        parent_id: 2,
        position: 1,
      })
      expect(get_request).toHaveBeenCalledWith('document-folders/')
      expect(result.success).toBe(true)
    })

    it('omits position when null', async () => {
      create_request.mockResolvedValueOnce({ data: {} })
      get_request.mockResolvedValueOnce({ data: [] })
      await store.moveFolder(5, { parent_id: null })
      expect(create_request).toHaveBeenCalledWith('document-folders/5/move/', { parent_id: null })
    })

    it('sets error on failure', async () => {
      create_request.mockRejectedValueOnce({ response: { data: { parent_id: 'invalid' } } })
      const result = await store.moveFolder(5, { parent_id: 999 })
      expect(result.success).toBe(false)
      expect(store.error).toBe('move_folder_failed')
    })
  })

  // --- Scoped reorder (added 2026-05-15) ----------------------------------

  describe('reorderFolders scoped by parent', () => {
    it('POSTs parent_id and ids, then applies order locally', async () => {
      store.folders = [
        { id: 1, parent: 99, order: 0, name: 'a' },
        { id: 2, parent: 99, order: 1, name: 'b' },
      ]
      create_request.mockResolvedValueOnce({ data: {} })
      await store.reorderFolders({ parent_id: 99, ids: [2, 1] })
      expect(create_request).toHaveBeenCalledWith('document-folders/reorder/', {
        parent_id: 99,
        ids: [2, 1],
      })
      expect(store.folders.find((f) => f.id === 2).order).toBe(0)
      expect(store.folders.find((f) => f.id === 1).order).toBe(1)
    })

    it('does not touch folders outside the scoped ids', async () => {
      store.folders = [
        { id: 1, parent: 99, order: 0 },
        { id: 9, parent: null, order: 5 },  // unrelated
      ]
      create_request.mockResolvedValueOnce({ data: {} })
      await store.reorderFolders({ parent_id: 99, ids: [1] })
      expect(store.folders.find((f) => f.id === 9).order).toBe(5)
    })
  })

  // --- createFolder with parent (added 2026-05-15) ------------------------

  it('createFolder forwards parent in payload', async () => {
    create_request.mockResolvedValueOnce({ data: { id: 2, name: 'Child', order: 0, parent: 1 } })
    await store.createFolder({ name: 'Child', parent: 1 })
    expect(create_request).toHaveBeenCalledWith('document-folders/create/', {
      name: 'Child',
      parent: 1,
    })
  })
})
