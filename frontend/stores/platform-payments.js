import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformPaymentsStore = defineStore('platformPayments', {
  state: () => ({
    subscriptions: [],
    currentSubscription: null,
    payments: [],
    proposals: [],
    isLoading: false,
    isUpdating: false,
    error: '',
  }),

  getters: {
    /**
     * The single payment that represents the current billing cycle.
     * Priority: overdue > failed > pending > processing.
     * If none found, subscription is up to date.
     */
    currentPeriodPayment: (state) => {
      const active = state.payments.filter((p) => ['overdue', 'failed', 'pending', 'processing'].includes(p.status))
      if (active.length === 0) return null
      const priority = { overdue: 0, failed: 1, pending: 2, processing: 3 }
      active.sort((a, b) => (priority[a.status] ?? 9) - (priority[b.status] ?? 9))
      return active[0]
    },

    /**
     * All resolved payments (paid or failed in past cycles) sorted newest first.
     */
    pastPayments: (state) => {
      const currentActive = ['overdue', 'failed', 'pending', 'processing']
      const activePay = state.payments.filter((p) => currentActive.includes(p.status))
      // Sort active by priority to identify the "current" one
      if (activePay.length > 0) {
        const priority = { overdue: 0, failed: 1, pending: 2, processing: 3 }
        activePay.sort((a, b) => (priority[a.status] ?? 9) - (priority[b.status] ?? 9))
        const currentId = activePay[0].id
        return state.payments
          .filter((p) => p.id !== currentId)
          .sort((a, b) => new Date(b.billing_period_start) - new Date(a.billing_period_start))
      }
      return [...state.payments].sort((a, b) => new Date(b.billing_period_start) - new Date(a.billing_period_start))
    },

    /**
     * True when subscription is active and no payment action is needed.
     */
    subscriptionUpToDate: (state) => {
      if (!state.currentSubscription) return false
      const needsAction = state.payments.some((p) => ['overdue', 'failed', 'pending'].includes(p.status))
      return state.currentSubscription.status === 'active' && !needsAction
    },
  },

  actions: {
    async fetchProposals() {
      try {
        const { get } = usePlatformApi()
        const response = await get('proposals/')
        this.proposals = response.data
        return { success: true }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || 'Error cargando propuestas.' }
      }
    },

    async fetchSubscriptions() {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        const response = await get('subscriptions/')
        this.subscriptions = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar las suscripciones.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchProjectSubscription(projectId) {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/subscription/`)
        this.currentSubscription = response.data
        this.payments = response.data.payments || []
        return { success: true, data: response.data }
      } catch (error) {
        if (error.response?.status === 404) {
          this.currentSubscription = null
          this.payments = []
          return { success: true, data: null }
        }
        const message = error.response?.data?.detail || 'Error cargando suscripción.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchProjectPayments(projectId) {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/payments/`)
        this.payments = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'Error cargando pagos.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async updateSubscription(projectId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { patch } = usePlatformApi()
        const response = await patch(`projects/${projectId}/subscription/`, payload)
        this.currentSubscription = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Error actualizando suscripción.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },

    async verifyTransaction(projectId, paymentId, transactionId) {
      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/payments/${paymentId}/verify/`, {
          transaction_id: transactionId,
        })
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || 'Error verificando transacción.' }
      }
    },

    async fetchWidgetData(projectId, paymentId) {
      try {
        const { get } = usePlatformApi()
        const response = await get(`projects/${projectId}/payments/${paymentId}/widget-data/`)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || 'Error obteniendo datos de pago.' }
      }
    },

    async generatePaymentLink(projectId, paymentId) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post(`projects/${projectId}/payments/${paymentId}/generate-link/`)

        const idx = this.payments.findIndex((p) => p.id === paymentId)
        if (idx !== -1) {
          this.payments[idx] = {
            ...this.payments[idx],
            wompi_payment_link_url: response.data.wompi_payment_link_url,
            status: 'processing',
          }
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'Error generando link de pago.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isUpdating = false
      }
    },
  },
})
