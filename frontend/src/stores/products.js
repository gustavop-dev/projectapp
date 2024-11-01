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
     * This method iterates over the products and their nested categories and items,
     * returning the appropriate title, description, and development time based on the selected language.
     * It also formats the price to the desired format.
     * 
     * @param {Object} state - The current state of the store.
     * @returns {Array} - A list of products with titles, descriptions, development times, and formatted prices.
     */
    getProducts: (state) => {
      const languageStore = useLanguageStore(); // Access the language store
      const currentLanguage = languageStore.currentLanguage;

      // Helper function to filter an object by language
      const filterByLanguage = (obj) => {
        let filteredObj = {};

        for (const key in obj) {
          if (key.endsWith('_en') || key.endsWith('_es')) {
            const baseKey = key.replace(/(_en|_es)$/, ''); // Remove the suffix
            filteredObj[baseKey] = obj[currentLanguage === 'es' ? `${baseKey}_es` : `${baseKey}_en`];
          } else if (typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
            filteredObj[key] = filterByLanguage(obj[key]);
          } else {
            filteredObj[key] = obj[key];
          }
        }

        return filteredObj;
      };

      // Helper function to format the price
      const formatPrice = (price) => {
        return new Intl.NumberFormat('es-CO', { style: 'decimal' }).format(price);
      };

      // Recursively filter the products, categories, and items
      return state.products.map((product) => {
        return {
          ...filterByLanguage(product),
          price: formatPrice(product.price), // Apply the price formatting
          categories: product.categories.map((category) => ({
            ...filterByLanguage(category),
            items: category.items.map((item) => filterByLanguage(item)),
          })),
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
