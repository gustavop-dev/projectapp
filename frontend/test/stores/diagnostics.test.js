/**
 * Tests for diagnostics store (Web App Diagnostics admin module).
 */
import { setActivePinia, createPinia } from 'pinia'
import { useDiagnosticsStore } from '../../stores/diagnostics'

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  put_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}))

const {
  get_request,
  create_request,
  put_request,
  patch_request,
  delete_request,
} = require('../../stores/services/request_http')

const mockDiagnostic = (overrides = {}) => ({
  id: 1,
  uuid: 'aaaa-bbbb-cccc',
  title: 'Diagnóstico — Acme',
  status: 'draft',
  client_name: 'Acme Corp',
  sections: [],
  change_logs: [],
  ...overrides,
})

const mockSection = (overrides = {}) => ({
  id: 10,
  section_type: 'purpose',
  title: 'Propósito',
  order: 1,
  is_enabled: true,
  visibility: 'both',
  content_json: { title: 'Propósito' },
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

  it('starts with empty diagnostics array and null current', () => {
    expect(store.diagnostics).toEqual([])
    expect(store.current).toBeNull()
    expect(store.isLoading).toBe(false)
    expect(store.isUpdating).toBe(false)
    expect(store.error).toBeNull()
  })

  // ── Getters ──────────────────────────────────────────────────────────────

  it('getById finds a diagnostic by numeric id', () => {
    store.diagnostics = [mockDiagnostic({ id: 1 }), mockDiagnostic({ id: 2 })]
    expect(store.getById(1).id).toBe(1)
    expect(store.getById('2').id).toBe(2)
    expect(store.getById(99)).toBeUndefined()
  })

  it('enabledSections returns only enabled sections sorted by order', () => {
    store.current = mockDiagnostic({
      sections: [
        mockSection({ id: 3, order: 3, is_enabled: true }),
        mockSection({ id: 1, order: 1, is_enabled: true }),
        mockSection({ id: 2, order: 2, is_enabled: false }),
      ],
    })
    expect(store.enabledSections.map((s) => s.id)).toEqual([1, 3])
  })

  it('sectionsByPhase filters by visibility (initial excludes final-only)', () => {
    store.current = mockDiagnostic({
      sections: [
        mockSection({ id: 1, visibility: 'both', order: 1 }),
        mockSection({ id: 2, visibility: 'initial', order: 2 }),
        mockSection({ id: 3, visibility: 'final', order: 3 }),
      ],
    })
    const initial = store.sectionsByPhase('initial')
    expect(initial.map((s) => s.id)).toEqual([1, 2])
    const final = store.sectionsByPhase('final')
    expect(final.map((s) => s.id)).toEqual([1, 3])
  })

  // ── fetchAll ─────────────────────────────────────────────────────────────

  it('fetchAll calls GET diagnostics/ and populates diagnostics array', async () => {
    const list = [mockDiagnostic({ id: 1 })]
    get_request.mockResolvedValueOnce({ data: list })
    const result = await store.fetchAll()
    expect(get_request).toHaveBeenCalledWith('diagnostics/')
    expect(store.diagnostics).toEqual(list)
    expect(result.success).toBe(true)
  })

  it('fetchAll appends status filter as query string', async () => {
    get_request.mockResolvedValueOnce({ data: [] })
    await store.fetchAll({ status: 'draft' })
    expect(get_request).toHaveBeenCalledWith('diagnostics/?status=draft')
  })

  it('fetchAll sets error and clears loading on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: { error: 'server_error' } } })
    const result = await store.fetchAll()
    expect(result.success).toBe(false)
    expect(store.error).toBe('server_error')
    expect(store.isLoading).toBe(false)
  })

  // ── fetchDetail / create / update / remove ──────────────────────────────

  it('fetchDetail sets current and calls the detail endpoint', async () => {
    const d = mockDiagnostic({ id: 7 })
    get_request.mockResolvedValueOnce({ data: d })
    const result = await store.fetchDetail(7)
    expect(get_request).toHaveBeenCalledWith('diagnostics/7/detail/')
    expect(store.current).toEqual(d)
    expect(result.success).toBe(true)
  })

  it('create POSTs to diagnostics/create/ and stores current', async () => {
    const d = mockDiagnostic()
    create_request.mockResolvedValueOnce({ data: d })
    const result = await store.create({ client_id: 1, language: 'es' })
    expect(create_request).toHaveBeenCalledWith('diagnostics/create/', { client_id: 1, language: 'es' })
    expect(store.current).toEqual(d)
    expect(result.success).toBe(true)
  })

  it('update PATCHes and updates current', async () => {
    const updated = mockDiagnostic({ duration_label: '2 semanas' })
    patch_request.mockResolvedValueOnce({ data: updated })
    const result = await store.update(1, { duration_label: '2 semanas' })
    expect(patch_request).toHaveBeenCalledWith('diagnostics/1/update/', { duration_label: '2 semanas' })
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  it('remove DELETEs and filters from diagnostics array', async () => {
    store.current = mockDiagnostic({ id: 3 })
    store.diagnostics = [mockDiagnostic({ id: 3 }), mockDiagnostic({ id: 6 })]
    delete_request.mockResolvedValueOnce({})
    await store.remove(3)
    expect(delete_request).toHaveBeenCalledWith('diagnostics/3/delete/')
    expect(store.diagnostics.map((d) => d.id)).toEqual([6])
    expect(store.current).toBeNull()
  })

  // ── Sections ─────────────────────────────────────────────────────────────

  it('updateSection PATCHes the section endpoint and merges in current', async () => {
    store.current = mockDiagnostic({ id: 1, sections: [mockSection({ id: 10, title: 'Old' })] })
    patch_request.mockResolvedValueOnce({ data: mockSection({ id: 10, title: 'New' }) })
    const result = await store.updateSection(1, 10, { title: 'New' })
    expect(patch_request).toHaveBeenCalledWith(
      'diagnostics/1/sections/10/update/',
      { title: 'New' },
    )
    expect(result.success).toBe(true)
    expect(store.current.sections[0].title).toBe('New')
  })

  it('bulkUpdateSections POSTs to bulk endpoint and replaces current', async () => {
    const next = mockDiagnostic({ sections: [mockSection({ id: 10, title: 'Changed' })] })
    create_request.mockResolvedValueOnce({ data: next })
    const payload = [{ id: 10, title: 'Changed' }]
    const result = await store.bulkUpdateSections(1, payload)
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/1/sections/bulk-update/',
      { sections: payload },
    )
    expect(result.success).toBe(true)
    expect(store.current.sections[0].title).toBe('Changed')
  })

  it('resetSection POSTs and updates the matching section', async () => {
    store.current = mockDiagnostic({ id: 1, sections: [mockSection({ id: 10, title: 'Edited' })] })
    create_request.mockResolvedValueOnce({ data: mockSection({ id: 10, title: 'Propósito' }) })
    const result = await store.resetSection(1, 10)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/sections/10/reset/', {})
    expect(result.success).toBe(true)
    expect(store.current.sections[0].title).toBe('Propósito')
  })

  // ── Activity ─────────────────────────────────────────────────────────────

  it('fetchActivity GETs and updates change_logs on current', async () => {
    store.current = mockDiagnostic({ id: 1 })
    const logs = [{ id: 5, change_type: 'note', description: 'Nota' }]
    get_request.mockResolvedValueOnce({ data: logs })
    const result = await store.fetchActivity(1)
    expect(get_request).toHaveBeenCalledWith('diagnostics/1/activity/')
    expect(result.success).toBe(true)
    expect(store.current.change_logs).toEqual(logs)
  })

  it('logActivity prepends the new entry to current.change_logs', async () => {
    store.current = mockDiagnostic({ id: 1, change_logs: [{ id: 2 }] })
    create_request.mockResolvedValueOnce({ data: { id: 7, change_type: 'note', description: 'X' } })
    const result = await store.logActivity(1, 'note', 'X')
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/1/activity/create/',
      { change_type: 'note', description: 'X' },
    )
    expect(result.success).toBe(true)
    expect(store.current.change_logs.map((l) => l.id)).toEqual([7, 2])
  })

  // ── Analytics ────────────────────────────────────────────────────────────

  it('fetchAnalytics GETs the analytics endpoint', async () => {
    get_request.mockResolvedValueOnce({ data: { view_count: 3, sections: [] } })
    const result = await store.fetchAnalytics(1)
    expect(get_request).toHaveBeenCalledWith('diagnostics/1/analytics/')
    expect(result.success).toBe(true)
    expect(result.data.view_count).toBe(3)
  })

  // ── Transitions ──────────────────────────────────────────────────────────

  it('sendInitial POSTs to send-initial/ and updates current', async () => {
    const updated = mockDiagnostic({ status: 'sent' })
    create_request.mockResolvedValueOnce({ data: updated })
    const result = await store.sendInitial(1)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/send-initial/', {})
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
    const updated = mockDiagnostic({ status: 'sent' })
    create_request.mockResolvedValueOnce({ data: updated })
    const result = await store.sendFinal(1)
    expect(create_request).toHaveBeenCalledWith('diagnostics/1/send-final/', {})
    expect(store.current).toEqual(updated)
    expect(result.success).toBe(true)
  })

  // ── fetchPublic / trackView / trackSectionView ──────────────────────────

  it('fetchPublic sets current from the public endpoint', async () => {
    const d = mockDiagnostic({ status: 'sent' })
    get_request.mockResolvedValueOnce({ data: d })
    const result = await store.fetchPublic('aaaa-bbbb')
    expect(get_request).toHaveBeenCalledWith('diagnostics/public/by-slug/aaaa-bbbb/')
    expect(store.current).toEqual(d)
    expect(result.success).toBe(true)
  })

  it('fetchPublic sets error to not_found on 404', async () => {
    get_request.mockRejectedValueOnce({ response: { status: 404, data: {} } })
    const result = await store.fetchPublic('missing-uuid')
    expect(result.success).toBe(false)
    expect(store.error).toBe('not_found')
  })

  it('trackView POSTs to the track endpoint with session id', async () => {
    create_request.mockResolvedValueOnce({})
    await store.trackView('aaaa-bbbb', 'sess-1')
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/public/aaaa-bbbb/track/',
      { session_id: 'sess-1' },
    )
  })

  it('trackView swallows errors silently', async () => {
    create_request.mockRejectedValueOnce(new Error('network'))
    await expect(store.trackView('uuid')).resolves.toBeUndefined()
    expect(store.error).toBeNull()
  })

  it('trackSectionView POSTs to the section-track endpoint', async () => {
    create_request.mockResolvedValueOnce({})
    await store.trackSectionView('aaaa-bbbb', {
      session_id: 'sess',
      section_type: 'purpose',
      section_title: 'Propósito',
      time_spent_seconds: 12.5,
    })
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/public/aaaa-bbbb/track-section/',
      {
        session_id: 'sess',
        section_type: 'purpose',
        section_title: 'Propósito',
        time_spent_seconds: 12.5,
      },
    )
  })

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

  // ── Attachments ──────────────────────────────────────────────────────────

  it('fetchAttachments GETs and writes to current.attachments when ids match', async () => {
    store.current = mockDiagnostic({ id: 7, attachments: [] })
    get_request.mockResolvedValueOnce({ data: [{ id: 1 }] })
    await store.fetchAttachments(7)
    expect(get_request).toHaveBeenCalledWith('diagnostics/7/attachments/')
    expect(store.current.attachments).toEqual([{ id: 1 }])
  })

  it('uploadAttachment appends to current.attachments on success', async () => {
    store.current = mockDiagnostic({ id: 7, attachments: [{ id: 1 }] })
    const fd = new FormData()
    create_request.mockResolvedValueOnce({ data: { id: 2 } })
    await store.uploadAttachment(7, fd)
    expect(create_request).toHaveBeenCalledWith('diagnostics/7/attachments/upload/', fd)
    expect(store.current.attachments.map((a) => a.id)).toEqual([1, 2])
  })

  it('deleteAttachment filters from current.attachments', async () => {
    store.current = mockDiagnostic({ id: 7, attachments: [{ id: 1 }, { id: 2 }] })
    delete_request.mockResolvedValueOnce({})
    await store.deleteAttachment(7, 2)
    expect(store.current.attachments.map((a) => a.id)).toEqual([1])
  })

  // ── Email composer ───────────────────────────────────────────────────────

  it('sendCustomEmail surfaces HTTP status on 429', async () => {
    create_request.mockRejectedValueOnce({
      response: { status: 429, data: { error: 'cool_down' } },
    })
    const result = await store.sendCustomEmail(7, new FormData())
    expect(result.status).toBe(429)
    expect(result.error).toBe('cool_down')
  })

  it('fetchEmailDefaults hits the defaults endpoint', async () => {
    get_request.mockResolvedValueOnce({ data: { recipient_email: 'x@y.com' } })
    const result = await store.fetchEmailDefaults(7)
    expect(get_request).toHaveBeenCalledWith('diagnostics/7/email/defaults/')
    expect(result.data.recipient_email).toBe('x@y.com')
  })

  // ── Error paths for new section/activity/analytics actions ─────────────

  it('updateSection returns error shape on failure', async () => {
    patch_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.updateSection(1, 10, {})
    expect(result.success).toBe(false)
    expect(store.error).toBe('update_section_failed')
  })

  it('bulkUpdateSections returns error shape on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { error: 'sections_must_be_list' } } })
    const result = await store.bulkUpdateSections(1, [])
    expect(result.success).toBe(false)
    expect(store.error).toBe('sections_must_be_list')
  })

  it('resetSection returns error shape on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.resetSection(1, 10)
    expect(result.success).toBe(false)
    expect(result.error).toBe('reset_failed')
  })

  it('fetchActivity returns error shape on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.fetchActivity(1)
    expect(result.success).toBe(false)
    expect(result.error).toBe('fetch_failed')
  })

  it('logActivity returns error shape on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { error: 'description_required' } } })
    const result = await store.logActivity(1, 'note', '')
    expect(result.success).toBe(false)
    expect(result.error).toBe('description_required')
  })

  it('fetchAnalytics returns null data on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: {} } })
    const result = await store.fetchAnalytics(1)
    expect(result.success).toBe(false)
    expect(result.data).toBeNull()
  })

  it('trackSectionView swallows network errors silently', async () => {
    create_request.mockRejectedValueOnce(new Error('offline'))
    await expect(
      store.trackSectionView('uuid', { session_id: 's', section_type: 'purpose' }),
    ).resolves.toBeUndefined()
    expect(store.error).toBeNull()
  })

  it('respondPublic sets error on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { error: 'invalid_transition' } } })
    const result = await store.respondPublic('uuid', 'accept')
    expect(result.success).toBe(false)
    expect(store.error).toBe('invalid_transition')
  })

  // ── Diagnostic defaults ────────────────────────────────────────────────

  it('fetchDiagnosticDefaults requests the lang-scoped endpoint', async () => {
    get_request.mockResolvedValueOnce({
      data: {
        language: 'es',
        payment_initial_pct: 60,
        payment_final_pct: 40,
        sections_json: [],
      },
    })
    const result = await store.fetchDiagnosticDefaults('es')
    expect(get_request).toHaveBeenCalledWith('diagnostics/defaults/?lang=es')
    expect(result.success).toBe(true)
    expect(result.data.payment_initial_pct).toBe(60)
  })

  it('fetchDiagnosticDefaults returns errors on failure', async () => {
    get_request.mockRejectedValueOnce({ response: { data: { detail: 'oops' } } })
    const result = await store.fetchDiagnosticDefaults('en')
    expect(result.success).toBe(false)
    expect(store.error).toBe('fetch_defaults_failed')
  })

  it('saveDiagnosticDefaults PUTs only the whitelisted general fields', async () => {
    put_request.mockResolvedValueOnce({ data: { id: 1, language: 'es' } })
    const result = await store.saveDiagnosticDefaults(
      'es',
      [{ section_type: 'purpose', title: 'X', order: 0, content_json: {} }],
      {
        payment_initial_pct: 70,
        payment_final_pct: 30,
        default_currency: 'USD',
        default_investment_amount: 1500,
        default_duration_label: '4 semanas',
        expiration_days: 30,
        reminder_days: 5,
        urgency_reminder_days: 10,
        ignored_field: 'should not be sent',
      },
    )
    expect(put_request).toHaveBeenCalledTimes(1)
    const [url, payload] = put_request.mock.calls[0]
    expect(url).toBe('diagnostics/defaults/')
    expect(payload).toEqual({
      language: 'es',
      sections_json: [{ section_type: 'purpose', title: 'X', order: 0, content_json: {} }],
      payment_initial_pct: 70,
      payment_final_pct: 30,
      default_currency: 'USD',
      default_investment_amount: 1500,
      default_duration_label: '4 semanas',
      expiration_days: 30,
      reminder_days: 5,
      urgency_reminder_days: 10,
    })
    expect(result.success).toBe(true)
  })

  it('saveDiagnosticDefaults can be called without a sections array', async () => {
    put_request.mockResolvedValueOnce({ data: { id: 1 } })
    await store.saveDiagnosticDefaults('en', null, { payment_initial_pct: 50, payment_final_pct: 50 })
    const [, payload] = put_request.mock.calls[0]
    expect(payload).not.toHaveProperty('sections_json')
    expect(payload.payment_initial_pct).toBe(50)
  })

  it('saveDiagnosticDefaults surfaces validation errors', async () => {
    put_request.mockRejectedValueOnce({
      response: { data: { payment_initial_pct: ['must equal 100'] } },
    })
    const result = await store.saveDiagnosticDefaults('es', null, {})
    expect(result.success).toBe(false)
    expect(result.errors).toEqual({ payment_initial_pct: ['must equal 100'] })
  })

  it('resetDiagnosticDefaults POSTs the language and reports success', async () => {
    create_request.mockResolvedValueOnce({ data: { status: 'reset', deleted: true } })
    const result = await store.resetDiagnosticDefaults('es')
    expect(create_request).toHaveBeenCalledWith('diagnostics/defaults/reset/', { language: 'es' })
    expect(result.success).toBe(true)
    expect(result.data.deleted).toBe(true)
  })

  // ── sendAttachmentsToClient ───────────────────────────────────────────────

  it('sendAttachmentsToClient POSTs to attachments/send/ and returns data', async () => {
    create_request.mockResolvedValueOnce({ data: { sent: true } })
    const result = await store.sendAttachmentsToClient(5, { attachment_ids: [1, 2] })
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/5/attachments/send/',
      { attachment_ids: [1, 2] },
    )
    expect(result.success).toBe(true)
    expect(result.data.sent).toBe(true)
  })

  it('sendAttachmentsToClient returns success false on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { error: 'send_failed' } } })
    const result = await store.sendAttachmentsToClient(5, {})
    expect(result.success).toBe(false)
    expect(result.error).toBe('send_failed')
  })

  // ── fetchEmailHistory ─────────────────────────────────────────────────────

  it('fetchEmailHistory GETs the history endpoint with default page 1', async () => {
    get_request.mockResolvedValueOnce({ data: { results: [], total: 0, has_next: false } })
    const result = await store.fetchEmailHistory(3)
    expect(get_request).toHaveBeenCalledWith('diagnostics/3/email/history/?page=1')
    expect(result.success).toBe(true)
  })

  it('fetchEmailHistory passes explicit page number in query string', async () => {
    get_request.mockResolvedValueOnce({ data: { results: [{ id: 10 }], total: 1, has_next: false } })
    const result = await store.fetchEmailHistory(3, 2)
    expect(get_request).toHaveBeenCalledWith('diagnostics/3/email/history/?page=2')
    expect(result.data.results[0].id).toBe(10)
  })

  it('fetchEmailHistory returns fallback data on network error', async () => {
    get_request.mockRejectedValueOnce(new Error('offline'))
    const result = await store.fetchEmailHistory(3)
    expect(result.success).toBe(false)
    expect(result.data).toEqual({ results: [], total: 0, page: 1, has_next: false })
  })

  // ── generateConfidentiality ────────────────────────────────────────────────

  it('generateConfidentiality POSTs and returns data on success', async () => {
    create_request.mockResolvedValueOnce({ data: { pdf_url: '/media/nda.pdf' } })
    const result = await store.generateConfidentiality(4)
    expect(create_request).toHaveBeenCalledWith('diagnostics/4/confidentiality/generate/', {})
    expect(result.success).toBe(true)
    expect(result.data.pdf_url).toBe('/media/nda.pdf')
  })

  it('generateConfidentiality returns success false on failure', async () => {
    create_request.mockRejectedValueOnce({ response: { data: { error: 'generate_failed' } } })
    const result = await store.generateConfidentiality(4)
    expect(result.success).toBe(false)
    expect(result.error).toBe('generate_failed')
  })

  it('generateConfidentiality updates current.attachments when attachment returned', async () => {
    store.current = mockDiagnostic({ id: 4, attachments: [] })
    create_request.mockResolvedValueOnce({ data: { attachment: { id: 99, type: 'nda' } } })
    await store.generateConfidentiality(4)
    expect(store.current.attachments.some((a) => a.id === 99)).toBe(true)
  })

  // ── trackSectionView with entered_at ──────────────────────────────────────

  it('trackSectionView includes entered_at in POST payload', async () => {
    create_request.mockResolvedValueOnce({})
    await store.trackSectionView('uuid-x', {
      session_id: 'sess',
      section_type: 'intro',
      section_title: 'Intro',
      time_spent_seconds: 5,
      entered_at: '2026-01-01T10:00:00Z',
    })
    const [, payload] = create_request.mock.calls[0]
    expect(payload.entered_at).toBe('2026-01-01T10:00:00Z')
  })

  // ── updateConfidentialityParams ───────────────────────────────────────────

  it('updateConfidentialityParams POSTs params and returns data', async () => {
    create_request.mockResolvedValueOnce({ data: { confidentiality_params: { name: 'Acme' } } })
    const result = await store.updateConfidentialityParams(4, { name: 'Acme' })
    expect(create_request).toHaveBeenCalledWith(
      'diagnostics/4/confidentiality/params/',
      { confidentiality_params: { name: 'Acme' } },
    )
    expect(result.success).toBe(true)
  })
})
