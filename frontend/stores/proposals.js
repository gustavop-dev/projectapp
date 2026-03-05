import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useProposalStore = defineStore('proposals', {
  /**
   * State of the Proposal store.
   *
   * Properties:
   * - proposals (Array): List of proposals (admin).
   * - currentProposal (Object|null): Currently viewed/edited proposal.
   * - isLoading (Boolean): Whether a fetch operation is in progress.
   * - isUpdating (Boolean): Whether a mutation operation is in progress.
   * - error (String|null): Last error message.
   */
  state: () => ({
    proposals: [],
    currentProposal: null,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    /**
     * getProposalById: Find a proposal in the list by its ID.
     */
    getProposalById: (state) => (id) =>
      state.proposals.find((p) => p.id === id),

    /**
     * enabledSections: Return only enabled sections, sorted by order.
     */
    enabledSections: (state) =>
      state.currentProposal?.sections
        ?.filter((s) => s.is_enabled)
        ?.sort((a, b) => a.order - b.order) || [],

    /**
     * totalSections: Count of enabled sections.
     */
    totalSections: (state) =>
      state.currentProposal?.sections?.filter((s) => s.is_enabled)?.length || 0,
  },

  actions: {
    // -----------------------------------------------------------------
    // Public
    // -----------------------------------------------------------------

    /**
     * fetchPublicProposal: Retrieve a proposal by UUID for client viewing.
     * @param {string} uuid - Proposal UUID.
     */
    async fetchPublicProposal(uuid) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`proposals/${uuid}/`);
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        const status = error.response?.status;
        if (status === 410) {
          this.error = 'expired';
        } else if (status === 404) {
          this.error = 'not_found';
        } else {
          this.error = 'unknown';
        }
        return { success: false, error: this.error, status };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    // -----------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------

    /**
     * fetchProposals: List all proposals (admin).
     * @param {string} [statusFilter] - Optional status filter.
     */
    async fetchProposals(statusFilter) {
      this.isLoading = true;
      this.error = null;
      try {
        const url = statusFilter
          ? `proposals/?status=${statusFilter}`
          : 'proposals/';
        const response = await get_request(url);
        this.proposals = response.data;
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching proposals:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchProposal: Retrieve full proposal detail for admin editing.
     * @param {number} id - Proposal ID.
     */
    async fetchProposal(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`proposals/${id}/detail/`);
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching proposal:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * createProposal: Create a new proposal.
     * @param {object} payload - Proposal data.
     */
    async createProposal(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('proposals/create/', payload);
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating proposal:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updateProposal: Update proposal metadata.
     * @param {number} id - Proposal ID.
     * @param {object} payload - Fields to update.
     */
    async updateProposal(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`proposals/${id}/update/`, payload);
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating proposal:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deleteProposal: Delete a proposal.
     * @param {number} id - Proposal ID.
     */
    async deleteProposal(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`proposals/${id}/delete/`);
        this.proposals = this.proposals.filter((p) => p.id !== id);
        if (this.currentProposal?.id === id) {
          this.currentProposal = null;
        }
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting proposal:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * sendProposal: Mark proposal as SENT and schedule reminder.
     * @param {number} id - Proposal ID.
     */
    async sendProposal(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`proposals/${id}/send/`, {});
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'send_failed';
        console.error('Error sending proposal:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updateSection: Update a proposal section's content.
     * @param {number} sectionId - Section ID.
     * @param {object} payload - Fields to update (content_json, title, etc.).
     */
    async updateSection(sectionId, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(
          `proposals/sections/${sectionId}/update/`,
          payload,
        );
        // Update the section in currentProposal
        if (this.currentProposal?.sections) {
          const idx = this.currentProposal.sections.findIndex(
            (s) => s.id === sectionId,
          );
          if (idx !== -1) {
            this.currentProposal.sections[idx] = response.data;
          }
        }
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_section_failed';
        console.error('Error updating section:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * reorderSections: Bulk reorder sections.
     * @param {number} proposalId - Proposal ID.
     * @param {Array} sections - Array of { id, order }.
     */
    async reorderSections(proposalId, sections) {
      this.isUpdating = true;
      try {
        await create_request(
          `proposals/${proposalId}/reorder-sections/`,
          { sections },
        );
        // Update local order
        if (this.currentProposal?.sections) {
          const orderMap = Object.fromEntries(
            sections.map((s) => [s.id, s.order]),
          );
          this.currentProposal.sections.forEach((s) => {
            if (orderMap[s.id] !== undefined) {
              s.order = orderMap[s.id];
            }
          });
        }
        return { success: true };
      } catch (error) {
        console.error('Error reordering sections:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    // -----------------------------------------------------------------
    // Auth
    // -----------------------------------------------------------------

    /**
     * respondToProposal: Client accepts or rejects a proposal.
     * @param {string} uuid - Proposal UUID.
     * @param {string} action - 'accepted' or 'rejected'.
     */
    async respondToProposal(uuid, action) {
      try {
        const response = await create_request(`proposals/${uuid}/respond/`, { action });
        if (this.currentProposal && this.currentProposal.uuid === uuid) {
          this.currentProposal.status = action;
        }
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error responding to proposal:', error);
        return { success: false };
      }
    },

    /**
     * checkAdminAuth: Verify if the current session is an authenticated staff user.
     */
    async checkAdminAuth() {
      try {
        const response = await get_request('auth/check/');
        return { success: true, user: response.data.user };
      } catch (error) {
        return { success: false };
      }
    },
  },
});
