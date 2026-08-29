import { defineStore } from 'pinia'
import {
  create_request,
  get_request,
  patch_request,
} from './services/request_http'

const errorPayload = (error) => error?.response?.data || { detail: 'request_failed' }

function readBlobText(blob) {
  if (typeof blob.text === 'function') return blob.text()
  if (typeof FileReader === 'undefined') return Promise.resolve('')

  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsText(blob)
  })
}

async function downloadableErrorPayload(error) {
  const payload = error?.response?.data
  if (typeof Blob === 'undefined' || !(payload instanceof Blob)) return errorPayload(error)

  try {
    const text = await readBlobText(payload)
    if (!text) return { detail: 'request_failed' }
    try {
      return JSON.parse(text)
    } catch {
      return { detail: text }
    }
  } catch {
    return { detail: 'request_failed' }
  }
}

export const useAdditionalModulesStore = defineStore('additional_modules', {
  state: () => ({
    categories: [],
    modules: [],
    revision: '',
    shareLinks: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    activeModules: (state) => state.modules.filter((module) => module.is_active),
    modulesForCategory: (state) => (categoryId) => state.modules.filter(
      (module) => module.category === categoryId,
    ),
  },

  actions: {
    async fetchCatalog() {
      this.isLoading = true
      this.error = null
      try {
        const response = await get_request('additional-modules/admin/')
        this.categories = response.data.categories
        this.modules = response.data.modules
        this.revision = response.data.revision
        return { success: true, data: response.data }
      } catch (error) {
        this.error = errorPayload(error)
        return { success: false, errors: this.error }
      } finally {
        this.isLoading = false
      }
    },

    async saveCategory(categoryId, payload) {
      this.isUpdating = true
      try {
        const response = categoryId
          ? await patch_request(`additional-modules/admin/categories/${categoryId}/`, payload)
          : await create_request('additional-modules/admin/categories/', payload)
        await this.fetchCatalog()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      } finally {
        this.isUpdating = false
      }
    },

    async setCategoryStatus(categoryId, action) {
      this.isUpdating = true
      try {
        const response = await create_request(
          `additional-modules/admin/categories/${categoryId}/${action}/`,
          {},
        )
        await this.fetchCatalog()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      } finally {
        this.isUpdating = false
      }
    },

    async saveModule(moduleId, payload) {
      this.isUpdating = true
      try {
        const response = moduleId
          ? await patch_request(`additional-modules/admin/modules/${moduleId}/`, payload)
          : await create_request('additional-modules/admin/modules/', payload)
        await this.fetchCatalog()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      } finally {
        this.isUpdating = false
      }
    },

    async setModuleStatus(moduleId, action) {
      this.isUpdating = true
      try {
        const response = await create_request(
          `additional-modules/admin/modules/${moduleId}/${action}/`,
          {},
        )
        await this.fetchCatalog()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      } finally {
        this.isUpdating = false
      }
    },

    async reorderCatalog(payload) {
      this.isUpdating = true
      try {
        const response = await create_request('additional-modules/admin/reorder/', {
          revision: this.revision,
          ...payload,
        })
        await this.fetchCatalog()
        return { success: true, data: response.data }
      } catch (error) {
        const errors = errorPayload(error)
        if (error?.response?.status === 409) await this.fetchCatalog()
        return { success: false, errors }
      } finally {
        this.isUpdating = false
      }
    },

    async fetchShareLinks() {
      try {
        const response = await get_request('additional-modules/admin/shares/')
        this.shareLinks = response.data
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      }
    },

    async createShareLink(payload) {
      this.isUpdating = true
      try {
        const response = await create_request('additional-modules/admin/shares/', payload)
        this.shareLinks.unshift(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      } finally {
        this.isUpdating = false
      }
    },

    async setShareLinkStatus(uuid, action) {
      this.isUpdating = true
      try {
        const response = await create_request(
          `additional-modules/admin/shares/${uuid}/${action}/`,
          {},
        )
        const index = this.shareLinks.findIndex((link) => link.uuid === uuid)
        if (index !== -1) this.shareLinks.splice(index, 1, response.data)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: errorPayload(error) }
      } finally {
        this.isUpdating = false
      }
    },

    async downloadPdf(payload) {
      try {
        const response = await create_request(
          'additional-modules/admin/pdf/',
          payload,
          { responseType: 'blob' },
        )
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, errors: await downloadableErrorPayload(error) }
      }
    },
  },
})
