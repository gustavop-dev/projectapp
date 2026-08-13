/**
 * Tests for documents store (panel admin).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentStore } from '../../stores/documents'

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

describe('useDocumentStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useDocumentStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty documents', () => {
      expect(store.documents).toEqual([])
      expect(store.currentDocument).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.isUpdating).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('getDocumentById', () => {
    it('returns document matching id', () => {
      store.documents = [{ id: 1, title: 'A' }, { id: 2, title: 'B' }]
      expect(store.getDocumentById(2)).toEqual({ id: 2, title: 'B' })
    })
  })

  describe('fetchDocuments', () => {
    it('stores list on success', async () => {
      get_request.mockResolvedValueOnce({ data: [{ id: 1 }] })
      const result = await store.fetchDocuments()
      expect(result.success).toBe(true)
      expect(store.documents).toEqual([{ id: 1 }])
      expect(store.isLoading).toBe(false)
    })

    it('returns errors payload on failure', async () => {
      get_request.mockRejectedValueOnce({ response: { data: { detail: 'x' } } })
      const result = await store.fetchDocuments()
      expect(result.success).toBe(false)
      expect(store.error).toBe('fetch_failed')
      expect(result.errors).toEqual({ detail: 'x' })
    })

    it('normalizes failure into message/code/status', async () => {
      get_request.mockRejectedValueOnce({
        response: { status: 500, data: { detail: 'boom' } },
      })
      const result = await store.fetchDocuments()
      expect(result.message).toBe('boom')
      expect(result.status).toBe(500)
    })

    it('falls back to a spanish message when the error has no payload', async () => {
      get_request.mockRejectedValueOnce(new Error('network'))
      const result = await store.fetchDocuments()
      expect(result.success).toBe(false)
      expect(result.message).toBe('No se pudieron cargar los documentos.')
    })

    it('calls documents/ with no query params when no filters active', async () => {
      get_request.mockResolvedValueOnce({ data: [] })
      await store.fetchDocuments()
      expect(get_request).toHaveBeenCalledWith('documents/?scope=active')
    })

    it('sends folder query param when activeFolderId is a numeric id', async () => {
      store.activeFolderId = 7
      get_request.mockResolvedValueOnce({ data: [] })
      await store.fetchDocuments()
      expect(get_request).toHaveBeenCalledWith('documents/?folder=7&scope=active')
    })

    it('sends folder=none when activeFolderId is "none"', async () => {
      store.activeFolderId = 'none'
      get_request.mockResolvedValueOnce({ data: [] })
      await store.fetchDocuments()
      expect(get_request).toHaveBeenCalledWith('documents/?folder=none&scope=active')
    })

    it('sends tags query param when activeTagIds has values', async () => {
      store.activeTagIds = [3, 5]
      get_request.mockResolvedValueOnce({ data: [] })
      await store.fetchDocuments()
      expect(get_request).toHaveBeenCalledWith('documents/?scope=active&tags=3%2C5')
    })

    it('accepts override params without mutating store filters', async () => {
      store.activeFolderId = 'all'
      store.activeTagIds = []
      get_request.mockResolvedValueOnce({ data: [] })
      await store.fetchDocuments({ folder: 2, tags: [9] })
      expect(get_request).toHaveBeenCalledWith('documents/?folder=2&scope=active&tags=9')
      expect(store.activeFolderId).toBe('all')
      expect(store.activeTagIds).toEqual([])
    })
  })

  describe('setFilters', () => {
    it('updates folder and triggers refetch', async () => {
      get_request.mockResolvedValueOnce({ data: [] })
      await store.setFilters({ folder: 4 })
      expect(store.activeFolderId).toBe(4)
      expect(get_request).toHaveBeenCalledWith('documents/?folder=4&scope=active')
    })

    it('updates tags array by cloning input', async () => {
      get_request.mockResolvedValueOnce({ data: [] })
      const inputTags = [1, 2]
      await store.setFilters({ tags: inputTags })
      expect(store.activeTagIds).toEqual([1, 2])
      expect(store.activeTagIds).not.toBe(inputTags)
    })

    it('supports clearing tags with empty array', async () => {
      store.activeTagIds = [1]
      get_request.mockResolvedValueOnce({ data: [] })
      await store.setFilters({ tags: [] })
      expect(store.activeTagIds).toEqual([])
      expect(get_request).toHaveBeenCalledWith('documents/?scope=active')
    })
  })

  describe('toggleTagFilter', () => {
    it('adds a tag id when absent and refetches', async () => {
      get_request.mockResolvedValueOnce({ data: [] })
      await store.toggleTagFilter(8)
      expect(store.activeTagIds).toEqual([8])
      expect(get_request).toHaveBeenCalledWith('documents/?scope=active&tags=8')
    })

    it('removes a tag id when already present', async () => {
      store.activeTagIds = [1, 2, 3]
      get_request.mockResolvedValueOnce({ data: [] })
      await store.toggleTagFilter(2)
      expect(store.activeTagIds).toEqual([1, 3])
      expect(get_request).toHaveBeenCalledWith('documents/?scope=active&tags=1%2C3')
    })

    it('keeps the archived scope when toggling a tag', async () => {
      // Togglear una etiqueta dentro de Archivados no debe devolver al usuario
      // a la vista de activos: el scope viaja explícito en el refetch.
      store.archiveScope = 'archived'
      get_request.mockResolvedValueOnce({ data: [] })
      await store.toggleTagFilter(8)
      expect(store.activeTagIds).toEqual([8])
      expect(get_request).toHaveBeenCalledWith('documents/?scope=archived&tags=8')
    })
  })

  describe('fetchDocument', () => {
    it('sets currentDocument on success', async () => {
      get_request.mockResolvedValueOnce({ data: { id: 5, title: 'Doc' } })
      const result = await store.fetchDocument(5)
      expect(result.success).toBe(true)
      expect(store.currentDocument).toEqual({ id: 5, title: 'Doc' })
    })

    it('returns failure when detail fetch errors', async () => {
      get_request.mockRejectedValueOnce({ response: { data: {} } })
      const result = await store.fetchDocument(1)
      expect(result.success).toBe(false)
      expect(store.error).toBe('fetch_detail_failed')
    })
  })

  describe('createFromMarkdown', () => {
    it('sets currentDocument from response', async () => {
      const payload = { title: 'T', content_markdown: '# Hi' }
      create_request.mockResolvedValueOnce({ data: { id: 9 } })
      const result = await store.createFromMarkdown(payload)
      expect(create_request).toHaveBeenCalledWith('documents/create-from-markdown/', payload)
      expect(result.success).toBe(true)
      expect(store.currentDocument).toEqual({ id: 9 })
    })

    it('returns errors when create fails', async () => {
      create_request.mockRejectedValueOnce({ response: { data: { err: 1 } } })
      const result = await store.createFromMarkdown({})
      expect(result.success).toBe(false)
      expect(store.error).toBe('create_from_markdown_failed')
    })
  })

  describe('updateDocument', () => {
    it('patches document and updates current', async () => {
      patch_request.mockResolvedValueOnce({ data: { id: 2, title: 'Up' } })
      const result = await store.updateDocument(2, { title: 'Up' })
      expect(patch_request).toHaveBeenCalledWith('documents/2/update/', { title: 'Up' })
      expect(result.success).toBe(true)
      expect(store.currentDocument).toEqual({ id: 2, title: 'Up' })
    })

    it('returns errors when patch fails', async () => {
      patch_request.mockRejectedValueOnce({ response: { data: { a: 1 } } })
      const result = await store.updateDocument(1, {})
      expect(result.success).toBe(false)
      expect(store.error).toBe('update_failed')
    })
  })

  describe('deleteDocument', () => {
    it('removes id from list and clears current when same id', async () => {
      store.documents = [{ id: 1 }, { id: 2 }]
      store.currentDocument = { id: 1 }
      delete_request.mockResolvedValueOnce({})
      const result = await store.deleteDocument(1)
      expect(result.success).toBe(true)
      expect(store.documents).toEqual([{ id: 2 }])
      expect(store.currentDocument).toBeNull()
    })

    it('keeps currentDocument when deleting other id', async () => {
      store.currentDocument = { id: 2 }
      store.documents = [{ id: 1 }, { id: 2 }]
      delete_request.mockResolvedValueOnce({})
      await store.deleteDocument(1)
      expect(store.currentDocument).toEqual({ id: 2 })
    })

    it('returns failure when delete errors', async () => {
      delete_request.mockRejectedValueOnce({ response: { data: { d: 1 } } })
      const result = await store.deleteDocument(9)
      expect(result.success).toBe(false)
      expect(store.error).toBe('delete_failed')
    })
  })

  describe('duplicateDocument', () => {
    it('prepends duplicated document', async () => {
      store.documents = [{ id: 1 }]
      create_request.mockResolvedValueOnce({ data: { id: 2, copy: true } })
      const result = await store.duplicateDocument(1)
      expect(create_request).toHaveBeenCalledWith('documents/1/duplicate/', {})
      expect(result.success).toBe(true)
      expect(store.documents[0]).toEqual({ id: 2, copy: true })
    })

    it('returns errors when duplicate fails', async () => {
      create_request.mockRejectedValueOnce({ response: { data: {} } })
      const result = await store.duplicateDocument(1)
      expect(result.success).toBe(false)
      expect(store.error).toBe('duplicate_failed')
    })
  })

  describe('downloadPdf', () => {
    beforeEach(() => {
      global.URL.createObjectURL = jest.fn(() => 'blob:x')
      global.URL.revokeObjectURL = jest.fn()
    })

    it('requests the pdf blob and triggers a download', async () => {
      get_request.mockResolvedValue({ data: new Blob(['x']) })
      const clickSpy = jest.fn()
      jest.spyOn(document, 'createElement').mockReturnValue({
        href: '', setAttribute: jest.fn(), click: clickSpy, remove: jest.fn(),
      })
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})

      const result = await store.downloadPdf(3, 'My Doc')
      expect(get_request).toHaveBeenCalledWith(
        'documents/3/pdf/', { responseType: 'blob' })
      expect(clickSpy).toHaveBeenCalled()
      expect(result.success).toBe(true)
    })

    it('appends the template query when given a valid style', async () => {
      get_request.mockResolvedValue({ data: new Blob(['x']) })
      jest.spyOn(document, 'createElement').mockReturnValue({
        href: '', setAttribute: jest.fn(), click: jest.fn(), remove: jest.fn(),
      })
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})

      await store.downloadPdf(1, 't', 'friendly')
      expect(get_request).toHaveBeenCalledWith(
        'documents/1/pdf/?template=friendly', { responseType: 'blob' })
    })

    it('ignores an unknown template value', async () => {
      get_request.mockResolvedValue({ data: new Blob(['x']) })
      jest.spyOn(document, 'createElement').mockReturnValue({
        href: '', setAttribute: jest.fn(), click: jest.fn(), remove: jest.fn(),
      })
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})

      await store.downloadPdf(1, 't', 'bogus')
      expect(get_request).toHaveBeenCalledWith(
        'documents/1/pdf/', { responseType: 'blob' })
    })

    it('returns an error result on failure', async () => {
      get_request.mockRejectedValue(new Error('boom'))
      const result = await store.downloadPdf(1)
      expect(result.success).toBe(false)
    })
  })

  describe('archive scope', () => {
    it('requests the archived scope when asked for it', async () => {
      get_request.mockResolvedValueOnce({ data: [{ id: 9, title: 'Viejo' }] })

      const result = await store.fetchDocuments({ scope: 'archived' })

      expect(get_request).toHaveBeenCalledWith('documents/?scope=archived')
      expect(result.success).toBe(true)
      expect(store.documents).toEqual([{ id: 9, title: 'Viejo' }])
    })

    it('asks for the oldest first when the archived order says so', async () => {
      store.archivedOrder = 'oldest'
      get_request.mockResolvedValueOnce({ data: [] })

      await store.fetchDocuments({ scope: 'archived' })

      expect(get_request).toHaveBeenCalledWith('documents/?scope=archived&order=oldest')
    })

    it('ignores the archived order outside the archived scope', async () => {
      store.archivedOrder = 'oldest'
      get_request.mockResolvedValueOnce({ data: [] })

      await store.fetchDocuments({ scope: 'all' })

      expect(get_request).toHaveBeenCalledWith('documents/?scope=all')
    })

    it('composes the archived scope with the active tag filter', async () => {
      store.activeTagIds = [2, 5]
      get_request.mockResolvedValueOnce({ data: [] })

      await store.fetchDocuments({ scope: 'archived' })

      expect(get_request).toHaveBeenCalledWith('documents/?scope=archived&tags=2%2C5')
    })

    it('never inherits the scope from the store', async () => {
      // create.vue, edit.vue y las pestañas de diagnóstico llaman sin scope y
      // jamás deben heredar el archivado que el gestor haya dejado puesto.
      store.archiveScope = 'archived'
      get_request.mockResolvedValueOnce({ data: [] })

      await store.fetchDocuments()

      expect(get_request).toHaveBeenCalledWith('documents/?scope=active')
    })

    it('omits the folder param at the hierarchical root', async () => {
      store.activeFolderId = 'root'
      get_request.mockResolvedValueOnce({ data: [] })

      await store.fetchDocuments({ scope: 'archived' })

      expect(get_request).toHaveBeenCalledWith('documents/?scope=archived')
    })

    it('discards a stale list response', async () => {
      let resolveFirst
      get_request.mockReturnValueOnce(new Promise((r) => { resolveFirst = r }))
      get_request.mockResolvedValueOnce({ data: [{ id: 2, title: 'Nuevo' }] })

      const first = store.fetchDocuments({ scope: 'active' })
      await store.fetchDocuments({ scope: 'active' })
      resolveFirst({ data: [{ id: 1, title: 'Viejo' }] })
      await first

      expect(store.documents).toEqual([{ id: 2, title: 'Nuevo' }])
    })

    it('archiveDocument drops the row while the active scope is showing', async () => {
      store.documents = [{ id: 7, title: 'Viejo' }, { id: 8, title: 'Otro' }]
      patch_request.mockResolvedValueOnce({ data: { id: 7, is_archived: true } })

      const result = await store.archiveDocument(7)

      expect(patch_request).toHaveBeenCalledWith('documents/7/archive/', {})
      expect(result.success).toBe(true)
      expect(store.documents.map((d) => d.id)).toEqual([8])
    })

    it('archiveDocument keeps the row under the mixed scope, flipping its badge', async () => {
      store.archiveScope = 'all'
      store.documents = [{ id: 7, title: 'Viejo', is_archived: false }]
      patch_request.mockResolvedValueOnce({ data: { id: 7, title: 'Viejo', is_archived: true } })

      await store.archiveDocument(7)

      expect(store.documents).toEqual([{ id: 7, title: 'Viejo', is_archived: true }])
    })

    it('unarchiveDocument reports the container chain that came back', async () => {
      store.archiveScope = 'archived'
      store.documents = [{ id: 7, title: 'Viejo' }]
      patch_request.mockResolvedValueOnce({
        data: { id: 7, is_archived: false, restored_chain: [{ id: 4, name: 'temp' }] },
      })

      const result = await store.unarchiveDocument(7)

      expect(patch_request).toHaveBeenCalledWith('documents/7/unarchive/', {})
      expect(result.restoredChain).toEqual([{ id: 4, name: 'temp' }])
      expect(store.documents).toEqual([])
    })

    it('normalizes an archive failure into a Spanish message', async () => {
      store.documents = [{ id: 7 }]
      patch_request.mockRejectedValueOnce(new Error('boom'))

      const result = await store.archiveDocument(7)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No se pudo archivar el documento.')
      expect(store.documents).toHaveLength(1)
    })

    it('deleteDocument also removes the row from the search results', async () => {
      store.searchResults = [{ id: 7, title: 'Viejo' }]
      delete_request.mockResolvedValueOnce({})

      await store.deleteDocument(7)

      expect(store.searchResults).toEqual([])
    })
  })

  describe('global search', () => {
    it('ignores folder and scope so nothing stays hidden', async () => {
      store.activeFolderId = 7
      store.archiveScope = 'active'
      get_request.mockResolvedValueOnce({ data: [{ id: 9, is_archived: true }] })

      const result = await store.searchDocuments('mapeo')

      expect(get_request).toHaveBeenCalledWith('documents/?scope=all&search=mapeo')
      expect(result.success).toBe(true)
      expect(store.searchResults).toEqual([{ id: 9, is_archived: true }])
    })

    it('discards a stale search response', async () => {
      let resolveFirst
      get_request.mockReturnValueOnce(new Promise((r) => { resolveFirst = r }))
      get_request.mockResolvedValueOnce({ data: [{ id: 2 }] })

      const first = store.searchDocuments('ma')
      await store.searchDocuments('mapeo')
      resolveFirst({ data: [{ id: 1 }] })
      await first

      expect(store.searchResults).toEqual([{ id: 2 }])
    })
  })

  describe('panel counts', () => {
    it('fetches the authoritative sidebar totals', async () => {
      get_request.mockResolvedValueOnce({
        data: { documents: { active: 89, archived: 1 }, folders: { active: 25, archived: 1 } },
      })

      await store.fetchCounts()

      expect(get_request).toHaveBeenCalledWith('documents/counts/')
      expect(store.counts.documents.active).toBe(89)
      expect(store.counts.folders.archived).toBe(1)
    })

    it('merges a partial payload instead of blanking the sidebar', async () => {
      store.counts.documents.active = 89
      get_request.mockResolvedValueOnce({ data: { documents: { archived: 3 } } })

      await store.fetchCounts()

      expect(store.counts.documents.active).toBe(89)
      expect(store.counts.documents.archived).toBe(3)
    })
  })
})
