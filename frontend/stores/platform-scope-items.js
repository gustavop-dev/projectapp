import { defineStore } from 'pinia'
import { usePlatformApi } from '~/composables/usePlatformApi'

// Client-facing mirror of a proposal's vistas/componentes/funcionalidades.
// Used as the grouping backbone for the project Kanban board.
export const usePlatformScopeItemsStore = defineStore('platformScopeItems', {
  state: () => ({
    items: [],
    projectId: null,
    isLoading: false,
    error: '',
  }),

  getters: {
    itemCount: (state) => state.items.length,

    // Scope items grouped by their group_id (views / components / features / …),
    // preserving backend ordering, for grouped/swimlane rendering.
    groups: (state) => {
      const map = new Map()
      for (const item of state.items) {
        const key = item.group_id || 'otros'
        if (!map.has(key)) {
          map.set(key, {
            group_id: key,
            group_title: item.group_title || key,
            group_icon: item.group_icon || '',
            items: [],
          })
        }
        map.get(key).items.push(item)
      }
      return Array.from(map.values())
    },
  },

  actions: {
    async fetchScopeItems(projectId, phaseId = null) {
      this.isLoading = true
      this.error = ''
      this.projectId = projectId
      try {
        const { get } = usePlatformApi()
        const suffix = phaseId ? `?phase_id=${phaseId}` : ''
        const response = await get(`projects/${projectId}/scope-items/${suffix}`)
        // Guard against non-array payloads so board getters stay safe.
        this.items = Array.isArray(response.data) ? response.data : []
        return { success: true }
      } catch (error) {
        const message = error.response?.data?.detail
          || 'No pudimos cargar las vistas, componentes y funcionalidades.'
        this.error = message
        return { success: false, message }
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false
      }
    },
  },
})
