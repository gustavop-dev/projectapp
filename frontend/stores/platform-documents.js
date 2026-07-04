import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformDocumentsStore = defineStore('platformDocuments', {
  state: () => ({
    documents: [],
    email: '',
    emailVerified: false,
    isLoading: false,
    isSending: false,
    isSigning: false,
    error: '',
  }),

  getters: {
    // The main contract the client must sign (if any).
    signableDocument: (state) =>
      state.documents.find((d) => d.requires_signature) || null,
    // Everything else shown as annexes.
    annexes: (state) => state.documents.filter((d) => !d.requires_signature),
  },

  actions: {
    async fetchDocuments() {
      this.isLoading = true
      this.error = ''
      try {
        const { get } = usePlatformApi()
        const response = await get('documents/')
        this.documents = response.data.documents || []
        this.email = response.data.email || ''
        this.emailVerified = !!response.data.email_verified
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No se pudieron cargar los documentos.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false
      }
    },

    async downloadPdf(uuid, title = 'documento') {
      try {
        const { get } = usePlatformApi()
        const response = await get(`documents/${uuid}/pdf/`, { responseType: 'blob' })
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
        return { success: false, message: error.response?.data?.detail || 'No se pudo descargar el PDF.' }
      }
    },

    async requestEmailVerification() {
      this.isSending = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post('email/verify/request/')
        return { success: true, message: response.data.detail }
      } catch (error) {
        const message = error.response?.data?.detail || 'No se pudo enviar el código.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isSending = false
      }
    },

    async confirmEmailVerification(code) {
      this.isSending = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        await post('email/verify/confirm/', { code })
        this.emailVerified = true
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'Código inválido.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isSending = false
      }
    },

    async signDocument(uuid, signatureName = '') {
      this.isSigning = true
      this.error = ''
      try {
        const { post } = usePlatformApi()
        const response = await post(`documents/${uuid}/sign/`, {
          accept: true,
          signature_name: signatureName,
        })
        // Replace the signed document in the local list.
        const idx = this.documents.findIndex((d) => d.uuid === uuid)
        if (idx !== -1) this.documents.splice(idx, 1, response.data)
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No se pudo firmar el documento.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isSigning = false
      }
    },
  },
})
