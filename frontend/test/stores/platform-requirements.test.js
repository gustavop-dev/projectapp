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
      expect(store.deliverableId).toBeNull()
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

    it('columns groups cards by status with correct labels', () => {
      const cols = store.columns

      expect(cols).toHaveLength(3)
      expect(cols[0].key).toBe('todo')
      expect(cols[0].cards).toHaveLength(2)
      expect(cols[1].key).toBe('in_progress')
      expect(cols[1].cards).toHaveLength(1)
      expect(cols[2].key).toBe('in_review')
      expect(cols[2].cards).toHaveLength(1)
    })

    it('columns sorts cards by order', () => {
      const todoCards = store.columns[0].cards

      expect(todoCards[0].order).toBeLessThanOrEqual(todoCards[1].order)
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

  describe('fetchRequirements', () => {
    it('populates requirements on success', async () => {
      mockGet.mockResolvedValueOnce({ data: [SAMPLE_REQ] })

      const result = await store.fetchRequirements(1, 7)

      expect(result.success).toBe(true)
      expect(store.requirements).toEqual([SAMPLE_REQ])
      expect(store.projectId).toBe(1)
      expect(store.deliverableId).toBe(7)
      expect(store.isLoading).toBe(false)
      expect(mockGet).toHaveBeenCalledWith('projects/1/deliverables/7/requirements/')
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({
        response: { data: { detail: 'No autorizado.' } },
      })

      const result = await store.fetchRequirements(1, 7)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
    })
  })

  describe('fetchRequirement', () => {
    it('sets currentRequirement on success', async () => {
      const detail = { ...SAMPLE_REQ, comments: [], history: [] }
      mockGet.mockResolvedValueOnce({ data: detail })

      const result = await store.fetchRequirement(1, 7, 1)

      expect(result.success).toBe(true)
      expect(store.currentRequirement).toEqual(detail)
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({
        response: { data: { detail: 'No encontrado.' } },
      })

      const result = await store.fetchRequirement(1, 7, 999)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No encontrado.')
      expect(store.isLoading).toBe(false)
    })
  })

  describe('createRequirement', () => {
    it('appends new requirement to list on success', async () => {
      const newReq = { ...SAMPLE_REQ, id: 10 }
      mockPost.mockResolvedValueOnce({ data: newReq })

      const result = await store.createRequirement(1, 7, { title: 'New' })

      expect(result.success).toBe(true)
      expect(store.requirements).toContainEqual(newReq)
    })

    it('sets error on failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Error.' } },
      })

      const result = await store.createRequirement(1, 7, { title: '' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error.')
    })
  })

  describe('moveRequirement', () => {
    it('updates card status optimistically and confirms on success', async () => {
      store.requirements = [{ ...SAMPLE_REQ, id: 1, status: 'todo', order: 0 }]
      const movedReq = { ...SAMPLE_REQ, id: 1, status: 'in_progress', order: 0 }
      mockPost.mockResolvedValueOnce({ data: movedReq })

      const result = await store.moveRequirement(1, 7, 1, 'in_progress', 0)

      expect(result.success).toBe(true)
      expect(store.requirements[0].status).toBe('in_progress')
    })

    it('reverts status on API failure', async () => {
      store.requirements = [{ ...SAMPLE_REQ, id: 1, status: 'todo', order: 0 }]
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Forbidden.' } },
      })

      const result = await store.moveRequirement(1, 7, 1, 'done', 0)

      expect(result.success).toBe(false)
      expect(store.requirements[0].status).toBe('todo')
    })

    it('returns error when card not found', async () => {
      store.requirements = []

      const result = await store.moveRequirement(1, 7, 999, 'done', 0)

      expect(result.success).toBe(false)
    })
  })

  describe('updateRequirement', () => {
    it('updates requirement in list on success', async () => {
      store.requirements = [SAMPLE_REQ]
      const updated = { ...SAMPLE_REQ, title: 'Updated' }
      mockPatch.mockResolvedValueOnce({ data: updated })

      const result = await store.updateRequirement(1, 7, 1, { title: 'Updated' })

      expect(result.success).toBe(true)
      expect(store.requirements[0].title).toBe('Updated')
    })

    it('updates currentRequirement if matching', async () => {
      store.requirements = [SAMPLE_REQ]
      store.currentRequirement = SAMPLE_REQ
      const updated = { ...SAMPLE_REQ, title: 'Updated' }
      mockPatch.mockResolvedValueOnce({ data: updated })

      await store.updateRequirement(1, 7, 1, { title: 'Updated' })

      expect(store.currentRequirement.title).toBe('Updated')
    })

    it('sets error on failure', async () => {
      mockPatch.mockRejectedValueOnce({
        response: { data: { detail: 'Error al actualizar.' } },
      })

      const result = await store.updateRequirement(1, 7, 1, { title: 'X' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error al actualizar.')
      expect(store.isUpdating).toBe(false)
    })
  })

  describe('deleteRequirement', () => {
    it('removes requirement from list on success', async () => {
      store.requirements = [SAMPLE_REQ, { ...SAMPLE_REQ, id: 2 }]
      mockDelete.mockResolvedValueOnce({})

      const result = await store.deleteRequirement(1, 7, 1)

      expect(result.success).toBe(true)
      expect(store.requirements).toHaveLength(1)
      expect(store.requirements[0].id).toBe(2)
    })

    it('sets error on failure', async () => {
      mockDelete.mockRejectedValueOnce({
        response: { data: { detail: 'No autorizado.' } },
      })

      const result = await store.deleteRequirement(1, 7, 1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
    })
  })

  describe('addComment', () => {
    it('appends comment to currentRequirement on success', async () => {
      store.currentRequirement = { ...SAMPLE_REQ, comments: [] }
      const comment = { id: 1, content: 'Hello', is_internal: false }
      mockPost.mockResolvedValueOnce({ data: comment })

      const result = await store.addComment(1, 7, 1, 'Hello', false)

      expect(result.success).toBe(true)
      expect(store.currentRequirement.comments).toContainEqual(comment)
    })

    it('sets error on failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Error.' } },
      })

      const result = await store.addComment(1, 7, 1, '', false)

      expect(result.success).toBe(false)
    })
  })
})
