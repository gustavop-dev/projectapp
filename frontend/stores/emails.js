import { defineStore } from 'pinia';
import { get_request, create_request } from './services/request_http';

export const useEmailStore = defineStore('emails', {
  state: () => ({
    history: [],
    historyPagination: { total: 0, page: 1, has_next: false },
    defaults: { greeting: '', footer: '' },
    isSending: false,
    isLoadingHistory: false,
    isLoadingDefaults: false,
    error: null,
  }),

  actions: {
    async fetchDefaults() {
      this.isLoadingDefaults = true;
      this.error = null;
      try {
        const response = await get_request('emails/defaults/');
        this.defaults = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_defaults_failed';
        console.error('Error fetching email defaults:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoadingDefaults = false;
      }
    },

    async fetchHistory(page = 1) {
      this.isLoadingHistory = true;
      this.error = null;
      try {
        const response = await get_request(`emails/history/?page=${page}`);
        if (page === 1) {
          this.history = response.data.results;
        } else {
          this.history.push(...response.data.results);
        }
        this.historyPagination = {
          total: response.data.total,
          page: response.data.page,
          has_next: response.data.has_next,
        };
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_history_failed';
        console.error('Error fetching email history:', error);
        return { success: false, data: { results: [], total: 0, page: 1, has_next: false } };
      /* c8 ignore next 3 */
      } finally {
        this.isLoadingHistory = false;
      }
    },

    async sendEmail(formData) {
      this.isSending = true;
      this.error = null;
      try {
        const response = await create_request('emails/send/', formData);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error.response?.data?.error || 'send_failed';
        console.error('Error sending email:', error);
        return { success: false, error: error.response?.data?.error };
      /* c8 ignore next 3 */
      } finally {
        this.isSending = false;
      }
    },
  },
});
