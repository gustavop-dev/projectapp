import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformDataModelStore = defineStore('platformDataModel', {
  state: () => ({
    entities: [],
    projectId: null,
    isLoading: false,
    isUploading: false,
    error: '',
  }),

  getters: {
    entityCount: (state) => state.entities.length,
  },

  actions: {
    async fetchEntities(projectId) {
      this.isLoading = true
      this.error = ''
      this.projectId = projectId
      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/data-model-entities/`)
        this.entities = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar el modelo de datos.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async uploadEntities(projectId, payload) {
      this.isUploading = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/data-model-entities/`, payload)
        this.entities = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos subir el modelo de datos.'
        this.error = message
        return { success: false, message, errors: error.response?.data }
      } finally {
        this.isUploading = false
      }
    },

    async fetchTemplate(projectId) {
      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/data-model-entities/template/`)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, message: 'No pudimos obtener la plantilla.' }
      }
    },
  },
})
