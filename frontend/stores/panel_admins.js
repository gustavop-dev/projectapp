import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const usePanelAdminsStore = defineStore('panel_admins', {
  state: () => ({
    admins: [],
    loading: false,
    error: null,
  }),

  getters: {
    activeAdmins: (state) => state.admins.filter((a) => a.is_active),
    pendingAdmins: (state) => state.admins.filter((a) => a.is_active && !a.is_onboarded),
    inactiveAdmins: (state) => state.admins.filter((a) => !a.is_active),
  },

  actions: {
    async fetchAdmins(filter = 'all') {
      this.loading = true;
      this.error = null;
      try {
        const queryParam = filter !== 'all' ? `?filter=${filter}` : '';
        const response = await get_request(`accounts/admins/${queryParam}`);
        this.admins = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error.response?.data?.detail || 'Error al cargar administradores.';
        return { success: false, error: this.error };
      } finally {
        this.loading = false;
      }
    },

    async createAdmin(payload) {
      try {
        const response = await create_request('accounts/admins/', payload);
        this.admins.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        const detail = error.response?.data?.detail
          || error.response?.data?.email?.[0]
          || 'Error al crear administrador.';
        return { success: false, error: detail };
      }
    },

    async updateAdmin(userId, payload) {
      try {
        const response = await patch_request(`accounts/admins/${userId}/`, payload);
        const idx = this.admins.findIndex((a) => a.user_id === userId);
        if (idx !== -1) this.admins[idx] = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al actualizar administrador.';
        return { success: false, error: detail };
      }
    },

    async deactivateAdmin(userId) {
      try {
        await delete_request(`accounts/admins/${userId}/`);
        const idx = this.admins.findIndex((a) => a.user_id === userId);
        if (idx !== -1) this.admins[idx].is_active = false;
        return { success: true };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al desactivar administrador.';
        return { success: false, error: detail };
      }
    },

    async reactivateAdmin(userId) {
      try {
        const response = await patch_request(`accounts/admins/${userId}/`, { is_active: true });
        const idx = this.admins.findIndex((a) => a.user_id === userId);
        if (idx !== -1) this.admins[idx] = response.data;
        return { success: true };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al reactivar administrador.';
        return { success: false, error: detail };
      }
    },

    async resendInvite(userId) {
      try {
        await create_request(`accounts/admins/${userId}/resend-invite/`, {});
        return { success: true };
      } catch (error) {
        const detail = error.response?.data?.detail || 'Error al reenviar invitación.';
        return { success: false, error: detail };
      }
    },
  },
});
