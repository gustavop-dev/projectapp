/**
 * Tests for documents store (panel admin).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentStore } from '../../stores/documents'

jest.mock('axios', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}))

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const axios = require('axios').default
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
    it('requests blob and triggers download', async () => {
      const prevCreate = window.URL.createObjectURL
      const prevRevoke = window.URL.revokeObjectURL
      window.URL.createObjectURL = jest.fn(() => 'blob:u')
      window.URL.revokeObjectURL = jest.fn()
      const link = { href: '', setAttribute: jest.fn(), click: jest.fn(), remove: jest.fn() }
      jest.spyOn(document, 'createElement').mockReturnValue(link)
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})
      Object.defineProperty(document, 'cookie', { value: 'csrftoken=abc', configurable: true })
      axios.get.mockResolvedValueOnce({ data: new Blob(['pdf']) })

      const result = await store.downloadPdf(3, 'My Doc')

      expect(axios.get).toHaveBeenCalledWith(
        '/api/documents/3/pdf/',
        expect.objectContaining({ responseType: 'blob' }),
      )
      expect(link.click).toHaveBeenCalled()
      expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:u')
      expect(result.success).toBe(true)
      window.URL.createObjectURL = prevCreate
      window.URL.revokeObjectURL = prevRevoke
      document.createElement.mockRestore()
      document.body.appendChild.mockRestore()
    })

    it('returns failure when axios get rejects', async () => {
      axios.get.mockRejectedValueOnce({ response: { data: { detail: 'nope' } } })
      const result = await store.downloadPdf(1, 't')
      expect(result.success).toBe(false)
      expect(result.errors).toEqual({ detail: 'nope' })
    })

    it('sends empty csrf header when cookie has no csrftoken', async () => {
      const prevCreate = window.URL.createObjectURL
      const prevRevoke = window.URL.revokeObjectURL
      window.URL.createObjectURL = jest.fn(() => 'blob:u')
      window.URL.revokeObjectURL = jest.fn()
      const link = { click: jest.fn(), setAttribute: jest.fn(), remove: jest.fn() }
      jest.spyOn(document, 'createElement').mockReturnValue(link)
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {})
      Object.defineProperty(document, 'cookie', { value: '', configurable: true })
      axios.get.mockResolvedValueOnce({ data: new Blob(['x']) })
      await store.downloadPdf(1)
      expect(axios.get).toHaveBeenCalledWith(
        '/api/documents/1/pdf/',
        expect.objectContaining({
          headers: { 'X-CSRFToken': '' },
        }),
      )
      window.URL.createObjectURL = prevCreate
      window.URL.revokeObjectURL = prevRevoke
      document.createElement.mockRestore()
      document.body.appendChild.mockRestore()
    })
  })
})
