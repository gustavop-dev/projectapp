import { defineStore } from 'pinia'
import { get_request, create_request } from './services/request_http'

export const useMonitoringStore = defineStore('monitoring', {
  state: () => ({
    resources: [], sources: [], records: [], count: 0, pageSize: 25,
    detail: null, loading: false, saving: false, error: '', requestId: 0, detailId: 0,
  }),
  actions: {
    async catalog() {
      const { data } = await get_request('monitoring/catalog/')
      this.resources = data.resources
      this.sources = data.sources
    },
    async list(params, reports = false) {
      const requestId = ++this.requestId
      this.loading = true
      this.error = ''
      try {
        const { data } = await get_request(`monitoring/${reports ? 'reports' : 'cases'}/`, { params })
        if (requestId !== this.requestId) return
        this.records = data.results
        this.count = data.count
        this.pageSize = data.page_size
      } catch (error) {
        if (requestId === this.requestId) this.error = error.response?.data?.detail || 'load'
      } finally {
        if (requestId === this.requestId) this.loading = false
      }
    },
    async open(id, reports = false, page = 1) {
      const detailId = ++this.detailId
      const { data } = await get_request(`monitoring/${reports ? 'reports' : 'cases'}/${id}/`, { params: { page } })
      if (detailId === this.detailId) this.detail = data
    },
    close() {
      this.detailId += 1
      this.detail = null
    },
    async transition(state) {
      this.saving = true
      try {
        const { id, version } = this.detail
        await create_request(`monitoring/cases/${id}/state/`, { state, version })
        await this.open(id)
      } finally { this.saving = false }
    },
    async note(text) {
      this.saving = true
      try {
        const id = this.detail.id
        await create_request(`monitoring/cases/${id}/notes/`, { text })
        await this.open(id)
      } finally { this.saving = false }
    },
  },
})
