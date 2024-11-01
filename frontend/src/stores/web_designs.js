import { defineStore } from "pinia";
import { get_request } from "./services/request_http";
import { useLanguageStore } from "@/stores/language"; // Import the language store

export const useWebDesignsStore = defineStore("web_designs", {
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
     * getFilteredDesignsAndCategories: Getter that filters designs based on the current language
     * and returns both the filtered designs and the unique categories.
     *
     * It first applies a language-based filter to the designs and then extracts unique categories from the filtered designs.
     *
     * @param {Object} state - The current state of the store.
     * @returns {Object} - An object containing:
     *  - designs: An array of designs filtered by language.
     *  - categories: An array of unique category titles filtered by language.
     */
    getFilteredDesignsAndCategories: (state) => {
      const languageStore = useLanguageStore(); // Access the language store
      const currentLanguage = languageStore.currentLanguage;

      /**
       * filterByLanguage: Helper function that filters the object's properties based on the selected language.
       * It removes '_en' and '_es' suffixes and keeps the property relevant to the current language.
       *
       * @param {Object} obj - The object to be filtered.
       * @returns {Object} - A filtered object with properties in the correct language.
       */
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

      // Step 1: Filter designs based on the language
      const filteredDesigns = state.designs.map((design) =>
        filterByLanguage(design)
      );

      // Step 2: Extract unique categories from the filtered designs
      const categories = [
        ...new Set(filteredDesigns.map((design) => design.category_title)),
      ];

      // Return an object with both filtered designs and unique categories
      return {
        designs: filteredDesigns, // Filtered designs
        categories: categories, // Unique categories
      };
    },
    /**
     * getFilteredByCategory: Getter that filters the passed designs by the selected category.
     *
     * @param {Object} state - The current state of the store.
     * @returns {Function} - A function that accepts a list of designs and a category,
     * and returns the designs filtered by that category.
     */
    getFilteredByCategory: (state) => (designs, selectedCategory) => {
      // If "All" is selected, return the entire list of designs
      if (selectedCategory === "All") {
        return designs;
      }

      // Otherwise, filter by the selected category
      return designs.filter(
        (design) => design.category_title === selectedCategory
      );
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

      let response = await get_request("/designs/");
      let jsonData = response.data;

      if (jsonData && typeof jsonData === "string") {
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
