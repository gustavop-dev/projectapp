import { defineStore } from 'pinia';
import { get_request, create_request } from './services/request_http';

export const useContactsStore = defineStore('contacts', {
  /**
   * State of the Contacts store.
   * 
   * Properties:
   * - contacts (Array): Stores the list of contacts.
   * - areUpdateContacts (Boolean): Tracks if the contact data has been updated.
   * - isSubmitting (Boolean): Tracks if a form submission is in progress.
   * - submitError (String|null): Stores any error message from submission.
   * - submitSuccess (Boolean): Tracks if the last submission was successful.
   */
  state: () => ({
    contacts: [],
    areUpdateContacts: false,
    isSubmitting: false,
    submitError: null,
    submitSuccess: false,
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
    },

    /**
     * sendContact: Sends contact form data to the API.
     * 
     * @param {Object} formData - The form data to send
     * @param {string} formData.fullName - Full name (used as subject)
     * @param {string} formData.email - Email address (required)
     * @param {string} formData.phone - Phone number (optional)
     * @param {string} formData.project - Project description (used as message, required)
     * @param {string} formData.budget - Budget range (optional)
     * @returns {Promise<Object>} Response data from the API
     */
    async sendContact(formData) {
      this.isSubmitting = true;
      this.submitError = null;
      this.submitSuccess = false;

      try {
        const payload = {
          email: formData.email,
          phone_number: formData.phone || null,
          subject: formData.fullName,
          message: formData.project,
          budget: formData.budget || null
        };

        const response = await create_request('new-contact/', payload);
        
        this.submitSuccess = true;
        this.isSubmitting = false;
        
        return {
          success: true,
          data: response.data
        };
      } catch (error) {
        this.isSubmitting = false;
        this.submitSuccess = false;
        
        if (error.response && error.response.data) {
          this.submitError = error.response.data;
        } else {
          this.submitError = 'Error al enviar el formulario. Por favor intenta de nuevo.';
        }
        
        console.error('Error sending contact form:', error);
        
        return {
          success: false,
          error: this.submitError
        };
      }
    },

    /**
     * resetSubmitState: Resets the submission state flags.
     */
    resetSubmitState() {
      this.submitError = null;
      this.submitSuccess = false;
      this.isSubmitting = false;
    }
  }
});
