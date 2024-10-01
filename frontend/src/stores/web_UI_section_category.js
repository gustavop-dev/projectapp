import { defineStore } from 'pinia';
import { get_request } from './services/request_http';
import { useLanguageStore } from '@/stores/language'; // Import the language store

export const useWebDevelopmentsStore = defineStore('web_UI_section_category', {
  /**
   * State of the WebDevelopments store.
   * 
   * Properties:
   * - developments (Array): Stores the list of developments with sections and components.
   * - areUpdateDevelopments (Boolean): Tracks if the developments data has been updated.
   */
  state: () => ({
    developments: [],
    areUpdateDevelopments: false,
  }),

  getters: {
    /**
     * getDevelopments: Getter that filters developments based on the current language.
     * 
     * Iterates over the developments, sections, and components, returning the appropriate title
     * and description fields based on the selected language.
     * 
     * @param {Object} state - The current state of the store.
     * @returns {Array} - A list of developments with titles and descriptions filtered by language.
     */
    getDevelopments: (state) => {
      const languageStore = useLanguageStore(); // Access the language store

      return state.developments.map((development) => {
        return {
          ...development,
          title: languageStore.currentLanguage === 'es' ? development.title_es : development.title_en,
          description: languageStore.currentLanguage === 'es' ? development.description_es : development.description_en,
          sections: development.sections.map((section) => ({
            ...section,
            title: languageStore.currentLanguage === 'es' ? section.title_es : section.title_en,
            components: section.components.map((component) => ({
              ...component,
              title: languageStore.currentLanguage === 'es' ? component.title_es : component.title_en,
              examples: component.examples.map((example) => ({
                ...example,
                title: languageStore.currentLanguage === 'es' ? example.title_es : example.title_en,
              })),
            })),
          })),
        };
      });
    },

    /**
     * getExamplesById: Getter that retrieves specific examples by their IDs, filtered by language.
     * 
     * This getter filters the data hierarchy (development -> section -> component -> examples) 
     * based on the provided IDs, and returns the appropriate titles according to the current language.
     * 
     * @param {Object} state - The current state of the store.
     * @param {Number} developmentId - The ID of the development.
     * @param {Number} sectionId - The ID of the section.
     * @param {Number} componentId - The ID of the component.
     * @returns {Object|null} - The filtered data for the given IDs, or null if not found.
     */
    getExamplesById: (state) => (developmentId, sectionId, componentId) => {
      const languageStore = useLanguageStore();
      const development = state.developments.find(dev => dev.id === parseInt(developmentId));
      if (!development) return null;

      const section = development.sections.find(sec => sec.id === parseInt(sectionId));
      if (!section) return null;

      const component = section.components.find(comp => comp.id === parseInt(componentId));
      if (!component) return null;

      return {
        development: {
          title: languageStore.currentLanguage === 'es' ? development.title_es : development.title_en,
        },
        section: {
          title: languageStore.currentLanguage === 'es' ? section.title_es : section.title_en,
        },
        component: {
          title: languageStore.currentLanguage === 'es' ? component.title_es : component.title_en,
        },
        examples: component.examples.map((example) => ({
          ...example,
          title: languageStore.currentLanguage === 'es' ? example.title_es : example.title_en,
        })),
      };
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching development data if it hasn't been updated yet.
     * 
     * This action ensures that the developments are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areUpdateDevelopments) await this.fetchDevelopmentsData();
    },

    /**
     * fetchDevelopmentsData: Fetches development data from the API.
     * 
     * This action makes an HTTP request to fetch the development categories data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     */
    async fetchDevelopmentsData() {
      if (this.areUpdateDevelopments) return;

      let response = await get_request('/ui_section_categories/');
      let jsonData = response.data;

      if (jsonData && typeof jsonData === 'string') {
        try {
          jsonData = JSON.parse(jsonData);
        } catch (error) {
          console.error(error.message);
          jsonData = [];
        }
      }

      this.developments = jsonData ?? [];
      this.areUpdateDevelopments = true;
    }
  }
});
