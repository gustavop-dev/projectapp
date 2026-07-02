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
 * (card-snapshots exists in the API but has no panel view yet — add its
 * entry here when that page is built.)
 */
const ACCOUNTING_ENTITIES = {
  incomes: { stateKey: 'incomes', path: 'accounting/incomes/' },
  expenses: { stateKey: 'expenses', path: 'accounting/expenses/' },
  hostings: { stateKey: 'hostings', path: 'accounting/hostings/' },
  pocket: { stateKey: 'pocketMovements', path: 'accounting/pocket/' },
  recurring: { stateKey: 'recurringPayments', path: 'accounting/recurring/' },
  ads: { stateKey: 'adsRecords', path: 'accounting/ads/' },
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
   *   adsRecords (Array): records per entity.
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
  },
});
