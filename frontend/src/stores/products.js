import { defineStore } from 'pinia';
import { get_request } from './services/request_http';
import { useLanguageStore } from '@/stores/language'; // Import the language store

export const useProductStore = defineStore('products', {
  /**
   * State of the Product store.
   * 
   * Properties:
   * - products (Array): Stores the list of products.
   * - areProductsUpdated (Boolean): Tracks if the product data has been updated.
   */
  state: () => ({
    products: [],
    areProductsUpdated: false,
  }),

  getters: {
    /**
     * getProducts: Getter that filters products based on the current language.
     * 
     * Iterates over the products and returns the appropriate title, description, and development time
     * based on the selected language.
     * 
     * @param {Object} state - The current state of the store.
     * @returns {Array} - A list of products with titles, descriptions, and development times filtered by language.
     */
    getProducts: (state) => {
      const languageStore = useLanguageStore(); // Access the language store

      return state.products.map((product) => {
        return {
          ...product, // Keeps properties that are not text-based
          title: languageStore.currentLanguage === 'es' ? product.title_es : product.title_en,
          description: languageStore.currentLanguage === 'es' ? product.description_es : product.description_en,
          development_time: languageStore.currentLanguage === 'es' ? product.development_time_es : product.development_time_en,
        };
      });
    },
  },

  actions: {
    /**
     * init: Initializes the store by fetching product data if it hasn't been updated yet.
     * 
     * This action ensures that the products are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areProductsUpdated) {
        await this.fetchProductData();
      }
    },

    /**
     * fetchProductData: Fetches product data from the API.
     * 
     * This action makes an HTTP request to fetch the product data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     * 
     * In case of errors during the API request or JSON parsing, it logs the error to the console.
     */
    async fetchProductData() {
      if (this.areProductsUpdated) return;
      try {
        let response = await get_request('/products/');
        let jsonData = response.data;

        if (jsonData && typeof jsonData === 'string') {
          try {
            jsonData = JSON.parse(jsonData);
          } catch (error) {
            console.error(error.message);
            jsonData = [];
          }
        }

        this.products = jsonData ?? [];
        this.areProductsUpdated = true;
      } catch (error) {
        console.error('Error fetching products:', error);
      }
    }
  }
});
