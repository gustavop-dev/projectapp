/**
 * Tests for the platform-documents store (client document portal).
 */
import { setActivePinia, createPinia } from 'pinia'
import { usePlatformDocumentsStore } from '../../stores/platform-documents'

const mockGet = jest.fn()
const mockPost = jest.fn()

jest.mock('~/composables/usePlatformApi', () => ({
  usePlatformApi: () => ({ get: mockGet, post: mockPost }),
}))

describe('usePlatformDocumentsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformDocumentsStore()
    jest.clearAllMocks()
  })

  it('starts with empty state', () => {
    expect(store.documents).toEqual([])
    expect(store.email).toBe('')
    expect(store.emailVerified).toBe(false)
  })

  describe('getters', () => {
    it('separates the signable document from annexes', () => {
      store.documents = [
        { uuid: 'a', requires_signature: false },
        { uuid: 'b', requires_signature: true },
        { uuid: 'c', requires_signature: false },
      ]
      expect(store.signableDocument.uuid).toBe('b')
      expect(store.annexes.map((d) => d.uuid)).toEqual(['a', 'c'])
    })
  })

  describe('fetchDocuments', () => {
    it('stores documents and email state on success', async () => {
      mockGet.mockResolvedValueOnce({
        data: { email: 'c@t.com', email_verified: true, documents: [{ uuid: 'x' }] },
      })
      const result = await store.fetchDocuments()
      expect(result.success).toBe(true)
      expect(store.documents).toEqual([{ uuid: 'x' }])
      expect(store.email).toBe('c@t.com')
      expect(store.emailVerified).toBe(true)
    })

    it('returns error on failure', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'nope' } } })
      const result = await store.fetchDocuments()
      expect(result.success).toBe(false)
      expect(store.error).toBe('nope')
    })
  })

  describe('downloadPdf', () => {
    let anchor
    let clickSpy
    let createElSpy

    beforeEach(() => {
      window.URL.createObjectURL = jest.fn(() => 'blob:mock')
      window.URL.revokeObjectURL = jest.fn()
      anchor = document.createElement('a')
      clickSpy = jest.spyOn(anchor, 'click').mockImplementation(() => {})
      createElSpy = jest.spyOn(document, 'createElement').mockReturnValue(anchor)
    })

    afterEach(() => {
      createElSpy.mockRestore()
    })

    it('requests the pdf as a blob and triggers a named download', async () => {
      mockGet.mockResolvedValueOnce({ data: new Blob(['%PDF']) })
      const result = await store.downloadPdf('u-1', 'Mi Contrato')
      expect(mockGet).toHaveBeenCalledWith('documents/u-1/pdf/', { responseType: 'blob' })
      expect(anchor.getAttribute('download')).toBe('Mi-Contrato.pdf')
      expect(clickSpy).toHaveBeenCalled()
      expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock')
      expect(result.success).toBe(true)
    })

    it('returns error when the download fails', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'No autorizado' } } })
      const result = await store.downloadPdf('u-1')
      expect(result.success).toBe(false)
      expect(result.message).toBe('No autorizado')
    })
  })

  describe('email verification', () => {
    it('requests a code', async () => {
      mockPost.mockResolvedValueOnce({ data: { detail: 'ok' } })
      const result = await store.requestEmailVerification()
      expect(mockPost).toHaveBeenCalledWith('email/verify/request/')
      expect(result.success).toBe(true)
    })

    it('marks verified on confirm success', async () => {
      mockPost.mockResolvedValueOnce({ data: { email_verified: true } })
      const result = await store.confirmEmailVerification('123456')
      expect(mockPost).toHaveBeenCalledWith('email/verify/confirm/', { code: '123456' })
      expect(result.success).toBe(true)
      expect(store.emailVerified).toBe(true)
    })

    it('surfaces bad-code error and stays unverified', async () => {
      mockPost.mockRejectedValueOnce({ response: { data: { detail: 'Código inválido.' } } })
      const result = await store.confirmEmailVerification('000000')
      expect(result.success).toBe(false)
      expect(store.emailVerified).toBe(false)
    })
  })

  describe('signDocument', () => {
    it('replaces the signed document in the list', async () => {
      store.documents = [{ uuid: 'b', requires_signature: true, signed: false }]
      mockPost.mockResolvedValueOnce({
        data: { uuid: 'b', requires_signature: true, signed: true, signed_at: '2026-07-03' },
      })
      const result = await store.signDocument('b')
      expect(mockPost).toHaveBeenCalledWith('documents/b/sign/', { accept: true, signature_name: '' })
      expect(result.success).toBe(true)
      expect(store.documents[0].signed).toBe(true)
    })

    it('returns error on failure', async () => {
      mockPost.mockRejectedValueOnce({ response: { data: { detail: 'blocked' } } })
      const result = await store.signDocument('b')
      expect(result.success).toBe(false)
      expect(store.error).toBe('blocked')
    })
  })
})
