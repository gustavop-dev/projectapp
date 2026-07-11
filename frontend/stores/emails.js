import { defineStore } from 'pinia';
import { get_request, create_request, put_request } from './services/request_http';

export const useEmailStore = defineStore('emails', {
  state: () => ({
    history: [],
    historyPagination: { total: 0, page: 1, has_next: false },
    defaults: { greeting: '', footer: '' },
    isSending: false,
    isLoadingHistory: false,
    isLoadingDefaults: false,
    isSavingDefaults: false,
    isLoadingPreview: false,
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

    async saveDefaults(payload) {
      this.isSavingDefaults = true;
      this.error = null;
      try {
        const response = await put_request('emails/defaults/', payload);
        this.defaults = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error.response?.data?.error || 'save_defaults_failed';
        console.error('Error saving email defaults:', error);
        return { success: false, error: error.response?.data?.error };
      /* c8 ignore next 3 */
      } finally {
        this.isSavingDefaults = false;
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

    async previewEmail(payload) {
      this.isLoadingPreview = true;
      this.error = null;
      try {
        const response = await create_request('emails/preview/', payload);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = error.response?.data?.error || 'preview_failed';
        console.error('Error fetching email preview:', error);
        return { success: false, error: error.response?.data?.error };
      /* c8 ignore next 3 */
      } finally {
        this.isLoadingPreview = false;
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
