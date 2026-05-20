import { setActivePinia, createPinia } from 'pinia'
import { usePlatformRequirementsStore } from '../../stores/platform-requirements'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  const mockPatch = jest.fn()
  const mockDelete = jest.fn()
  return {
    usePlatformApi: () => ({
      get: mockGet,
      post: mockPost,
      patch: mockPatch,
      delete: mockDelete,
    }),
    readPlatformSession: jest.fn(() => ({
      accessToken: '', refreshToken: '', user: null,
      verificationToken: '', pendingEmail: '',
    })),
    writePlatformSession: jest.fn(),
    clearPlatformSession: jest.fn(),
    __mockGet: mockGet,
    __mockPost: mockPost,
    __mockPatch: mockPatch,
    __mockDelete: mockDelete,
  }
})

const {
  __mockGet: mockGet,
  __mockPost: mockPost,
  __mockPatch: mockPatch,
  __mockDelete: mockDelete,
} = require('../../composables/usePlatformApi')

const SAMPLE_REQ = {
  id: 1,
  title: 'Login page',
  status: 'todo',
  priority: 'high',
  order: 0,
  comments_count: 2,
  updated_at: '2025-01-01T12:00:00Z',
}

describe('usePlatformRequirementsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformRequirementsStore()
    jest.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty requirements array', () => {
      expect(store.requirements).toEqual([])
      expect(store.currentRequirement).toBeNull()
      expect(store.projectId).toBeNull()
      expect(store.phaseId).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe('')
    })
  })

  describe('getters', () => {
    beforeEach(() => {
      store.requirements = [
        { ...SAMPLE_REQ, id: 1, status: 'todo', order: 1 },
        { ...SAMPLE_REQ, id: 2, status: 'in_progress', order: 0 },
        { ...SAMPLE_REQ, id: 3, status: 'in_review', order: 0 },
        { ...SAMPLE_REQ, id: 4, status: 'done', order: 0, updated_at: '2025-01-02T00:00:00Z' },
        { ...SAMPLE_REQ, id: 5, status: 'done', order: 0, updated_at: '2025-01-03T00:00:00Z' },
        { ...SAMPLE_REQ, id: 6, status: 'todo', order: 0 },
      ]
    })

    it('columns groups cards by status across four columns', () => {
      const cols = store.columns

      expect(cols).toHaveLength(4)
      expect(cols.map((c) => c.key)).toEqual(['todo', 'in_progress', 'in_review', 'done'])
      expect(cols[0].cards).toHaveLength(2)
      expect(cols[1].cards).toHaveLength(1)
      expect(cols[2].cards).toHaveLength(1)
      expect(cols[3].cards).toHaveLength(2)
    })

    it('columns sorts non-done cards by order', () => {
      const todoCards = store.columns[0].cards

      expect(todoCards[0].order).toBeLessThanOrEqual(todoCards[1].order)
    })

    it('columns sorts the done column by updated_at descending', () => {
      const doneCards = store.columns[3].cards

      expect(doneCards[0].id).toBe(5)
      expect(doneCards[1].id).toBe(4)
    })

    it('doneCards filters done requirements', () => {
      expect(store.doneCards).toHaveLength(2)
    })

    it('doneCards sorted by updated_at descending', () => {
      const done = store.doneCards

      expect(done[0].id).toBe(5)
      expect(done[1].id).toBe(4)
    })

    it('totalCount returns all requirements', () => {
      expect(store.totalCount).toBe(6)
    })

    it('doneCount returns done count', () => {
      expect(store.doneCount).toBe(2)
    })

    it('progressPercent calculates correctly', () => {
      expect(store.progressPercent).toBe(33)
    })

    it('progressPercent returns 0 when no requirements', () => {
      store.requirements = []

      expect(store.progressPercent).toBe(0)
    })
  })

  describe('fetchProjectRequirements', () => {
    it('returns data on success', async () => {
      mockGet.mockResolvedValueOnce({ data: [SAMPLE_REQ] })

      const result = await store.fetchProjectRequirements(1)

      expect(result.success).toBe(true)
      expect(result.data).toEqual([SAMPLE_REQ])
      expect(mockGet).toHaveBeenCalledWith('projects/1/requirements/')
    })

    it('returns message on failure', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'No autorizado.' } } })

      const result = await store.fetchProjectRequirements(1)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No autorizado.')
    })
  })

  describe('fetchRequirements', () => {
    it('populates requirements and stores project/phase on success', async () => {
      mockGet.mockResolvedValueOnce({ data: [SAMPLE_REQ] })

      const result = await store.fetchRequirements(1, 7)

      expect(result.success).toBe(true)
      expect(store.requirements).toEqual([SAMPLE_REQ])
      expect(store.projectId).toBe(1)
      expect(store.phaseId).toBe(7)
      expect(store.isLoading).toBe(false)
      expect(mockGet).toHaveBeenCalledWith('projects/1/requirements/?phase_id=7')
    })

    it('omits the phase_id query when no phase is given', async () => {
      mockGet.mockResolvedValueOnce({ data: [] })

      await store.fetchRequirements(1)

      expect(mockGet).toHaveBeenCalledWith('projects/1/requirements/')
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'No autorizado.' } } })

      const result = await store.fetchRequirements(1, 7)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
    })

    it('uses fallback message when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))

      const result = await store.fetchRequirements(1, 7)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos cargar los requerimientos.')
    })
  })

  describe('fetchRequirement', () => {
    it('sets currentRequirement on success', async () => {
      const detail = { ...SAMPLE_REQ, comments: [], history: [] }
      mockGet.mockResolvedValueOnce({ data: detail })

      const result = await store.fetchRequirement(1, 1)

      expect(result.success).toBe(true)
      expect(store.currentRequirement).toEqual(detail)
      expect(mockGet).toHaveBeenCalledWith('projects/1/requirements/1/')
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({ response: { data: { detail: 'No encontrado.' } } })

      const result = await store.fetchRequirement(1, 999)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No encontrado.')
      expect(store.isLoading).toBe(false)
    })

    it('uses fallback message when detail is absent', async () => {
      mockGet.mockRejectedValueOnce(new Error('network'))

      const result = await store.fetchRequirement(1, 1)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos cargar el requerimiento.')
    })
  })

  describe('createRequirement', () => {
    it('appends new requirement to list on success', async () => {
      const newReq = { ...SAMPLE_REQ, id: 10 }
      mockPost.mockResolvedValueOnce({ data: newReq })

      const result = await store.createRequirement(1, { title: 'New' })

      expect(result.success).toBe(true)
      expect(store.requirements).toContainEqual(newReq)
      expect(mockPost).toHaveBeenCalledWith('projects/1/requirements/', { title: 'New' })
    })

    it('sets error on failure', async () => {
      mockPost.mockRejectedValueOnce({ response: { data: { detail: 'Error.' } } })

      const result = await store.createRequirement(1, { title: '' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error.')
    })

    it('uses fallback when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))

      const result = await store.createRequirement(1, {})

      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos crear el requerimiento.')
    })
  })

  describe('moveRequirement', () => {
    it('updates card status optimistically and confirms on success', async () => {
      store.requirements = [{ ...SAMPLE_REQ, id: 1, status: 'todo', order: 0 }]
      const movedReq = { ...SAMPLE_REQ, id: 1, status: 'in_progress', order: 0 }
      mockPost.mockResolvedValueOnce({ data: movedReq })

      const result = await store.moveRequirement(1, 1, 'in_progress', 0)

      expect(result.success).toBe(true)
      expect(store.requirements[0].status).toBe('in_progress')
      expect(mockPost).toHaveBeenCalledWith('projects/1/requirements/1/move/', {
        status: 'in_progress',
        order: 0,
      })
    })

    it('replaces the requirement entry with server response data', async () => {
      store.requirements = [{ ...SAMPLE_REQ, id: 1, status: 'todo', order: 0 }]
      const serverResponse = {
        ...SAMPLE_REQ, id: 1, status: 'in_progress', order: 3, updated_at: '2025-02-01T00:00:00Z',
      }
      mockPost.mockResolvedValueOnce({ data: serverResponse })

      await store.moveRequirement(1, 1, 'in_progress', 3)

      expect(store.requirements[0]).toEqual(serverResponse)
    })

    it('reverts status on API failure', async () => {
      store.requirements = [{ ...SAMPLE_REQ, id: 1, status: 'todo', order: 0 }]
      mockPost.mockRejectedValueOnce({ response: { data: { detail: 'Forbidden.' } } })

      const result = await store.moveRequirement(1, 1, 'done', 0)

      expect(result.success).toBe(false)
      expect(store.requirements[0].status).toBe('todo')
    })

    it('returns error when card not found', async () => {
      store.requirements = []

      const result = await store.moveRequirement(1, 999, 'done', 0)

      expect(result.success).toBe(false)
    })

    it('uses fallback message when move error has no detail', async () => {
      store.requirements = [{ ...SAMPLE_REQ, id: 1, status: 'todo', order: 0 }]
      mockPost.mockRejectedValueOnce({})

      const result = await store.moveRequirement(1, 1, 'done', 0)

      expect(result.message).toBe('No pudimos mover el requerimiento.')
    })
  })

  describe('updateRequirement', () => {
    it('updates requirement in list on success', async () => {
      store.requirements = [SAMPLE_REQ]
      mockPatch.mockResolvedValueOnce({ data: { ...SAMPLE_REQ, title: 'Updated' } })

      const result = await store.updateRequirement(1, 1, { title: 'Updated' })

      expect(result.success).toBe(true)
      expect(store.requirements[0].title).toBe('Updated')
      expect(mockPatch).toHaveBeenCalledWith('projects/1/requirements/1/', { title: 'Updated' })
    })

    it('updates currentRequirement if matching', async () => {
      store.requirements = [SAMPLE_REQ]
      store.currentRequirement = SAMPLE_REQ
      mockPatch.mockResolvedValueOnce({ data: { ...SAMPLE_REQ, title: 'Updated' } })

      await store.updateRequirement(1, 1, { title: 'Updated' })

      expect(store.currentRequirement.title).toBe('Updated')
    })

    it('does not overwrite currentRequirement when id differs', async () => {
      store.requirements = [SAMPLE_REQ]
      store.currentRequirement = { ...SAMPLE_REQ, id: 99 }
      mockPatch.mockResolvedValueOnce({ data: { ...SAMPLE_REQ, title: 'Updated' } })

      await store.updateRequirement(1, 1, { title: 'Updated' })

      expect(store.currentRequirement.id).toBe(99)
      expect(store.currentRequirement.title).toBe(SAMPLE_REQ.title)
    })

    it('skips list update when requirement not in list', async () => {
      store.requirements = []
      mockPatch.mockResolvedValueOnce({ data: { ...SAMPLE_REQ, title: 'Updated' } })

      const result = await store.updateRequirement(1, 1, { title: 'Updated' })

      expect(result.success).toBe(true)
      expect(store.requirements).toHaveLength(0)
    })

    it('sets error on failure', async () => {
      mockPatch.mockRejectedValueOnce({ response: { data: { detail: 'Error al actualizar.' } } })

      const result = await store.updateRequirement(1, 1, { title: 'X' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error al actualizar.')
      expect(store.isUpdating).toBe(false)
    })

    it('uses fallback when detail is absent', async () => {
      mockPatch.mockRejectedValueOnce(new Error('network'))

      const result = await store.updateRequirement(1, 1, {})

      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos actualizar el requerimiento.')
    })
  })

  describe('deleteRequirement', () => {
    it('removes requirement from list on success', async () => {
      store.requirements = [SAMPLE_REQ, { ...SAMPLE_REQ, id: 2 }]
      mockDelete.mockResolvedValueOnce({})

      const result = await store.deleteRequirement(1, 1)

      expect(result.success).toBe(true)
      expect(store.requirements).toHaveLength(1)
      expect(store.requirements[0].id).toBe(2)
      expect(mockDelete).toHaveBeenCalledWith('projects/1/requirements/1/')
    })

    it('sets error on failure', async () => {
      mockDelete.mockRejectedValueOnce({ response: { data: { detail: 'No autorizado.' } } })

      const result = await store.deleteRequirement(1, 1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
    })

    it('uses fallback when detail is absent', async () => {
      mockDelete.mockRejectedValueOnce(new Error('network'))

      const result = await store.deleteRequirement(1, 1)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos eliminar el requerimiento.')
    })
  })

  describe('addComment', () => {
    it('appends comment to currentRequirement on success', async () => {
      store.currentRequirement = { ...SAMPLE_REQ, comments: [] }
      const comment = { id: 1, content: 'Hello', is_internal: false }
      mockPost.mockResolvedValueOnce({ data: comment })

      const result = await store.addComment(1, 1, 'Hello', false)

      expect(result.success).toBe(true)
      expect(store.currentRequirement.comments).toContainEqual(comment)
      expect(mockPost).toHaveBeenCalledWith('projects/1/requirements/1/comments/', {
        content: 'Hello',
        is_internal: false,
      })
    })

    it('skips appending when currentRequirement id does not match reqId', async () => {
      store.currentRequirement = { ...SAMPLE_REQ, id: 99, comments: [] }
      mockPost.mockResolvedValueOnce({ data: { id: 5, content: 'Hi' } })

      const result = await store.addComment(1, 1, 'Hi', false)

      expect(result.success).toBe(true)
      expect(store.currentRequirement.comments).toHaveLength(0)
    })

    it('skips appending when currentRequirement has no comments array', async () => {
      store.currentRequirement = { ...SAMPLE_REQ, id: 1 }
      mockPost.mockResolvedValueOnce({ data: { id: 5, content: 'Hi' } })

      const result = await store.addComment(1, 1, 'Hi', false)

      expect(result.success).toBe(true)
      expect(store.currentRequirement.comments).toBeUndefined()
    })

    it('sets error on failure', async () => {
      mockPost.mockRejectedValueOnce({ response: { data: { detail: 'Error.' } } })

      const result = await store.addComment(1, 1, '', false)

      expect(result.success).toBe(false)
      expect(result.message).toBe('Error.')
    })

    it('uses default fallback message when error has no detail', async () => {
      mockPost.mockRejectedValueOnce({})

      const result = await store.addComment(1, 1, 'Hi', false)

      expect(result.success).toBe(false)
      expect(result.message).toBe('No pudimos agregar el comentario.')
    })
  })

  describe('backlog getters', () => {
    it('backlogCards returns only backlog items sorted by order', () => {
      store.requirements = [
        { ...SAMPLE_REQ, id: 10, status: 'backlog', order: 2 },
        { ...SAMPLE_REQ, id: 11, status: 'backlog', order: 0 },
        { ...SAMPLE_REQ, id: 12, status: 'todo', order: 0 },
      ]

      const cards = store.backlogCards

      expect(cards).toHaveLength(2)
      expect(cards[0].id).toBe(11)
      expect(cards[1].id).toBe(10)
    })

    it('backlogCount returns only backlog count', () => {
      store.requirements = [
        { ...SAMPLE_REQ, id: 1, status: 'backlog' },
        { ...SAMPLE_REQ, id: 2, status: 'backlog' },
        { ...SAMPLE_REQ, id: 3, status: 'todo' },
      ]

      expect(store.backlogCount).toBe(2)
    })
  })

  describe('doneCards sorting with missing updated_at', () => {
    it('handles requirements without updated_at field', () => {
      store.requirements = [
        { ...SAMPLE_REQ, id: 1, status: 'done', updated_at: undefined },
        { ...SAMPLE_REQ, id: 2, status: 'done', updated_at: '2025-01-01' },
      ]

      expect(() => store.doneCards).not.toThrow()
      expect(store.doneCards).toHaveLength(2)
    })

    it('handles requirements where both lack updated_at', () => {
      store.requirements = [
        { ...SAMPLE_REQ, id: 1, status: 'done', updated_at: undefined },
        { ...SAMPLE_REQ, id: 2, status: 'done', updated_at: undefined },
      ]

      expect(() => store.doneCards).not.toThrow()
      expect(store.doneCards).toHaveLength(2)
    })
  })

  describe('bulkUpload', () => {
    it('appends returned requirements to list on success', async () => {
      store.requirements = [SAMPLE_REQ]
      mockPost.mockResolvedValueOnce({
        data: { requirements: [{ ...SAMPLE_REQ, id: 20 }, { ...SAMPLE_REQ, id: 21 }] },
      })

      const result = await store.bulkUpload(1, 7, [{ title: 'A' }, { title: 'B' }])

      expect(result.success).toBe(true)
      expect(store.requirements.map((r) => r.id)).toEqual([1, 20, 21])
      expect(mockPost).toHaveBeenCalledWith(
        'projects/1/requirements/bulk/?phase_id=7&mode=append',
        [{ title: 'A' }, { title: 'B' }],
      )
    })

    it('replaces the list when mode is replace', async () => {
      store.requirements = [SAMPLE_REQ]
      mockPost.mockResolvedValueOnce({ data: { requirements: [{ ...SAMPLE_REQ, id: 30 }] } })

      await store.bulkUpload(1, 7, [{ title: 'A' }], 'replace')

      expect(store.requirements.map((r) => r.id)).toEqual([30])
    })

    it('does not touch list when response has no requirements key', async () => {
      store.requirements = [SAMPLE_REQ]
      mockPost.mockResolvedValueOnce({ data: { message: 'queued' } })

      const result = await store.bulkUpload(1, 7, [{ title: 'A' }])

      expect(result.success).toBe(true)
      expect(store.requirements).toHaveLength(1)
    })

    it('omits phase_id from the query when no phase is given', async () => {
      mockPost.mockResolvedValueOnce({ data: { requirements: [] } })

      await store.bulkUpload(1, null, [])

      expect(mockPost).toHaveBeenCalledWith('projects/1/requirements/bulk/?mode=append', [])
    })

    it('returns failure on error', async () => {
      mockPost.mockRejectedValueOnce({ response: { data: { detail: 'bad' } } })

      const result = await store.bulkUpload(1, 7, [])

      expect(result.success).toBe(false)
      expect(store.error).toBe('bad')
    })

    it('uses fallback message when detail is absent', async () => {
      mockPost.mockRejectedValueOnce(new Error('network'))

      const result = await store.bulkUpload(1, 7, [])

      expect(result.success).toBe(false)
      expect(result.message).toBe('Error al cargar requerimientos.')
    })

    it('clears isUpdating when upload completes', async () => {
      mockPost.mockResolvedValueOnce({ data: { requirements: [] } })

      await store.bulkUpload(1, 7, [])

      expect(store.isUpdating).toBe(false)
    })
  })
})
