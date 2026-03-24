import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformRequirementsStore = defineStore('platformRequirements', {
  state: () => ({
    requirements: [],
    currentRequirement: null,
    projectId: null,
    isLoading: false,
    isUpdating: false,
    error: '',
  }),

  getters: {
    columns() {
      const cols = [
        { key: 'todo', label: 'Por hacer', color: 'blue' },
        { key: 'in_progress', label: 'En progreso', color: 'amber' },
        { key: 'in_review', label: 'En revisión', color: 'purple' },
      ]
      return cols.map((col) => ({
        ...col,
        cards: this.requirements
          .filter((r) => r.status === col.key)
          .sort((a, b) => a.order - b.order),
      }))
    },

    backlogCards: (state) => state.requirements
      .filter((r) => r.status === 'backlog')
      .sort((a, b) => a.order - b.order),

    backlogCount: (state) => state.requirements.filter((r) => r.status === 'backlog').length,

    doneCards: (state) => state.requirements
      .filter((r) => r.status === 'done')
      .sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || '')),

    totalCount: (state) => state.requirements.length,
    doneCount: (state) => state.requirements.filter((r) => r.status === 'done').length,
    progressPercent() {
      if (this.totalCount === 0) return 0
      return Math.round((this.doneCount / this.totalCount) * 100)
    },
  },

  actions: {
    async fetchRequirements(projectId) {
      this.isLoading = true
      this.error = ''
      this.projectId = projectId

      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/requirements/`)
        this.requirements = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar los requerimientos.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchRequirement(projectId, reqId) {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/requirements/${reqId}/`)
        this.currentRequirement = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar el requerimiento.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async createRequirement(projectId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/requirements/`, payload)
        this.requirements.push(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos crear el requerimiento.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async moveRequirement(projectId, reqId, newStatus, newOrder = 0) {
      const card = this.requirements.find((r) => r.id === reqId)
      if (!card) return { success: false, message: 'Card not found' }

      const oldStatus = card.status
      const oldOrder = card.order

      card.status = newStatus
      card.order = newOrder

      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/requirements/${reqId}/move/`, {
          status: newStatus,
          order: newOrder,
        })

        const idx = this.requirements.findIndex((r) => r.id === reqId)
        if (idx !== -1) this.requirements[idx] = response.data

        return { success: true, data: response.data }
      } catch (error) {
        card.status = oldStatus
        card.order = oldOrder
        const message = error.response?.data?.detail || 'No pudimos mover el requerimiento.'
        this.error = message
        return { success: false, message }
      }
    },

    async updateRequirement(projectId, reqId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { patch } = usePlatformApi()
        const response = await patch(`projects/${projectId}/requirements/${reqId}/`, payload)

        const idx = this.requirements.findIndex((r) => r.id === reqId)
        if (idx !== -1) this.requirements[idx] = { ...this.requirements[idx], ...response.data }
        if (this.currentRequirement?.id === reqId) {
          this.currentRequirement = response.data
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos actualizar el requerimiento.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async deleteRequirement(projectId, reqId) {
      this.isUpdating = true
      this.error = ''

      try {
        const { delete: destroy } = usePlatformApi()
        await destroy(`projects/${projectId}/requirements/${reqId}/`)
        this.requirements = this.requirements.filter((r) => r.id !== reqId)
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos eliminar el requerimiento.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async addComment(projectId, reqId, content, isInternal = false) {
      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/requirements/${reqId}/comments/`, {
          content,
          is_internal: isInternal,
        })

        if (this.currentRequirement?.id === reqId && this.currentRequirement.comments) {
          this.currentRequirement.comments.push(response.data)
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos agregar el comentario.'
        return { success: false, message }
      }
    },

    async bulkUpload(projectId, items) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/requirements/bulk/`, items)
        if (response.data.requirements) {
          this.requirements.push(...response.data.requirements)
        }
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Error al cargar requerimientos.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },
  },
})
