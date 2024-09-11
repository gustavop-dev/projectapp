import { defineStore } from 'pinia';
import { get_request } from './services/request_http';
import { useLanguageStore } from '@/stores/language'; // Import the language store

export const useWebDesignsStore = defineStore('web-designs', {
  /**
   * State of the WebDesigns store.
   * 
   * Properties:
   * - designs (Array): Stores the list of web designs.
   * - areUpdateDesigns (Boolean): Tracks if the designs data has been updated.
   */
  state: () => ({
    designs: [],
    areUpdateDesigns: false,
  }),

  getters: {
    /**
     * getDesigns: Getter that filters designs based on the current language.
     * 
     * Iterates over the designs and returns the appropriate title based on the selected language.
     * 
     * @param {Object} state - The current state of the store.
     * @returns {Array} - A list of designs with titles filtered by language.
     */
    getDesigns: (state) => {
      const languageStore = useLanguageStore(); // Access the language store

      return state.designs.map((design) => {
        return {
          ...design, // Keeps properties that are not text-based
          title: languageStore.currentLanguage === 'es' ? design.title_es : design.title_en,
        };
      });
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching designs data if it hasn't been updated yet.
     * 
     * This action ensures that the designs are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areUpdateDesigns) await this.fetchDesignsData();
    },

    /**
     * fetchDesignsData: Fetches designs data from the API.
     * 
     * This action makes an HTTP request to fetch the designs data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     */
    async fetchDesignsData() {
      if (this.areUpdateDesigns) return;

      let response = await get_request('api/web-designs/');
      let jsonData = response.data;

      if (jsonData && typeof jsonData === 'string') {
        try {
          jsonData = JSON.parse(jsonData);
        } catch (error) {
          console.error(error.message);
          jsonData = [];
        }
      }

      this.designs = jsonData ?? [];
      this.areUpdateDesigns = true;
    },
  },
});
