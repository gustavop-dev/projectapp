import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  patch_request,
  delete_request,
} from './services/request_http';
import { normalizeApiError } from './services/normalize_api_error';

/**
 * Accounting entities exposed by the backend (/api/accounting/...).
 * Every entity shares the same CRUD URL shape, so the store maps a key
 * to its endpoint path and the state array holding its records.
 */
const ACCOUNTING_ENTITIES = {
  incomes: { stateKey: 'incomes', path: 'accounting/incomes/' },
  expenses: { stateKey: 'expenses', path: 'accounting/expenses/' },
  hostings: { stateKey: 'hostings', path: 'accounting/hostings/' },
  pocket: { stateKey: 'pocketMovements', path: 'accounting/pocket/' },
  recurring: { stateKey: 'recurringPayments', path: 'accounting/recurring/' },
  ads: { stateKey: 'adsRecords', path: 'accounting/ads/' },
  cards: { stateKey: 'cardSnapshots', path: 'accounting/card-snapshots/' },
  statements: { stateKey: 'statements', path: 'accounting/statements/' },
  merchantAliases: { stateKey: 'merchantAliases', path: 'accounting/merchant-aliases/' },
};

function entityConfig(entity) {
  const config = ACCOUNTING_ENTITIES[entity];
  if (!config) throw new Error(`Unknown accounting entity: ${entity}`);
  return config;
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const encoded = query.toString();
  return encoded ? `?${encoded}` : '';
}

export const useAccountingStore = defineStore('accounting', {
  /**
   * State of the Accounting store.
   *
   * Properties:
   * - incomes/expenses/hostings/pocketMovements/recurringPayments/
   *   adsRecords/cardSnapshots (Array): records per entity.
   * - metas (Object): list meta per entity key (balance, totals...).
   * - summary (Object|null): dashboard payload for selectedYear.
   * - changelog (Object): paginated audit log {results, count, page, numPages}.
   * - settings (Object|null): notification settings singleton.
   */
  state: () => ({
    incomes: [],
    expenses: [],
    hostings: [],
    pocketMovements: [],
    recurringPayments: [],
    adsRecords: [],
    cardSnapshots: [],
    collectionAccounts: [],
    collectionAccountsMeta: {},
    statements: [],
    merchantAliases: [],
    statementStatus: null,
    statementDetail: null,
    metas: {},
    summary: null,
    changelog: { results: [], count: 0, page: 1, numPages: 1 },
    settings: null,
    selectedYear: new Date().getFullYear(),
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    /**
     * metaFor: last list meta for an entity key. The pocket balance lives
     * here too (meta.balance) — the server is its single owner.
     */
    metaFor: (state) => (entity) => state.metas[entity] || {},

    /**
     * pocketWithRunningBalance: movements sorted chronologically with a
     * running_balance column (ledger view).
     */
    pocketWithRunningBalance: (state) => {
      const sorted = [...state.pocketMovements].sort((a, b) =>
        a.movement_date === b.movement_date
          ? String(a.created_at).localeCompare(String(b.created_at))
          : String(a.movement_date).localeCompare(String(b.movement_date)),
      );
      let running = 0;
      return sorted.map((movement) => {
        const amount = Number(movement.amount) || 0;
        running += movement.direction === 'in' ? amount : -amount;
        return { ...movement, running_balance: running };
      });
    },

    /**
     * recurringTotalsByFrequency: COP totals of active payments per frequency label.
     */
    recurringTotalsByFrequency: (state) =>
      state.recurringPayments
        .filter((payment) => payment.is_active)
        .reduce((totals, payment) => {
          const key = payment.frequency_label || payment.frequency;
          totals[key] = (totals[key] || 0) + (Number(payment.cop_equivalent) || 0);
          return totals;
        }, {}),

    /**
     * recurringTotalsByMethod: COP totals of active payments per payment method label.
     */
    recurringTotalsByMethod: (state) =>
      state.recurringPayments
        .filter((payment) => payment.is_active)
        .reduce((totals, payment) => {
          const key = payment.payment_method_label || payment.payment_method;
          totals[key] = (totals[key] || 0) + (Number(payment.cop_equivalent) || 0);
          return totals;
        }, {}),
  },

  actions: {
    /**
     * fetchRecords: List an entity's records with optional query params
     * (year, kind, date_from, date_to, amount_min, amount_max, partner, q...).
     */
    async fetchRecords(entity, params = {}) {
      const config = entityConfig(entity);
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(
          `${config.path}${buildQuery(params)}`,
        );
        this[config.stateKey] = response.data.results;
        this.metas = { ...this.metas, [entity]: response.data.meta || {} };
        return { success: true, data: response.data.results };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error(`Error fetching accounting ${entity}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * createRecord: Create a record and prepend it to the local list.
     */
    async createRecord(entity, payload) {
      const config = entityConfig(entity);
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`${config.path}create/`, payload);
        this[config.stateKey] = [response.data, ...this[config.stateKey]];
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error(`Error creating accounting ${entity}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updateRecord: Patch a record and replace it in the local list.
     */
    async updateRecord(entity, id, payload) {
      const config = entityConfig(entity);
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(
          `${config.path}${id}/update/`, payload,
        );
        this[config.stateKey] = this[config.stateKey].map((record) =>
          record.id === id ? response.data : record,
        );
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error(`Error updating accounting ${entity} ${id}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deleteRecord: Delete a record and drop it from the local list.
     */
    async deleteRecord(entity, id) {
      const config = entityConfig(entity);
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`${config.path}${id}/delete/`);
        this[config.stateKey] = this[config.stateKey].filter(
          (record) => record.id !== id,
        );
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error(`Error deleting accounting ${entity} ${id}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * fetchStatementStatus: 12-month processed/draft/pending grid.
     */
    async fetchStatementStatus(year, cardName = '') {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(
          `accounting/statements/status/${buildQuery({ year, card_name: cardName })}`,
        );
        this.statementStatus = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching statement status:', error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchStatementDetail: header + transactions + category totals.
     */
    async fetchStatementDetail(id) {
      this.error = null;
      try {
        const response = await get_request(`accounting/statements/${id}/`);
        this.statementDetail = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error(`Error fetching statement ${id}:`, error);
        return { success: false, ...normalizeApiError(error) };
      }
    },

    /**
     * finalizeStatement: validate totals and mark processed.
     */
    async finalizeStatement(id, force = false) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(
          `accounting/statements/${id}/finalize/`, { force },
        );
        this.statementDetail = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error(`Error finalizing statement ${id}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * reopenStatement: processed → draft for corrections.
     */
    async reopenStatement(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(
          `accounting/statements/${id}/reopen/`, {},
        );
        this.statementDetail = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error(`Error reopening statement ${id}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updateStatementTransaction: patch one line of a draft statement.
     */
    async updateStatementTransaction(statementId, txId, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(
          `accounting/statements/${statementId}/transactions/${txId}/update/`,
          payload,
        );
        if (this.statementDetail?.id === statementId) {
          this.statementDetail = {
            ...this.statementDetail,
            transactions: this.statementDetail.transactions.map((tx) =>
              tx.id === txId ? response.data : tx,
            ),
          };
        }
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error(`Error updating statement transaction ${txId}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deleteStatementTransaction: remove one line of a draft statement.
     */
    async deleteStatementTransaction(statementId, txId) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(
          `accounting/statements/${statementId}/transactions/${txId}/delete/`,
        );
        if (this.statementDetail?.id === statementId) {
          this.statementDetail = {
            ...this.statementDetail,
            transactions: this.statementDetail.transactions.filter(
              (tx) => tx.id !== txId,
            ),
          };
        }
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error(`Error deleting statement transaction ${txId}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * fetchSummary: Dashboard payload for a year (defaults to selectedYear).
     */
    async fetchSummary(year) {
      const targetYear = year || this.selectedYear;
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(
          `accounting/dashboard/?year=${targetYear}`,
        );
        this.summary = response.data;
        this.selectedYear = targetYear;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'summary_failed';
        console.error('Error fetching accounting summary:', error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchChangelog: Paginated audit log with optional filters
     * ({page, entity_type, object_id, action, actor, date_from, date_to}).
     */
    async fetchChangelog(params = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(
          `accounting/change-logs/${buildQuery(params)}`,
        );
        this.changelog = {
          results: response.data.results,
          count: response.data.count,
          page: response.data.page,
          numPages: response.data.num_pages,
        };
        return { success: true, data: this.changelog };
      } catch (error) {
        this.error = 'changelog_failed';
        console.error('Error fetching accounting changelog:', error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchSettings: Notification settings singleton.
     */
    async fetchSettings() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('accounting/settings/');
        this.settings = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'settings_failed';
        console.error('Error fetching accounting settings:', error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * updateSettings: Patch recipients / notifications toggle.
     */
    async updateSettings(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(
          'accounting/settings/update/', payload,
        );
        this.settings = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'settings_update_failed';
        console.error('Error updating accounting settings:', error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    // ── Collection accounts (cuentas de cobro) ──

    /**
     * fetchCollectionAccounts: Cobros monitor list + status counters.
     */
    async fetchCollectionAccounts(params = {}) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(
          `accounting/collection-accounts/${buildQuery(params)}`,
        );
        this.collectionAccounts = response.data.results ?? [];
        this.collectionAccountsMeta = response.data.meta ?? {};
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching collection accounts:', error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * sendHostingCollectionAccount: issue + email the cuenta de cobro of a
     * hosting. Returns {success, data: {document, email_sent}}.
     */
    async sendHostingCollectionAccount(hostingId) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `accounting/hostings/${hostingId}/send-collection-account/`, {},
        );
        return { success: true, data: response.data };
      } catch (error) {
        console.error(`Error sending collection account (hosting ${hostingId}):`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    async _collectionAccountAction(id, action) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `accounting/collection-accounts/${id}/${action}/`, {},
        );
        if (response.data?.id) {
          this.collectionAccounts = this.collectionAccounts.map((doc) =>
            doc.id === id ? response.data : doc,
          );
        }
        return { success: true, data: response.data };
      } catch (error) {
        console.error(`Error on collection account ${id} ${action}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    // ── Hosting cycles (payment history) ──

    async fetchHostingCycles(hostingId) {
      try {
        const response = await get_request(
          `accounting/hostings/${hostingId}/cycles/`,
        );
        return { success: true, data: response.data.results ?? [] };
      } catch (error) {
        console.error(`Error fetching cycles (hosting ${hostingId}):`, error);
        return { success: false, ...normalizeApiError(error) };
      }
    },

    async createHostingCycle(hostingId, payload) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          `accounting/hostings/${hostingId}/cycles/create/`, payload,
        );
        if (response.data?.hosting) {
          this.hostings = this.hostings.map((record) =>
            record.id === hostingId ? response.data.hosting : record,
          );
        }
        return { success: true, data: response.data };
      } catch (error) {
        console.error(`Error creating cycle (hosting ${hostingId}):`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteHostingCycle(hostingId, cycleId) {
      this.isUpdating = true;
      try {
        await delete_request(
          `accounting/hostings/${hostingId}/cycles/${cycleId}/delete/`,
        );
        return { success: true };
      } catch (error) {
        console.error(`Error deleting cycle ${cycleId}:`, error);
        return { success: false, ...normalizeApiError(error) };
      } finally {
        this.isUpdating = false;
      }
    },

    async resendCollectionAccount(id) {
      return this._collectionAccountAction(id, 'resend');
    },

    async markCollectionAccountPaid(id) {
      return this._collectionAccountAction(id, 'mark-paid');
    },

    async cancelCollectionAccount(id) {
      return this._collectionAccountAction(id, 'cancel');
    },
  },
});
