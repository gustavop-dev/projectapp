import { defineStore } from 'pinia'

import {
  create_request,
  get_request,
  patch_request,
} from './services/request_http'

function responseErrors(error) {
  return error?.response?.data || { detail: 'No fue posible completar la operación.' }
}

export const useFinancingAgreementsStore = defineStore('financingAgreements', {
  state: () => ({
    agreements: [],
    currentAgreement: null,
    templates: [],
    knownPlaceholders: [],
    clientContext: null,
    stats: {},
    total: 0,
    isLoading: false,
    isSaving: false,
    error: null,
  }),

  getters: {
    getById: (state) => (id) => state.agreements.find((row) => row.id === Number(id)) || null,
  },

  actions: {
    async fetchAgreements(params = {}) {
      this.isLoading = true
      this.error = null
      try {
        const query = new URLSearchParams()
        Object.entries(params).forEach(([key, value]) => {
          if (value !== '' && value !== null && value !== undefined) query.set(key, String(value))
        })
        const response = await get_request(`financing/agreements/${query.size ? `?${query}` : ''}`)
        this.agreements = response.data?.results || []
        this.stats = response.data?.stats || {}
        this.total = response.data?.count || 0
        return { success: true, data: response.data }
      } catch (error) {
        this.error = responseErrors(error)
        return { success: false, errors: this.error }
      } finally {
        this.isLoading = false
      }
    },

    async fetchAgreement(id) {
      this.isLoading = true
      this.error = null
      try {
        const response = await get_request(`financing/agreements/${id}/`)
        this.currentAgreement = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.error = responseErrors(error)
        return { success: false, errors: this.error }
      } finally {
        this.isLoading = false
      }
    },

    async fetchTemplates() {
      try {
        const response = await get_request('financing/agreements/templates/')
        this.templates = response.data?.results || []
        this.knownPlaceholders = response.data?.known_placeholders || []
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: responseErrors(error) }
      }
    },

    async fetchClientContext(clientId) {
      if (!clientId) {
        this.clientContext = null
        return { success: true, data: null }
      }
      try {
        const response = await get_request(`financing/agreements/client-context/?client_id=${clientId}`)
        this.clientContext = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.clientContext = null
        return { success: false, errors: responseErrors(error) }
      }
    },

    async createAgreement(payload) {
      this.isSaving = true
      try {
        const response = await create_request('financing/agreements/', payload)
        this.currentAgreement = response.data
        this.agreements = [response.data, ...this.agreements]
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: responseErrors(error) }
      } finally {
        this.isSaving = false
      }
    },

    async updateAgreement(id, payload) {
      this.isSaving = true
      try {
        const response = await patch_request(`financing/agreements/${id}/`, payload)
        this.currentAgreement = response.data
        const index = this.agreements.findIndex((row) => row.id === response.data.id)
        if (index >= 0) this.agreements.splice(index, 1, response.data)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: responseErrors(error) }
      } finally {
        this.isSaving = false
      }
    },

    async runAction(id, action, payload = {}) {
      this.isSaving = true
      try {
        const response = await create_request(`financing/agreements/${id}/${action}/`, payload)
        this.currentAgreement = response.data
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: responseErrors(error) }
      } finally {
        this.isSaving = false
      }
    },

    async uploadSigned(id, file) {
      const payload = new FormData()
      payload.append('signed_document', file)
      return this.runAction(id, 'upload-signed', payload)
    },
  },
})
