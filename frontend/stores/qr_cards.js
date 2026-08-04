import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useQrCardsStore = defineStore('qr_cards', {
  state: () => ({
    cards: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    getCardById: (state) => (id) => state.cards.find((c) => c.id === id),
  },

  actions: {
    async fetchCards() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('qr-cards/admin/');
        this.cards = response.data || [];
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching QR cards:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async createCard(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('qr-cards/admin/create/', payload);
        this.cards.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating QR card:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async updateCard(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`qr-cards/admin/${id}/update/`, payload);
        const index = this.cards.findIndex((c) => c.id === id);
        if (index !== -1) this.cards[index] = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating QR card:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteCard(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`qr-cards/admin/${id}/delete/`);
        this.cards = this.cards.filter((c) => c.id !== id);
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting QR card:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
