import { defineStore } from 'pinia';
import { get_request } from './services/request_http';
import { useLanguageStore } from '@/stores/language'; // Import the language store

export const useModels3dStore = defineStore('models_3d', {
  /**
   * State of the Models3d store.
   * 
   * Properties:
   * - models3d (Array): Stores the list of 3D models.
   * - areUpdateModels3d (Boolean): Tracks if the 3D models data has been updated.
   */
  state: () => ({
    models3d: [],
    areUpdateModels3d: false,
  }),

  getters: {
    /**
     * getFilteredModelsAndCategories: Getter that filters models based on the current language
     * and returns both the filtered models and the unique categories.
     *
     * @param {Object} state - The current state of the store.
     * @returns {Object} - An object containing:
     *  - models: An array of 3D models filtered by language.
     *  - categories: An array of unique category titles filtered by language.
     */
    getFilteredModelsAndCategories: (state) => {
      const languageStore = useLanguageStore(); // Access the language store
      const currentLanguage = languageStore.currentLanguage;

      const filterByLanguage = (obj) => {
        let filteredObj = {};

        for (const key in obj) {
          if (key.endsWith("_en") || key.endsWith("_es")) {
            const baseKey = key.replace(/(_en|_es)$/, ""); // Remove the suffix
            filteredObj[baseKey] =
              obj[currentLanguage === "es" ? `${baseKey}_es` : `${baseKey}_en`];
          } else {
            // Keep other properties that are not related to language
            filteredObj[key] = obj[key];
          }
        }

        return filteredObj;
      };

      // Step 1: Filter models based on the language
      const filteredModels = state.models3d.map((model) =>
        filterByLanguage(model)
      );

      // Step 2: Extract unique categories from the filtered models
      const categories = [
        ...new Set(filteredModels.map((model) => model.category_title)),
      ];

      // Return an object with both filtered models and unique categories
      return {
        models: filteredModels, // Filtered models
        categories: categories, // Unique categories
      };
    },

    /**
     * getFilteredByCategory: Getter that filters the passed models by the selected category.
     *
     * @param {Object} state - The current state of the store.
     * @returns {Function} - A function that accepts a list of models and a category,
     * and returns the models filtered by that category.
     */
    getFilteredByCategory: (state) => (models, selectedCategory) => {
      // If "All" is selected, return the entire list of models
      if (selectedCategory === "All") {
        return models;
      }

      // Otherwise, filter by the selected category
      return models.filter(
        (model) => model.category_title === selectedCategory
      );
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching 3D models data if it hasn't been updated yet.
     *
     * This action ensures that the 3D models are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areUpdateModels3d) await this.fetchModels3dData();
    },

    /**
     * fetchModels3dData: Fetches 3D models data from the API.
     *
     * This action makes an HTTP request to fetch the 3D models data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     */
    async fetchModels3dData() {
      if (this.areUpdateModels3d) return;

      try {
        let response = await get_request('models3d/');
        let jsonData = response.data;

        if (jsonData && typeof jsonData === 'string') {
          try {
            jsonData = JSON.parse(jsonData);
          } catch (error) {
            console.error(error.message);
            jsonData = [];
          }
        }

        this.models3d = jsonData ?? [];
        this.areUpdateModels3d = true;
      } catch (error) {
        console.error('Error fetching 3D models:', error);
      }
    },
  },
});