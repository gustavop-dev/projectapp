/**
 * Tests for diagnostics store (Web App Diagnostics admin module).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useDiagnosticsStore } from '../../stores/diagnostics'

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

const mockDiagnostic = (overrides = {}) => ({
  id: 1,
  uuid: 'aaaa-bbbb-cccc',
  title: 'Diagnóstico — Acme',
  status: 'draft',
  client_name: 'Acme Corp',
  documents: [],
  ...overrides,
})

const mockDoc = (overrides = {}) => ({
  id: 10,
  doc_type: 'initial_proposal',
  order: 1,
  content_md: '# Test',
  is_ready: false,
  ...overrides,
})

describe('useDiagnosticsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useDiagnosticsStore()
    jest.clearAllMocks()
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  // ── Initial state ────────────────────────────────────────────────────────

  it('starts with empty diagnostics array', () => {
    expect(store.diagnostics).toEqual([])
  })

  it('starts with null current', () => {
    expect(store.current).toBeNull()
  })

  it('starts with isLoading false', () => {
    expect(store.isLoading).toBe(false)
  })

  it('starts with isUpdating false', () => {
    expect(store.isUpdating).toBe(false)
  })

  it('starts with null error', () => {
    expect(store.error).toBeNull()
  })

  // ── Getters ──────────────────────────────────────────────────────────────

  it('getById finds a diagnostic by numeric id', () => {
    store.diagnostics = [mockDiagnostic({ id: 1 }), mockDiagnostic({ id: 2 })]
    expect(store.getById(1).id).toBe(1)
    expect(store.getById(2).id).toBe(2)
  })

  it('getById coerces string ids to numbers', () => {
    store.diagnostics = [mockDiagnostic({ id: 5 })]
    expect(store.getById('5').id).toBe(5)
  })

  it('getById returns undefined for a missing id', () => {
    store.diagnostics = [mockDiagnostic({ id: 1 })]
    expect(store.getById(99)).toBeUndefined()
  })

  it('visibleDocuments sorts documents by order ascending', () => {
    store.current = mockDiagnostic({
      documents: [
        mockDoc({ id: 3, order: 3 }),
        mockDoc({ id: 1, order: 1 }),
        mockDoc({ id: 2, order: 2 }),
      ],
    })
    const sorted = store.visibleDocuments
    expect(sorted.map((d) => d.order)).toEqual([1, 2, 3])
  })

  it('visibleDocuments returns empty array when current is null', () => {
    store.current = null
    expect(store.visibleDocuments).toEqual([])
  })

  it('visibleDocuments returns empty array when current has no documents', () => {
    store.current = mockDiagnostic({ documents: [] })
    expect(store.visibleDocuments).toEqual([])
  })

  // ── fetchAll ─────────────────────────────────────────────────────────────

  it('fetchAll calls GET diagnostics/ and populates diagnostics array', async () => {
    const list = [mockDiagnostic({ id: 1 }), mockDiagnostic({ id: 2 })]
    get_request.mockResolvedValueOnce({ data: list })
    const result = await store.fetchAll()
    expect(get_request).toHaveBeenCalledWith('diagnostics/')
    expect(store.diagnostics).toEqual(list)
    expect(result.success).toBe(true)
    expect(result.data).toEqual(list)
  })

  it('fetchAll appends status filter as query string', async () => {
    get_request.mockResolvedValueOnce({ data: [] })
    await store.fetchAll({ status: 'draft' })
    expect(get_request).toHaveBeenCalledWith('diagnostics/?status=draft')
  })

  it('fetchAll omits empty string and undefined params from query string', async () => {
    get_request.mockResolvedValueOnce({ data: [] })
    await store.fetchAll({ status: '', client: undefined })
    expect(get_request).toHaveBeenCalledWith('diagnostics/')
  })

  it('fetchAll sets error on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: { error: 'server_error' } } })
    const result = await store.fetchAll()
    expect(result.success).toBe(false)
    expect(store.error).toBe('server_error')
  })

  it('fetchAll defaults to fetch_failed when no error key in response', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    await store.fetchAll()
    expect(store.error).toBe('fetch_failed')
  })

  it('fetchAll clears isLoading in finally', async () => {
    get_request.mockResolvedValueOnce({ data: [] })
    await store.fetchAll()
    expect(store.isLoading).toBe(false)
  })

  // ── fetchDetail ──────────────────────────────────────────────────────────

  it('fetchDetail sets current and calls the detail endpoint', async () => {
    const d = mockDiagnostic({ id: 7 })
    get_request.mockResolvedValueOnce({ data: d })
    const result = await store.fetchDetail(7)
    expect(get_request).toHaveBeenCalledWith('diagnostics/7/detail/')
    expect(store.current).toEqual(d)
    expect(result.success).toBe(true)
  })

  it('fetchDetail sets error on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: { error: 'not_found' } } })
    const result = await store.fetchDetail(99)
    expect(result.success).toBe(false)
    expect(store.error).toBe('not_found')
  })

  it('fetchDetail clears isLoading in finally', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    await store.fetchDetail(1)
    expect(store.isLoading).toBe(false)
  })

  // ── create ───────────────────────────────────────────────────────────────

  it('create POSTs to diagnostics/create/ with payload', async () => {
    const d = mockDiagnostic()
    create_request.mockResolvedValueOnce({ data: d })
    const result = await store.create({ client_id: 1, language: 'es' })
    expect(create_request).toHaveBeenCalledWith('diagnostics/create/', { client_id: 1, language: 'es' })
    expect(store.current).toEqual(d)
    expect(result.success).toBe(true)
    expect(result.data).toEqual(d)
  })

  it('create clears isUpdating in finally', async () => {
    create_request.mockResolvedValueOnce({ data: mockDiagnostic() })
    await store.create({})
    expect(store.isUpdating).toBe(false)
  })

  it('create sets error on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { error: 'client_id_required' } } })
    const result = await store.create({})
    expect(result.success).toBe(false)
    expect(store.error).toBe('client_id_required')
  })

  // ── update ───────────────────────────────────────────────────────────────

  it('update PATCHes to diagnostics/{id}/update/ and updates current', async () => {
    const updated = mockDiagnostic({ duration_label: '2 semanas' })
    patch_request.mockResolvedValueOnce({ data: updated })
    const result = await store.update(1, { duration_label: '2 semanas' })
    expect(patch_request).toHaveBeenCalledWith('diagnostics/1/update/', { duration_label: '2 semanas' })
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  it('update sets error on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.update(1, {})
    expect(result.success).toBe(false)
    expect(store.error).toBe('update_failed')
  })

  // ── remove ───────────────────────────────────────────────────────────────

  it('remove DELETEs the diagnostic and filters it from the array', async () => {
    store.diagnostics = [mockDiagnostic({ id: 1 }), mockDiagnostic({ id: 2 })]
    delete_request.mockResolvedValueOnce({})
    await store.remove(1)
    expect(delete_request).toHaveBeenCalledWith('diagnostics/1/delete/')
    expect(store.diagnostics.map((d) => d.id)).toEqual([2])
  })

  it('remove nulls current when the deleted item was current', async () => {
    store.current = mockDiagnostic({ id: 3 })
    store.diagnostics = [mockDiagnostic({ id: 3 })]
    delete_request.mockResolvedValueOnce({})
    await store.remove(3)
    expect(store.current).toBeNull()
  })

  it('remove does not null current for a different id', async () => {
    store.current = mockDiagnostic({ id: 5 })
    store.diagnostics = [mockDiagnostic({ id: 5 }), mockDiagnostic({ id: 6 })]
    delete_request.mockResolvedValueOnce({})
    await store.remove(6)
    expect(store.current).not.toBeNull()
  })

  it('remove sets error on failure', async () => {
    delete_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.remove(99)
    expect(result.success).toBe(false)
    expect(store.error).toBe('delete_failed')
  })

  // ── updateDocument ───────────────────────────────────────────────────────

  it('updateDocument PATCHes the nested document endpoint', async () => {
    const updatedDoc = mockDoc({ content_md: '# Edited', is_ready: true })
    patch_request.mockResolvedValueOnce({ data: updatedDoc })
    const result = await store.updateDocument(1, 10, { content_md: '# Edited', is_ready: true })
    expect(patch_request).toHaveBeenCalledWith(
      'diagnostics/1/documents/10/update/',
      { content_md: '# Edited', is_ready: true },
    )
    expect(result.success).toBe(true)
  })

  it('updateDocument updates the matching doc in-place in current.documents', async () => {
    store.current = mockDiagnostic({
      id: 1,
      documents: [mockDoc({ id: 10, content_md: 'Old' })],
    })
    patch_request.mockResolvedValueOnce({ data: mockDoc({ id: 10, content_md: 'New' }) })
    await store.updateDocument(1, 10, { content_md: 'New' })
    expect(store.current.documents[0].content_md).toBe('New')
  })

  it('updateDocument leaves other docs untouched', async () => {
    store.current = mockDiagnostic({
      id: 1,
      documents: [
        mockDoc({ id: 10, content_md: 'A' }),
        mockDoc({ id: 11, content_md: 'B' }),
      ],
    })
    patch_request.mockResolvedValueOnce({ data: mockDoc({ id: 10, content_md: 'A edited' }) })
    await store.updateDocument(1, 10, { content_md: 'A edited' })
    expect(store.current.documents[1].content_md).toBe('B')
  })

  it('updateDocument sets error on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.updateDocument(1, 10, {})
    expect(result.success).toBe(false)
    expect(store.error).toBe('update_doc_failed')
  })

  // ── restoreDocument ──────────────────────────────────────────────────────

  it('restoreDocument POSTs to the restore endpoint', async () => {
    create_request.mockResolvedValueOnce({ data: mockDoc() })
    const result = await store.restoreDocument(1, 10)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/documents/10/restore/', {})
    expect(result.success).toBe(true)
  })

  it('restoreDocument updates the doc in current.documents', async () => {
    store.current = mockDiagnostic({
      id: 1,
      documents: [mockDoc({ id: 10, content_md: 'Edited version' })],
    })
    create_request.mockResolvedValueOnce({ data: mockDoc({ id: 10, content_md: '# Original' }) })
    await store.restoreDocument(1, 10)
    expect(store.current.documents[0].content_md).toBe('# Original')
  })

  // ── sendInitial / markInAnalysis / sendFinal ─────────────────────────────

  it('sendInitial POSTs to send-initial/ and updates current on success', async () => {
    const updated = mockDiagnostic({ status: 'sent' })
    create_request.mockResolvedValueOnce({ data: updated })
    const result = await store.sendInitial(1)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/send-initial/', {})
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  it('sendInitial returns error and message on failure', async () => {
    create_request.mockRejectedValueOnce({
      response: { data: { error: 'send_failed', message: 'Email error' } },
    })
    const result = await store.sendInitial(1)
    expect(result.success).toBe(false)
    expect(result.error).toBe('send_failed')
    expect(result.message).toBe('Email error')
  })

  it('markInAnalysis POSTs to mark-in-analysis/ and updates current', async () => {
    const updated = mockDiagnostic({ status: 'negotiating' })
    create_request.mockResolvedValueOnce({ data: updated })
    const result = await store.markInAnalysis(1)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/mark-in-analysis/', {})
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  it('markInAnalysis uses transition_failed as default error key', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.markInAnalysis(1)
    expect(result.success).toBe(false)
    expect(store.error).toBe('transition_failed')
  })

  it('sendFinal POSTs to send-final/ and updates current', async () => {
    const updated = mockDiagnostic({ status: 'sent', final_sent_at: '2026-04-16T10:00:00Z' })
    create_request.mockResolvedValueOnce({ data: updated })
    const result = await store.sendFinal(1)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/send-final/', {})
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  it('sendFinal uses send_failed as default error key', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.sendFinal(1)
    expect(result.success).toBe(false)
    expect(store.error).toBe('send_failed')
  })

  it('transition helpers clear isUpdating in finally', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    await store.sendInitial(1)
    expect(store.isUpdating).toBe(false)
  })

  // ── fetchPublic ──────────────────────────────────────────────────────────

  it('fetchPublic calls GET diagnostics/public/{uuid}/ and sets current', async () => {
    const d = mockDiagnostic({ status: 'sent' })
    get_request.mockResolvedValueOnce({ data: d })
    const result = await store.fetchPublic('aaaa-bbbb')
    expect(get_request).toHaveBeenCalledWith('diagnostics/public/aaaa-bbbb/')
    expect(store.current).toEqual(d)
    expect(result.success).toBe(true)
  })

  it('fetchPublic sets error to not_found on 404', async () => {
    get_request.mockRejectedValueOnce({ response: { status: 404, data: {} } })
    const result = await store.fetchPublic('missing-uuid')
    expect(result.success).toBe(false)
    expect(store.error).toBe('not_found')
  })

  it('fetchPublic sets error to fetch_failed on non-404 errors', async () => {
    get_request.mockRejectedValueOnce({ response: { status: 500, data: {} } })
    await store.fetchPublic('uuid')
    expect(store.error).toBe('fetch_failed')
  })

  it('fetchPublic clears isLoading in finally', async () => {
    get_request.mockRejectedValueOnce({ response: { status: 404, data: {} } })
    await store.fetchPublic('uuid')
    expect(store.isLoading).toBe(false)
  })

  // ── trackView ────────────────────────────────────────────────────────────

  it('trackView POSTs to the track endpoint', async () => {
    create_request.mockResolvedValueOnce({})
    await store.trackView('aaaa-bbbb')
    expect(create_request).toHaveBeenCalledWith('diagnostics/public/aaaa-bbbb/track/', {})
  })

  it('trackView swallows errors silently without mutating state', async () => {
    create_request.mockRejectedValueOnce(new Error('network'))
    await expect(store.trackView('uuid')).resolves.toBeUndefined()
    expect(store.error).toBeNull()
  })

  // ── respondPublic ────────────────────────────────────────────────────────

  it('respondPublic POSTs decision and updates current on success', async () => {
    const updated = mockDiagnostic({ status: 'accepted' })
    create_request.mockResolvedValueOnce({ data: updated })
    const result = await store.respondPublic('aaaa-bbbb', 'accept')
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/public/aaaa-bbbb/respond/',
      { decision: 'accept' },
    )
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  it('respondPublic sets error on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.respondPublic('uuid', 'reject')
    expect(result.success).toBe(false)
    expect(store.error).toBe('respond_failed')
  })

  it('respondPublic clears isUpdating in finally', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    await store.respondPublic('uuid', 'accept')
    expect(store.isUpdating).toBe(false)
  })
})
