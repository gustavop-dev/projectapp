import { defineStore } from 'pinia';

export const useLanguageStore = defineStore("language", {
  /**
   * State of the Language store.
   * 
   * Properties:
   * - currentLanguage (String): Stores the current language code ('en' or 'es').
   * - currentRegion (String): Stores the current region code ('co' or 'us').
   * - currentLocale (String): Stores the full locale code ('es-co' or 'en-us').
   * - messages (Object): Stores the loaded language messages for global and view-specific texts.
   */
  state: () => ({
    currentLanguage: '',  // Stores the current language code ('en' or 'es')
    currentRegion: '',    // Stores the current region code ('co' or 'us')
    currentLocale: '',    // Stores the full locale code ('es-co' or 'en-us')
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
     * Set the current region.
     * 
     * This action updates the `currentRegion` state to the provided region code.
     * @param {string} region - The region code to set (e.g., 'co' or 'us').
     */
    setCurrentRegion(region) {
      this.currentRegion = region;
    },

    /**
     * Set the current locale (language + region).
     * 
     * This action updates the locale and splits it into language and region components.
     * @param {string} locale - The full locale to set (e.g., 'es-co' or 'en-us').
     */
    setCurrentLocale(locale) {
      const [language, region] = locale.split('-');
      this.currentLocale = locale;
      this.currentLanguage = language;
      this.currentRegion = region;
    },

    /**
     * Initialize language to default (en-us).
     * 
     * Always defaults to English (en-us). Language can only be changed manually by the user.
     */
    async detectBrowserLanguageAndRegion() {
      // Always default to English (en-us)
      const locale = 'en-us';
      this.setCurrentLocale(locale);
      await this.loadMessages('en');
    },

    /**
     * Detect the browser's language preference (legacy method for backwards compatibility).
     * 
     * This action detects the user's browser language and sets `currentLanguage` to 'es' if the language
     * starts with 'es', otherwise it defaults to 'en'. It also loads the corresponding global language messages.
     */
    async detectBrowserLanguage() {
      await this.detectBrowserLanguageAndRegion();
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
      const globalMessages = await import(`~/locales/global/${language}.js`);
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
      const messages = await import(`~/locales/${view}/${this.currentLanguage}.js`);
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

    /**
     * Get the current locale path prefix.
     * 
     * This getter returns the locale prefix for URL routing (e.g., '/es-co' or '/en-us').
     * @returns {string} - The locale prefix for routing.
     */
    getLocalePrefix: (state) => {
      return state.currentLocale ? `/${state.currentLocale}` : '';
    },

    /**
     * Check if the current locale is Spanish Colombia.
     * @returns {boolean} - True if current locale is es-co.
     */
    isSpanishColombia: (state) => {
      return state.currentLocale === 'es-co';
    },

    /**
     * Check if the current locale is English US.
     * @returns {boolean} - True if current locale is en-us.
     */
    isEnglishUS: (state) => {
      return state.currentLocale === 'en-us';
    },
  },
});

