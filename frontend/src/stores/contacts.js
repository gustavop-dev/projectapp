import { defineStore } from 'pinia';
import { get_request } from './services/request_http';

export const useContactsStore = defineStore('contacts', {
  /**
   * State of the Contacts store.
   * 
   * Properties:
   * - contacts (Array): Stores the list of contacts.
   * - areUpdateContacts (Boolean): Tracks if the contact data has been updated.
   */
  state: () => ({
    contacts: [],
    areUpdateContacts: false,
  }),

  getters: {

  },

  actions: {
    /**
     * init: Initializes the store by fetching contacts data if it hasn't been updated yet.
     * 
     * This action ensures that the contacts are fetched only once, avoiding redundant requests.
     */
    async init() {
      if (!this.areUpdateContacts) {
        await this.fetchContactsData();
      }
    },

    /**
     * fetchContactsData: Fetches contacts data from the API.
     * 
     * This action makes an HTTP request to fetch the contacts data and updates
     * the state with the fetched data. It also handles potential JSON parsing errors.
     * 
     * In case of errors during the API request or JSON parsing, it logs the error to the console.
     */
    async fetchContactsData() {
      if (this.areUpdateContacts) return;
      try {
        let response = await get_request('/contacts/');
        let jsonData = response.data;

        if (jsonData && typeof jsonData === 'string') {
          try {
            jsonData = JSON.parse(jsonData);
          } catch (error) {
            console.error(error.message);
            jsonData = [];
          }
        }

        this.contacts = jsonData ?? [];
        this.areUpdateContacts = true;
      } catch (error) {
        console.error('Error fetching contacts:', error);
      }
    }
  }
});
