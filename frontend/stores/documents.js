import { defineStore } from 'pinia';
import axios from 'axios';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useDocumentStore = defineStore('documents', {
  /**
   * State of the Document store.
   *
   * Properties:
   * - documents (Array): List of documents (admin).
   * - currentDocument (Object|null): Currently viewed/edited document.
   * - isLoading (Boolean): Whether a fetch operation is in progress.
   * - isUpdating (Boolean): Whether a mutation operation is in progress.
   * - error (String|null): Last error message.
   */
  state: () => ({
    documents: [],
    currentDocument: null,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    /**
     * getDocumentById: Find a document in the list by its ID.
     */
    getDocumentById: (state) => (id) =>
      state.documents.find((d) => d.id === id),
  },

  actions: {
    /**
     * fetchDocuments: List all documents (admin).
     */
    async fetchDocuments() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('documents/');
        this.documents = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching documents:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchDocument: Retrieve full document detail for admin editing.
     * @param {number} id - Document ID.
     */
    async fetchDocument(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`documents/${id}/detail/`);
        this.currentDocument = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_detail_failed';
        console.error('Error fetching document:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * createFromMarkdown: Create a new document from markdown content.
     * @param {object} data - { title, client_name, language, cover_type, content_markdown }.
     */
    async createFromMarkdown(data) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('documents/create-from-markdown/', data);
        this.currentDocument = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_from_markdown_failed';
        console.error('Error creating document from markdown:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updateDocument: Update document metadata and/or content.
     * @param {number} id - Document ID.
     * @param {object} data - Fields to update.
     */
    async updateDocument(id, data) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`documents/${id}/update/`, data);
        this.currentDocument = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating document:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deleteDocument: Delete a document.
     * @param {number} id - Document ID.
     */
    async deleteDocument(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`documents/${id}/delete/`);
        this.documents = this.documents.filter((d) => d.id !== id);
        if (this.currentDocument?.id === id) {
          this.currentDocument = null;
        }
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting document:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * duplicateDocument: Create a deep copy of a document as a new draft.
     * @param {number} id - Document ID to duplicate.
     */
    async duplicateDocument(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`documents/${id}/duplicate/`, {});
        this.documents.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'duplicate_failed';
        console.error('Error duplicating document:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * downloadPdf: Download a document as PDF.
     * @param {number} id - Document ID.
     * @param {string} title - Filename for the download.
     */
    async downloadPdf(id, title = 'document') {
      try {
        const response = await axios.get(`/api/documents/${id}/pdf/`, {
          responseType: 'blob',
          headers: { 'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '' },
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${title}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        return { success: true };
      } catch (error) {
        console.error('Error downloading PDF:', error);
        return { success: false, errors: error.response?.data };
      }
    },
  },
});
