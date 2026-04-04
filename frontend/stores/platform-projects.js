import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformProjectsStore = defineStore('platformProjects', {
  state: () => ({
    projects: [],
    currentProject: null,
    isLoading: false,
    isUpdating: false,
    error: '',
  }),

  getters: {
    activeProjects: (state) => state.projects.filter((p) => p.status === 'active'),
    pausedProjects: (state) => state.projects.filter((p) => p.status === 'paused'),
    completedProjects: (state) => state.projects.filter((p) => p.status === 'completed'),
    projectCount: (state) => state.projects.length,
  },

  actions: {
    async fetchProjects(filters = {}) {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        const params = new URLSearchParams()
        if (filters.client) params.append('client', filters.client)
        if (filters.status) params.append('status', filters.status)
        const query = params.toString() ? `projects/?${params}` : 'projects/'
        const response = await get(query)
        this.projects = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar los proyectos.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false
      }
    },

    async fetchProject(projectId) {
      this.isLoading = true
      this.error = ''
      this.currentProject = null

      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/`)
        this.currentProject = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar el proyecto.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false
      }
    },

    async createProject(payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post('projects/', payload)
        this.projects = [response.data, ...this.projects]
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos crear el proyecto.'
        this.error = message
        return { success: false, message, errors: error.response?.data }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },

    async updateProject(projectId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { patch } = usePlatformApi()
        const response = await patch(`projects/${projectId}/`, payload)

        this.projects = this.projects.map((p) =>
          p.id === projectId ? response.data : p,
        )
        if (this.currentProject?.id === projectId) {
          this.currentProject = response.data
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos actualizar el proyecto.'
        this.error = message
        return { success: false, message, errors: error.response?.data }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },

    async archiveProject(projectId) {
      this.isUpdating = true
      this.error = ''

      try {
        const { delete: destroy } = usePlatformApi()
        await destroy(`projects/${projectId}/`)

        this.projects = this.projects.map((p) =>
          p.id === projectId ? { ...p, status: 'archived' } : p,
        )
        if (this.currentProject?.id === projectId) {
          this.currentProject = { ...this.currentProject, status: 'archived' }
        }

        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos archivar el proyecto.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },
  },
})
