import { setActivePinia, createPinia } from 'pinia'
import { usePlatformProjectsStore } from '../../stores/platform-projects'

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

const SAMPLE_PROJECT = {
  id: 1,
  name: 'Website Redesign',
  status: 'active',
  progress: 40,
  client_name: 'Ana García',
}

describe('usePlatformProjectsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformProjectsStore()
    jest.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty projects array', () => {
      expect(store.projects).toEqual([])
      expect(store.currentProject).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe('')
    })
  })

  describe('getters', () => {
    beforeEach(() => {
      store.projects = [
        { ...SAMPLE_PROJECT, id: 1, status: 'active' },
        { ...SAMPLE_PROJECT, id: 2, status: 'paused' },
        { ...SAMPLE_PROJECT, id: 3, status: 'completed' },
        { ...SAMPLE_PROJECT, id: 4, status: 'active' },
      ]
    })

    it('activeProjects filters by active status', () => {
      expect(store.activeProjects).toHaveLength(2)
    })

    it('pausedProjects filters by paused status', () => {
      expect(store.pausedProjects).toHaveLength(1)
    })

    it('completedProjects filters by completed status', () => {
      expect(store.completedProjects).toHaveLength(1)
    })

    it('projectCount returns total count', () => {
      expect(store.projectCount).toBe(4)
    })
  })

  describe('fetchProjects', () => {
    it('populates projects on success', async () => {
      mockGet.mockResolvedValueOnce({ data: [SAMPLE_PROJECT] })

      const result = await store.fetchProjects()

      expect(result.success).toBe(true)
      expect(store.projects).toEqual([SAMPLE_PROJECT])
      expect(store.isLoading).toBe(false)
    })

    it('appends filter query params', async () => {
      mockGet.mockResolvedValueOnce({ data: [] })

      await store.fetchProjects({ client: 5, status: 'active' })

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('client=5'),
      )
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('status=active'),
      )
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({
        response: { data: { detail: 'Error de red.' } },
      })

      const result = await store.fetchProjects()

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error de red.')
    })
  })

  describe('fetchProject', () => {
    it('sets currentProject on success', async () => {
      mockGet.mockResolvedValueOnce({ data: SAMPLE_PROJECT })

      const result = await store.fetchProject(1)

      expect(result.success).toBe(true)
      expect(store.currentProject).toEqual(SAMPLE_PROJECT)
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({
        response: { data: { detail: 'No encontrado.' } },
      })

      const result = await store.fetchProject(999)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No encontrado.')
    })
  })

  describe('createProject', () => {
    it('prepends new project to list on success', async () => {
      store.projects = [{ ...SAMPLE_PROJECT, id: 2 }]
      const newProject = { ...SAMPLE_PROJECT, id: 3 }
      mockPost.mockResolvedValueOnce({ data: newProject })

      const result = await store.createProject({ name: 'New', client_id: 1 })

      expect(result.success).toBe(true)
      expect(store.projects[0]).toEqual(newProject)
      expect(store.projects).toHaveLength(2)
    })

    it('sets error on failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Cliente no encontrado.' } },
      })

      const result = await store.createProject({ name: 'X', client_id: 999 })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Cliente no encontrado.')
    })
  })

  describe('updateProject', () => {
    it('replaces project in list on success', async () => {
      store.projects = [SAMPLE_PROJECT]
      const updated = { ...SAMPLE_PROJECT, name: 'Updated' }
      mockPatch.mockResolvedValueOnce({ data: updated })

      const result = await store.updateProject(1, { name: 'Updated' })

      expect(result.success).toBe(true)
      expect(store.projects[0].name).toBe('Updated')
    })

    it('updates currentProject if matching', async () => {
      store.projects = [SAMPLE_PROJECT]
      store.currentProject = SAMPLE_PROJECT
      const updated = { ...SAMPLE_PROJECT, name: 'Updated' }
      mockPatch.mockResolvedValueOnce({ data: updated })

      await store.updateProject(1, { name: 'Updated' })

      expect(store.currentProject.name).toBe('Updated')
    })

    it('sets error on failure', async () => {
      mockPatch.mockRejectedValueOnce({
        response: { data: { detail: 'No autorizado.' } },
      })

      const result = await store.updateProject(1, { name: 'X' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
      expect(store.isUpdating).toBe(false)
    })
  })

  describe('archiveProject', () => {
    it('sets project status to archived on success', async () => {
      store.projects = [SAMPLE_PROJECT]
      mockDelete.mockResolvedValueOnce({})

      const result = await store.archiveProject(1)

      expect(result.success).toBe(true)
      expect(store.projects[0].status).toBe('archived')
    })

    it('updates currentProject if matching', async () => {
      store.projects = [SAMPLE_PROJECT]
      store.currentProject = SAMPLE_PROJECT
      mockDelete.mockResolvedValueOnce({})

      await store.archiveProject(1)

      expect(store.currentProject.status).toBe('archived')
    })

    it('sets error on failure', async () => {
      mockDelete.mockRejectedValueOnce({
        response: { data: { detail: 'No autorizado.' } },
      })

      const result = await store.archiveProject(1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
    })
  })
})
