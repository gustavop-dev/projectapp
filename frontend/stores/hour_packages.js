import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useHourPackagesStore = defineStore('hour_packages', {
  /**
   * State of the HourPackages store (admin catalog per nationality).
   *
   * Properties:
   * - packages (Array): List of hour packages (filtered by nationality when requested).
   * - currentPackage (Object|null): Currently viewed/edited package.
   * - isLoading (Boolean): Whether a fetch operation is in progress.
   * - isUpdating (Boolean): Whether a mutation operation is in progress.
   * - error (String|null): Last error message.
   */
  state: () => ({
    packages: [],
    currentPackage: null,
    settings: null,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    /**
     * getPackageById: Find a package in the list by its ID.
     */
    getPackageById: (state) => (id) =>
      state.packages.find((p) => p.id === id),
  },

  actions: {
    /**
     * fetchAdminPackages: List hour packages, optionally filtered by nationality.
     * @param {string|null} nationality - 'COL' | 'MEX' | 'USA' or null for all.
     */
    async fetchAdminPackages(nationality = null) {
      this.isLoading = true;
      this.error = null;
      try {
        const url = nationality
          ? `hour-packages/admin/?nationality=${nationality}`
          : 'hour-packages/admin/';
        const response = await get_request(url);
        this.packages = response.data;
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching hour packages:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchAdminPackage: Retrieve full package detail for admin editing.
     * @param {number} id - Package ID.
     */
    async fetchAdminPackage(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`hour-packages/admin/${id}/detail/`);
        this.currentPackage = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching hour package:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * createPackage: Create a new hour package.
     * @param {object} payload - Package data.
     */
    async createPackage(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('hour-packages/admin/create/', payload);
        this.currentPackage = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating hour package:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updatePackage: Update an hour package's fields.
     * @param {number} id - Package ID.
     * @param {object} payload - Fields to update.
     */
    async updatePackage(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`hour-packages/admin/${id}/update/`, payload);
        this.currentPackage = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating hour package:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * fetchSettings: Load the hour-packages panel settings singleton.
     */
    async fetchSettings() {
      try {
        const response = await get_request('hour-packages/admin/settings/');
        this.settings = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching hour package settings:', error);
        return { success: false };
      }
    },

    /**
     * updateSettings: Patch the settings singleton (e.g. default_view_mode).
     * @param {object} payload - Fields to update.
     */
    async updateSettings(payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request('hour-packages/admin/settings/update/', payload);
        this.settings = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error updating hour package settings:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * restoreDefaults: Replace one nationality's catalog with the canonical
     * defaults. The backend returns the fresh list for that nationality.
     * @param {string} nationality - 'COL' | 'MEX' | 'USA'.
     */
    async restoreDefaults(nationality) {
      this.isUpdating = true;
      try {
        const response = await create_request(
          'hour-packages/admin/restore-defaults/', { nationality },
        );
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error restoring default hour packages:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deletePackage: Delete an hour package.
     * @param {number} id - Package ID.
     */
    async deletePackage(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`hour-packages/admin/${id}/delete/`);
        this.packages = this.packages.filter((p) => p.id !== id);
        if (this.currentPackage?.id === id) {
          this.currentPackage = null;
        }
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting hour package:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
