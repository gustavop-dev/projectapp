import { defineStore } from 'pinia';
import { get_request } from './services/request_http';
import { useLanguageStore } from '~/stores/language';

export const useHostingStore = defineStore('hosting', {
  /**
   * State of the Hosting store.
   * 
   * Properties:
   * - hostings (Array): Stores the list of hosting plans.
   * - areHostingsUpdated (Boolean): Tracks if the hosting data has been updated.
   */
  state: () => ({
    hostings: [],
    areHostingsUpdated: false,
  }),

  getters: {
    /**
     * getHostings: Getter that filters hosting plans based on the current language.
     * 
     * Iterates over the hosting plans and returns the appropriate fields based on the selected language.
     * 
     * @param {Object} state - The current state of the store.
     * @returns {Array} - A list of hosting plans with fields filtered by language.
     */
    getHostings: (state) => {
        const languageStore = useLanguageStore();
  
        return state.hostings.map((hosting) => {
          return {
            title: languageStore.currentLanguage === 'es' ? hosting.title_es : hosting.title_en,
            description: languageStore.currentLanguage === 'es' ? hosting.description_es : hosting.description_en,
            cpu_cores: languageStore.currentLanguage === 'es' ? hosting.cpu_cores_es : hosting.cpu_cores_en,
            ram: languageStore.currentLanguage === 'es' ? hosting.ram_es : hosting.ram_en,
            storage: languageStore.currentLanguage === 'es' ? hosting.storage_es : hosting.storage_en,
            bandwidth: languageStore.currentLanguage === 'es' ? hosting.bandwidth_es : hosting.bandwidth_en,
            data_center_location: languageStore.currentLanguage === 'es' ? hosting.data_center_location_es : hosting.data_center_location_en,
            operating_system: languageStore.currentLanguage === 'es' ? hosting.operating_system_es : hosting.operating_system_en,
            // Include any additional properties that don't require translation
            semi_annually_price: hosting.semi_annually_price,
            annual_price: hosting.annual_price,
          };
        });
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching hosting data if it hasn't been updated yet.
     * 
     * This action ensures that the hosting data is fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areHostingsUpdated) {
        await this.fetchHostingData();
      }
    },

    /**
     * fetchHostingData: Fetches hosting data from the API.
     * 
     * This action makes an HTTP request to fetch the hosting data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     * 
     * In case of errors during the API request or JSON parsing, it logs the error to the console.
     */
    async fetchHostingData() {
      if (this.areHostingsUpdated) return;
      try {
        const response = await get_request('hostings/');
        let jsonData = response.data;

        if (jsonData && typeof jsonData === 'string') {
          try {
            jsonData = JSON.parse(jsonData);
          } catch (error) {
            console.error(error.message);
            jsonData = [];
          }
        }

        this.hostings = jsonData ?? [];
        this.areHostingsUpdated = true;
      } catch (error) {
        console.error('Error fetching hosting data:', error);
      }
    }
  }
});
