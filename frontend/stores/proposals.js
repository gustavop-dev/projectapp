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
          // Store partial data from 410 response for ProposalExpired
          const partial = error.response?.data;
          if (partial) {
            this.currentProposal = {
              client_name: partial.client_name || '',
              title: partial.title || '',
              uuid: partial.uuid || uuid,
              expired_at: partial.expired_at || null,
            };
          }
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
     * createProposalFromJSON: Create a proposal from a complete JSON payload.
     * @param {object} jsonData - Full payload with metadata + sections.
     */
    async createProposalFromJSON(jsonData) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('proposals/create-from-json/', jsonData);
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_from_json_failed';
        console.error('Error creating proposal from JSON:', error);
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
     * duplicateProposal: Create a deep copy of a proposal as a new draft.
     * @param {number} id - Proposal ID to duplicate.
     */
    async duplicateProposal(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`proposals/${id}/duplicate/`, {});
        this.proposals.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'duplicate_failed';
        console.error('Error duplicating proposal:', error);
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
     * resendProposal: Re-send a proposal keeping existing expires_at.
     * @param {number} id - Proposal ID.
     */
    async resendProposal(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`proposals/${id}/resend/`, {});
        this.currentProposal = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'resend_failed';
        console.error('Error resending proposal:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * toggleProposalActive: Toggle a proposal's is_active flag.
     * @param {number} id - Proposal ID.
     */
    async toggleProposalActive(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`proposals/${id}/toggle-active/`, {});
        if (this.currentProposal?.id === id) {
          this.currentProposal = response.data;
        }
        const idx = this.proposals.findIndex((p) => p.id === id);
        if (idx !== -1) {
          this.proposals[idx].is_active = response.data.is_active;
        }
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'toggle_active_failed';
        console.error('Error toggling proposal active:', error);
        return { success: false };
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
     * @param {object} extra - Optional { reason, comment } for rejections.
     */
    async respondToProposal(uuid, action, extra = {}) {
      try {
        const response = await create_request(`proposals/${uuid}/respond/`, { action, ...extra });
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
     * commentOnProposal: Client submits a negotiation comment before deciding.
     * @param {string} uuid - Proposal UUID.
     * @param {string} comment - Client's comment text.
     */
    async commentOnProposal(uuid, comment) {
      try {
        const response = await create_request(`proposals/${uuid}/comment/`, { comment });
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error submitting proposal comment:', error);
        return { success: false };
      }
    },

    /**
     * trackSectionViews: Send section engagement data for a proposal.
     * @param {string} uuid - Proposal UUID.
     * @param {object} payload - { session_id, sections }.
     */
    async trackSectionViews(uuid, payload) {
      try {
        await create_request(`proposals/${uuid}/track/`, payload);
        return { success: true };
      } catch (error) {
        console.error('Error tracking section views:', error);
        return { success: false };
      }
    },

    /**
     * fetchProposalAnalytics: Retrieve engagement analytics for a proposal.
     * @param {number} id - Proposal ID.
     */
    async fetchProposalAnalytics(id) {
      try {
        const response = await get_request(`proposals/${id}/analytics/`);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching proposal analytics:', error);
        return { success: false };
      }
    },

    /**
     * fetchProposalDashboard: Retrieve global KPI metrics for all proposals.
     */
    async fetchProposalDashboard() {
      try {
        const response = await get_request('proposals/dashboard/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching proposal dashboard:', error);
        return { success: false };
      }
    },

    /**
     * scheduleFollowup: Schedule a follow-up reminder for a rejected proposal.
     * @param {string} uuid - Proposal UUID.
     * @param {number} months - Number of months until follow-up.
     */
    async scheduleFollowup(uuid, months = 3) {
      try {
        const response = await create_request(`proposals/${uuid}/schedule-followup/`, { months });
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error scheduling followup:', error);
        return { success: false };
      }
    },

    /**
     * shareProposal: Create a tracked share link for a proposal.
     * @param {string} uuid - Proposal UUID.
     * @param {object} payload - { name, email }.
     */
    async shareProposal(uuid, payload) {
      try {
        const response = await create_request(`proposals/${uuid}/share/`, payload);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error sharing proposal:', error);
        return { success: false };
      }
    },

    /**
     * fetchSharedProposal: Retrieve a proposal via a share link UUID.
     * @param {string} shareUuid - Share link UUID.
     * @param {object} params - Optional { name, email } query params.
     */
    async fetchSharedProposal(shareUuid, params = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const query = new URLSearchParams(params).toString();
        const url = query ? `proposals/shared/${shareUuid}/?${query}` : `proposals/shared/${shareUuid}/`;
        const response = await get_request(url);
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

    /**
     * fetchClients: List all unique clients with their proposal history.
     */
    async fetchClients() {
      try {
        const response = await get_request('proposals/clients/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching clients:', error);
        return { success: false };
      }
    },

    /**
     * logActivity: Manually log a seller activity on a proposal.
     */
    async logActivity(proposalId, payload) {
      try {
        const response = await create_request(`proposals/${proposalId}/log-activity/`, payload);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error logging activity:', error);
        return { success: false };
      }
    },

    /**
     * fetchAlerts: Get proposals that need attention (not viewed, not responded, expiring).
     */
    async fetchAlerts() {
      try {
        const response = await get_request('proposals/alerts/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching alerts:', error);
        return { success: false, data: [] };
      }
    },

    /**
     * createAlert: Create a manual alert/reminder for a proposal.
     * @param {object} payload - { proposal, alert_type, message, alert_date }
     */
    async createAlert(payload) {
      try {
        const response = await create_request('proposals/alerts/create/', payload);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error creating alert:', error);
        return { success: false, errors: error.response?.data };
      }
    },

    /**
     * dismissAlert: Dismiss a manual alert by its ID.
     * @param {number} alertId - The alert ID.
     */
    async dismissAlert(alertId) {
      try {
        await patch_request(`proposals/alerts/${alertId}/dismiss/`, {});
        return { success: true };
      } catch (error) {
        console.error('Error dismissing alert:', error);
        return { success: false };
      }
    },

    /**
     * bulkAction: Perform a batch action on multiple proposals.
     * @param {Array} ids - Proposal IDs.
     * @param {string} action - 'delete' | 'expire' | 'resend'.
     */
    async bulkAction(ids, action) {
      try {
        const response = await create_request('proposals/bulk-action/', { ids, action });
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error performing bulk action:', error);
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
