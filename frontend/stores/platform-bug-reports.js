import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformBugReportsStore = defineStore('platformBugReports', {
  state: () => ({
    bugReports: [],
    currentBugReport: null,
    projectId: null,
    isLoading: false,
    isUpdating: false,
    error: '',
  }),

  getters: {
    reportedCount: (state) => state.bugReports.filter((b) => b.status === 'reported').length,
    confirmedCount: (state) => state.bugReports.filter((b) => b.status === 'confirmed').length,
    fixingCount: (state) => state.bugReports.filter((b) => b.status === 'fixing').length,
    resolvedCount: (state) => state.bugReports.filter((b) => b.status === 'resolved').length,

    filteredByStatus: (state) => (statusFilter) => {
      if (!statusFilter || statusFilter === 'all') return state.bugReports
      return state.bugReports.filter((b) => b.status === statusFilter)
    },
  },

  actions: {
    async fetchBugReports(projectId, statusFilter = null) {
      this.isLoading = true
      this.error = ''
      this.projectId = projectId

      try {
        const { get } = usePlatformApi()
        let url = `projects/${projectId}/bug-reports/`
        if (statusFilter) url += `?status=${statusFilter}`
        const response = await get(url)
        this.bugReports = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar los reportes de bugs.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchAllBugReports(statusFilter = null) {
      this.isLoading = true
      this.error = ''
      this.projectId = null

      try {
        const { get } = usePlatformApi()
        let url = 'bug-reports/'
        if (statusFilter) url += `?status=${statusFilter}`
        const response = await get(url)
        this.bugReports = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar los reportes de bugs.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchBugReport(projectId, bugId) {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/bug-reports/${bugId}/`)
        this.currentBugReport = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar el reporte de bug.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async createBugReport(projectId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const hasFile = payload instanceof FormData
        const response = await post(`projects/${projectId}/bug-reports/`, payload, hasFile ? {
          headers: { 'Content-Type': 'multipart/form-data' },
        } : {})
        this.bugReports.unshift(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos crear el reporte de bug.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async evaluateBugReport(projectId, bugId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/bug-reports/${bugId}/evaluate/`, payload)

        const idx = this.bugReports.findIndex((b) => b.id === bugId)
        if (idx !== -1) this.bugReports[idx] = { ...this.bugReports[idx], ...response.data }
        if (this.currentBugReport?.id === bugId) {
          this.currentBugReport = response.data
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos evaluar el reporte de bug.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async deleteBugReport(projectId, bugId) {
      this.isUpdating = true
      this.error = ''

      try {
        const { delete: destroy } = usePlatformApi()
        await destroy(`projects/${projectId}/bug-reports/${bugId}/`)
        this.bugReports = this.bugReports.filter((b) => b.id !== bugId)
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos eliminar el reporte de bug.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async addComment(projectId, bugId, content, isInternal = false) {
      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/bug-reports/${bugId}/comments/`, {
          content,
          is_internal: isInternal,
        })

        if (this.currentBugReport?.id === bugId && this.currentBugReport.comments) {
          this.currentBugReport.comments.push(response.data)
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos agregar el comentario.'
        return { success: false, message }
      }
    },
  },
})
