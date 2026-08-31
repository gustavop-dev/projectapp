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

  describe('change client cascade', () => {
    it('previewChangeClient asks the backend for the impact', async () => {
      get_request.mockResolvedValue({ data: { totals: { documents: 3 } } })

      const result = await store.previewChangeClient(5, 9)

      expect(get_request).toHaveBeenCalledWith(
        'document-folders/5/change-client/preview/?client_profile_id=9',
      )
      expect(result.success).toBe(true)
      expect(result.data.totals.documents).toBe(3)
    })

    it('previewChangeClient reports a failure instead of throwing', async () => {
      get_request.mockRejectedValue({ response: { data: { error: 'nope' } } })

      const result = await store.previewChangeClient(5, 9)

      expect(result.success).toBe(false)
    })

    it('changeClient posts the confirmed plan and refreshes the folder', async () => {
      store.folders = [{ id: 5, name: 'Kore', client: 1 }]
      create_request.mockResolvedValue({
        data: { folder: { id: 5, name: 'Kore', client: 9 }, moved: { documents: 2 } },
      })

      const payload = {
        client_profile_id: 9, mode: 'propagate', document_ids: [1, 2], folder_ids: [],
      }
      const result = await store.changeClient(5, payload)

      expect(create_request).toHaveBeenCalledWith(
        'document-folders/5/change-client/', payload,
      )
      expect(result.success).toBe(true)
      // La fila vuelve con el cliente nuevo: el panel lateral no puede seguir
      // mostrando al anterior.
      expect(store.folders[0].client).toBe(9)
    })

    it('changeClient surfaces a stale-plan conflict', async () => {
      create_request.mockRejectedValue({
        response: { status: 409, data: { code: 'records_changed' } },
      })

      const result = await store.changeClient(5, { mode: 'propagate' })

      expect(result.success).toBe(false)
      expect(result.code).toBe('records_changed')
    })
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

    it('archiveFolder failure returns a normalized message for the toast', async () => {
      patch_request.mockRejectedValueOnce({
        response: { status: 500, data: { detail: 'boom' } },
      })

      const result = await store.archiveFolder(4)

      expect(result.success).toBe(false)
      expect(result.message).toBe('boom')
      expect(result.errors).toEqual({ detail: 'boom' })
    })

    it('unarchiveFolder failure falls back to a Spanish message', async () => {
      patch_request.mockRejectedValueOnce(new Error('network'))

      const result = await store.unarchiveFolder(4)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No se pudo restaurar la carpeta.')
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

    describe('archived mode lists only what holds archived content', () => {
      // El árbol que reportó el operador: parado en un proyecto sin nada
      // archivado veía TODAS sus carpetas, con su inventario activo.
      beforeEach(() => {
        store.folders = [
          { id: 10, name: 'Mimittos', parent: null, active_children_count: 1 },
          { id: 11, name: 'Cuentas', parent: 10, active_document_count: 1 },
          { id: 20, name: 'Vastago', parent: null, active_children_count: 1 },
          { id: 21, name: 'Feedback', parent: 20, active_document_count: 4, archived_document_count: 1 },
        ]
      })

      it('drops a project whose subtree has nothing archived', () => {
        expect(store.belongsToScope(store.folderById(10), 'archived')).toBe(false)
        expect(store.belongsToScope(store.folderById(11), 'archived')).toBe(false)
        expect(store.scopedRootFolders('archived').map((f) => f.id)).toEqual([20])
      })

      it('keeps an active folder that still holds archived documents', () => {
        expect(store.belongsToScope(store.folderById(21), 'archived')).toBe(true)
        expect(store.childrenOf(20, 'archived').map((f) => f.id)).toEqual([21])
        expect(store.childrenOf(10, 'archived')).toEqual([])
      })

      it('leaves the active and mixed scopes untouched', () => {
        expect(store.scopedRootFolders('active').map((f) => f.id)).toEqual([10, 20])
        expect(store.childrenOf(10, 'active').map((f) => f.id)).toEqual([11])
        expect(store.childrenOf(10, 'all').map((f) => f.id)).toEqual([11])
      })
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

  describe('subtree counters', () => {
    /** Carpeta con los seis contadores absolutos, como los sirve el backend. */
    const folder = (id, parent, {
      docs = 0, subs = 0, archivedDocs = 0, archivedSubs = 0, archived = false,
    } = {}) => ({
      id,
      parent,
      name: `F${id}`,
      is_archived: archived,
      document_count: archived ? archivedDocs : docs,
      children_count: archived ? archivedSubs : subs,
      active_document_count: docs,
      active_children_count: subs,
      archived_document_count: archivedDocs,
      archived_children_count: archivedSubs,
    })

    it('reports what a folder holds in its subfolders, not just its own', () => {
      // «Familia» en producción: cero documentos propios, 12 dos niveles abajo.
      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { docs: 1, subs: 2 }),
        folder(3, 2, { docs: 6 }),
        folder(4, 2, { docs: 5 }),
      ]

      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(12)
      expect(store.folderById(1).document_count).toBe(0)
    })

    it('carries the whole chain, four levels down', () => {
      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { subs: 1 }),
        folder(3, 2, { subs: 1 }),
        folder(4, 3, { docs: 9 }),
      ]

      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(9)
    })

    it('does not let sibling branches bleed into each other', () => {
      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { docs: 7 }),
        folder(8, null, { subs: 1 }),
        folder(9, 8, { docs: 3 }),
      ]

      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(7)
      expect(store.recursiveDocumentCount(store.folderById(8))).toBe(3)
    })

    it('counts a branch promoted to the top exactly once', () => {
      // A(activa) → B(archivada) → C(activa). El panel lista a C en la cima
      // porque su contenedor está fuera del scope; si A también la contara, la
      // suma de las filas pasaría del total de «Todos».
      store.folders = [
        folder(1, null, { docs: 2 }),
        folder(2, 1, { archived: true }),
        folder(3, 2, { docs: 5 }),
      ]

      const roots = store.scopedRootFolders('active')
      expect(roots.map((f) => f.id)).toEqual([1, 3])
      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(2)
      expect(store.recursiveDocumentCount(store.folderById(3))).toBe(5)
      expect(roots.reduce((n, f) => n + store.recursiveDocumentCount(f), 0)).toBe(7)
    })

    it('reaches archived content held inside an active folder', () => {
      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { archivedDocs: 4, archived: true }),
      ]

      expect(store.recursiveDocumentCount(store.folderById(1), 'archived')).toBe(4)
    })

    it('gives the same tree a different answer per mode', () => {
      store.folders = [
        folder(1, null, { docs: 1, subs: 1 }),
        folder(2, 1, { docs: 3, archivedDocs: 4 }),
      ]
      const root = () => store.folderById(1)

      expect(store.recursiveDocumentCount(root(), 'active')).toBe(4)
      expect(store.recursiveDocumentCount(root(), 'archived')).toBe(4)
      expect(store.recursiveDocumentCount(root(), 'all')).toBe(8)
    })

    it('follows the whole ancestor chain when the tree is refetched', () => {
      // Requisito de sincronización: mover un documento dos niveles arriba
      // cambia DOS contadores, no sólo el de la carpeta tocada.
      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { subs: 1 }),
        folder(3, 2, { docs: 4 }),
      ]
      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(4)

      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { subs: 1 }),
        folder(3, 2, { docs: 1 }),
      ]

      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(1)
      expect(store.recursiveDocumentCount(store.folderById(2))).toBe(1)
    })

    it('falls back to the direct count for a folder outside the loaded tree', () => {
      // Los resultados de `searchFolders` no viven en `folders` a propósito.
      store.folders = []

      expect(store.recursiveDocumentCount(folder(99, null, { docs: 3 }))).toBe(3)
    })

    it('rolls up a legacy payload without the absolute counters', () => {
      store.folders = [
        { id: 1, parent: null, document_count: 1, children_count: 1, is_archived: false },
        { id: 2, parent: 1, document_count: 6, children_count: 0, is_archived: false },
      ]

      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(7)
    })

    it('finishes on a cyclic parent chain instead of hanging the panel', () => {
      store.folders = [folder(1, 2, { docs: 2 }), folder(2, 1, { docs: 3 })]

      expect(Number.isFinite(store.recursiveDocumentCount(store.folderById(1)))).toBe(true)
    })

    it('cascadeContentOf names everything archiving would drag, at any depth', () => {
      // El aviso decía «1 documento» antes de arrastrar todo el subárbol.
      store.folders = [
        folder(1, null, { docs: 1, subs: 1 }),
        folder(2, 1, { docs: 6, archivedDocs: 2 }),
      ]

      expect(store.cascadeContentOf(store.folderById(1))).toMatchObject({ docs: 7, subs: 1 })
    })

    it('leaves the delete guard on the direct count, matching the 409', () => {
      // Un contador recursivo acá haría que el tooltip contradijera al servidor.
      store.folders = [
        folder(1, null, { subs: 1 }),
        folder(2, 1, { docs: 12 }),
      ]

      expect(store.recursiveDocumentCount(store.folderById(1))).toBe(12)
      expect(store.totalContentCount(store.folderById(1))).toBe(1)
    })
  })
})
