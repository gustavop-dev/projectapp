import { defineStore } from 'pinia';

export const useLanguageStore = defineStore("language", {
  /**
   * State of the Language store.
   * 
   * Properties:
   * - currentLanguage (String): Stores the current language code ('en' or 'es').
   * - messages (Object): Stores the loaded language messages for global and view-specific texts.
   */
  state: () => ({
    currentLanguage: '',  // Stores the current language code ('en' or 'es')
    messages: {},  // Stores the loaded language messages
  }),

  actions: {
    /**
     * Set the current language.
     * 
     * This action updates the `currentLanguage` state to the provided language code.
     * @param {string} language - The language code to set (e.g., 'en' or 'es').
     */
    setCurrentLanguage(language) {
      this.currentLanguage = language;
    },

    /**
     * Detect the browser's language preference.
     * 
     * This action detects the user's browser language and sets `currentLanguage` to 'es' if the language
     * starts with 'es', otherwise it defaults to 'en'. It also loads the corresponding global language messages.
     */
    async detectBrowserLanguage() {
      const userLang = navigator.language || navigator.userLanguage;
      this.currentLanguage = userLang.startsWith('es') ? 'es' : 'en';
      await this.loadMessages(this.currentLanguage);
    },

    /**
     * Load the global language messages.
     * 
     * This action dynamically imports the global language messages for the provided language code.
     * It is used to load common texts that are shared across the entire application.
     * 
     * @param {string} language - The language code ('en' or 'es').
     */
    async loadMessages(language) {
      const globalMessages = await import(`@/locales/global/${language}.js`);
      this.messages.global = globalMessages.default;
    },

    /**
     * Load language messages for a specific view.
     * 
     * This action dynamically imports the language messages for a specific view (page), based on the current language.
     * 
     * @param {string} view - The name of the view (e.g., 'home').
     */
    async loadMessagesForView(view) {
      const messages = await import(`@/locales/${view}/${this.currentLanguage}.js`);
      this.messages[view] = messages.default;
    },
  },

  getters: {
    /**
     * Get the language messages for a specific view.
     * 
     * This getter returns the language messages for a given view in the current language.
     * If no messages are available for the view, it returns an empty object.
     * 
     * @param {string} view - The view name (e.g., 'home').
     * @returns {object} - The language messages for the view in the current language.
     */
    getMessagesForView: (state) => (view) => {
      return state.messages[view] || {};
    },

    /**
     * Get the global language messages.
     * 
     * This getter returns the global language messages for a specific section in the current language.
     * If no messages are available for the section, it returns an empty object.
     * 
     * @param {string} section - The section name (e.g., 'navbar').
     * @returns {object} - The global language messages in the current language.
     */
    getGlobalMessages: (state) => (section) => {
      return state.messages.global?.[section] || {};
    },
  },
});

