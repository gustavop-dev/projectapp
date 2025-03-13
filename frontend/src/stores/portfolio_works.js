import { defineStore } from "pinia";
import { get_request } from "./services/request_http";
import { useLanguageStore } from "@/stores/language";

export const usePortfolioWorksStore = defineStore("portfolio_works", {
  /**
   * State of the PortfolioWorks store.
   *
   * Properties:
   * - portfolioWorks (Array): Stores the list of portfolio works.
   * - areUpdatePortfolioWorks (Boolean): Tracks if the portfolio works data has been updated.
   */
  state: () => ({
    portfolioWorks: [],
    areUpdatePortfolioWorks: false,
  }),

  getters: {
    /**
     * getFilteredPortfolioWorksAndCategories: Getter that filters portfolio works based on the current language
     * and returns both the filtered works and the unique categories.
     *
     * It first applies a language-based filter to the works and then extracts unique categories from the filtered works.
     *
     * @param {Object} state - The current state of the store.
     * @returns {Object} - An object containing:
     *  - portfolioWorks: An array of portfolio works filtered by language.
     *  - categories: An array of unique category titles filtered by language.
     */
    getFilteredPortfolioWorksAndCategories: (state) => {
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

      // Step 1: Filter portfolio works based on the language
      const filteredPortfolioWorks = state.portfolioWorks.map((work) =>
        filterByLanguage(work)
      );

      // Step 2: Extract unique categories from the filtered portfolio works
      const categories = [
        ...new Set(filteredPortfolioWorks.map((work) => work.category_title)),
      ];

      // Return an object with both filtered portfolio works and unique categories
      return {
        portfolioWorks: filteredPortfolioWorks, // Filtered portfolio works
        categories: categories, // Unique categories
      };
    },
    
    /**
     * getFilteredByCategory: Getter that filters the passed portfolio works by the selected category.
     *
     * @param {Object} state - The current state of the store.
     * @returns {Function} - A function that accepts a list of portfolio works and a category,
     * and returns the works filtered by that category.
     */
    getFilteredByCategory: (state) => (portfolioWorks, selectedCategory) => {
      // If "All" is selected, return the entire list of portfolio works
      if (selectedCategory === "All") {
        return portfolioWorks;
      }

      // Otherwise, filter by the selected category
      return portfolioWorks.filter(
        (work) => work.category_title === selectedCategory
      );
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching portfolio works data if it hasn't been updated yet.
     *
     * This action ensures that the portfolio works are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areUpdatePortfolioWorks) await this.fetchPortfolioWorksData();
    },

    /**
     * fetchPortfolioWorksData: Fetches portfolio works data from the API.
     *
     * This action makes an HTTP request to fetch the portfolio works data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     */
    async fetchPortfolioWorksData() {
      if (this.areUpdatePortfolioWorks) return;

      try {
        let response = await get_request("/portfolio_works/");
        let jsonData = response.data;

        if (jsonData && typeof jsonData === "string") {
          try {
            jsonData = JSON.parse(jsonData);
          } catch (error) {
            console.error("Error parsing portfolio works data:", error.message);
            jsonData = [];
          }
        }

        this.portfolioWorks = jsonData ?? [];
        this.areUpdatePortfolioWorks = true;
      } catch (error) {
        console.error("Error fetching portfolio works:", error);
        this.portfolioWorks = [];
      }
    },
  },
});