import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

export const usePlatformNotificationsStore = defineStore('platformNotifications', {
  state: () => ({
    notifications: [],
    unreadCount: 0,
    isLoading: false,
    error: '',
  }),

  getters: {
    unreadNotifications: (state) => state.notifications.filter((n) => !n.is_read),
    readNotifications: (state) => state.notifications.filter((n) => n.is_read),
  },

  actions: {
    async fetchNotifications(isRead = null) {
      this.isLoading = true
      this.error = ''

      try {
        const { get } = usePlatformApi()
        let url = 'notifications/'
        if (isRead === true) url += '?is_read=true'
        else if (isRead === false) url += '?is_read=false'
        const response = await get(url)
        this.notifications = response.data
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail || 'No pudimos cargar las notificaciones.'
        this.error = message
        return { success: false, message }
      } finally {
        this.isLoading = false
      }
    },

    async fetchUnreadCount() {
      try {
        const { get } = usePlatformApi()
        const response = await get('notifications/unread-count/')
        this.unreadCount = response.data.count
        return { success: true, count: response.data.count }
      } catch {
        return { success: false }
      }
    },

    async markRead(notificationId) {
      try {
        const { post } = usePlatformApi()
        const response = await post(`notifications/${notificationId}/read/`)

        const idx = this.notifications.findIndex((n) => n.id === notificationId)
        if (idx !== -1) this.notifications[idx] = response.data

        if (this.unreadCount > 0) this.unreadCount--
        return { success: true }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || 'Error.' }
      }
    },

    async markAllRead() {
      try {
        const { post } = usePlatformApi()
        const response = await post('notifications/mark-all-read/')

        this.notifications.forEach((n) => { n.is_read = true })
        this.unreadCount = 0
        return { success: true, count: response.data.marked_read }
      } catch (error) {
        return { success: false, message: error.response?.data?.detail || 'Error.' }
      }
    },

    startPolling(intervalMs = 30000) {
      this._pollInterval = setInterval(() => {
        this.fetchUnreadCount()
      }, intervalMs)
      this.fetchUnreadCount()
    },

    stopPolling() {
      if (this._pollInterval) {
        clearInterval(this._pollInterval)
        this._pollInterval = null
      }
    },
  },
})
