import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformCollectionAccountsStore = defineStore('platformCollectionAccounts', {
  state: () => ({
    accounts: [],
    currentAccount: null,
    isLoading: false,
    isUpdating: false,
    error: '',
  }),

  actions: {
    async fetchList(params = {}) {
      this.isLoading = true
      this.error = ''
      try {
        const { get } = usePlatformApi()
        const response = await get('collection-accounts/', { params })
        this.accounts = response.data
        return { success: true }
      } catch (error) {
        const message =
          error.response?.data?.detail || 'Could not load collection accounts.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchByProject(projectId, deliverableId = null) {
      this.isLoading = true
      this.error = ''
      try {
        const { get } = usePlatformApi()
        const params = deliverableId ? { deliverable_id: deliverableId } : {}
        const response = await get(`projects/${projectId}/collection-accounts/`, { params })
        this.accounts = response.data
        return { success: true }
      } catch (error) {
        const message =
          error.response?.data?.detail || 'Could not load collection accounts for this project.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchDetail(id) {
      this.isLoading = true
      this.error = ''
      try {
        const { get } = usePlatformApi()
        const response = await get(`collection-accounts/${id}/`)
        this.currentAccount = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'Could not load document.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async create(payload) {
      this.isUpdating = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post('collection-accounts/', payload)
        this.currentAccount = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || error.response?.data || 'Could not create.'
        this.error = typeof message === 'string' ? message : 'Could not create.'
        return { success: false, errors: error.response?.data }
      } finally {
        this.isUpdating = false
      }
    },

    async update(id, payload) {
      this.isUpdating = true
      this.error = ''
      try {
        const { patch } = usePlatformApi()
        const response = await patch(`collection-accounts/${id}/`, payload)
        this.currentAccount = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Could not update.'
        this.error = message
        return { success: false, errors: error.response?.data }
      } finally {
        this.isUpdating = false
      }
    },

    async issue(id) {
      this.isUpdating = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post(`collection-accounts/${id}/issue/`)
        this.currentAccount = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Could not issue document.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async markPaid(id) {
      this.isUpdating = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post(`collection-accounts/${id}/mark-paid/`)
        this.currentAccount = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Could not mark as paid.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async markCancelled(id) {
      this.isUpdating = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post(`collection-accounts/${id}/mark-cancelled/`)
        this.currentAccount = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Could not cancel.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async downloadPdf(id, title = 'collection-account') {
      try {
        const { get } = usePlatformApi()
        const response = await get(`collection-accounts/${id}/pdf/`, {
          responseType: 'blob',
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${title.replace(/\s+/g, '-')}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        return { success: true }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || 'PDF download failed.' }
      }
    },
  },
})
