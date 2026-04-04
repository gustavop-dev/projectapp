import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

function normalizeEmail(value) {
  return `${value || ''}`.trim().toLowerCase()
}

export const usePlatformClientsStore = defineStore('platformClients', {
  state: () => ({
    clients: [],
    currentClient: null,
    activeFilter: 'all',
    isLoading: false,
    isUpdating: false,
    error: '',
  }),

  getters: {
    activeClientsCount: (state) => state.clients.filter((client) => client.is_active).length,
    pendingClientsCount: (state) => state.clients.filter((client) => client.is_active && !client.is_onboarded).length,
    inactiveClientsCount: (state) => state.clients.filter((client) => !client.is_active).length,
    recentClients: (state) => state.clients.slice(0, 5),
  },

  actions: {
    replaceClientInState(updatedClient) {
      this.clients = this.clients.map((client) => (
        client.user_id === updatedClient.user_id ? updatedClient : client
      ))

      if (this.currentClient?.user_id === updatedClient.user_id) {
        this.currentClient = updatedClient
      }
    },

    async fetchClients(filter = 'all') {
      this.isLoading = true
      this.error = ''
      this.activeFilter = filter

      try {
        const { get } = usePlatformApi()
        const query = filter && filter !== 'all' ? `clients/?filter=${filter}` : 'clients/'
        const response = await get(query)
        this.clients = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar los clientes.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false
      }
    },

    async fetchClient(userId) {
      this.isLoading = true
      this.error = ''
      this.currentClient = null

      try {
        const { get } = usePlatformApi()
        const response = await get(`clients/${userId}/`)
        this.currentClient = response.data
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar el detalle del cliente.'
        this.error = message
        this.currentClient = null
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false
      }
    },

    async createClient(payload) {
      const email = normalizeEmail(payload?.email)
      const firstName = `${payload?.first_name || ''}`.trim()
      const lastName = `${payload?.last_name || ''}`.trim()

      if (!email || !firstName || !lastName) {
        const message = 'Completa email, nombre y apellido del cliente.'
        this.error = message
        return { success: false, message }
      }

      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post('clients/', {
          email,
          first_name: firstName,
          last_name: lastName,
          company_name: `${payload?.company_name || ''}`.trim(),
          phone: `${payload?.phone || ''}`.trim(),
        })

        if (this.activeFilter === 'all' || this.activeFilter === 'pending') {
          this.clients = [response.data, ...this.clients]
        }

        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos crear el cliente.'
        this.error = message
        return { success: false, message, errors: error.response?.data }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },

    async updateClient(userId, payload) {
      this.isUpdating = true
      this.error = ''

      try {
        const { patch } = usePlatformApi()
        const response = await patch(`clients/${userId}/`, payload)
        this.replaceClientInState(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos actualizar el cliente.'
        this.error = message
        return { success: false, message, errors: error.response?.data }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },

    async deactivateClient(userId) {
      this.isUpdating = true
      this.error = ''

      try {
        const { delete: destroy } = usePlatformApi()
        await destroy(`clients/${userId}/`)

        const updatedClient = this.clients.find((client) => client.user_id === userId)
        if (updatedClient) {
          const nextClient = { ...updatedClient, is_active: false }
          this.replaceClientInState(nextClient)
        }

        if (this.currentClient?.user_id === userId) {
          this.currentClient = {
            ...this.currentClient,
            is_active: false,
          }
        }

        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos desactivar el cliente.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },

    async resendInvite(userId) {
      this.isUpdating = true
      this.error = ''

      try {
        const { post } = usePlatformApi()
        const response = await post(`clients/${userId}/resend-invite/`, {})

        const updatedClient = this.clients.find((client) => client.user_id === userId)
        if (updatedClient) {
          const nextClient = { ...updatedClient, is_onboarded: false, is_active: true }
          this.replaceClientInState(nextClient)
        }

        if (this.currentClient?.user_id === userId) {
          this.currentClient = {
            ...this.currentClient,
            is_onboarded: false,
            is_active: true,
          }
        }

        return {
          success: true,
          message: response.data.detail || 'Invitación reenviada.',
        }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos reenviar la invitación.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false
      }
    },
  },
})
