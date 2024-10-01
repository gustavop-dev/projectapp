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
     * getModels3d: Getter that filters 3D models based on the current language.
     * 
     * Iterates over the 3D models and returns the appropriate title based on the selected language.
     * 
     * @param {Object} state - The current state of the store.
     * @returns {Array} - A list of 3D models with titles filtered by language.
     */
    getModels3d: (state) => {
      const languageStore = useLanguageStore(); // Access the language store

      return state.models3d.map((model) => {
        return {
          ...model, // Keeps properties that are not text-based
          title: languageStore.currentLanguage === 'es' ? model.title_es : model.title_en,
        };
      });
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching 3D models data if it hasn't been updated yet.
     * 
     * This action ensures that the 3D models are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areUpdateModels3d) {
        await this.fetchModels3dData();
      }
    },

    /**
     * fetchModels3dData: Fetches 3D models data from the API.
     * 
     * This action makes an HTTP request to fetch the 3D models data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     * 
     * In case of errors during the API request or JSON parsing, it logs the error to the console.
     */
    async fetchModels3dData() {
      if (this.areUpdateModels3d) return;
      try {
        let response = await get_request('api/models3d/');
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
    }
  }
});

