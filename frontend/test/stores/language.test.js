/**
 * Tests for the language store.
 *
 * Covers: setCurrentLanguage, setCurrentRegion, setCurrentLocale,
 * detectBrowserLanguageAndRegion, loadMessages, loadMessagesForView,
 * getters: getMessagesForView, getGlobalMessages, getLocalePrefix,
 * isSpanishColombia, isEnglishUS.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useLanguageStore } from '../../stores/language';

describe('useLanguageStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useLanguageStore();
  });

  describe('initial state', () => {
    it('has empty currentLanguage', () => {
      expect(store.currentLanguage).toBe('');
    });

    it('has empty currentRegion', () => {
      expect(store.currentRegion).toBe('');
    });

    it('has empty currentLocale', () => {
      expect(store.currentLocale).toBe('');
    });

    it('has empty messages object', () => {
      expect(store.messages).toEqual({});
    });
  });

  describe('setCurrentLanguage', () => {
    it('sets language to es', () => {
      store.setCurrentLanguage('es');
      expect(store.currentLanguage).toBe('es');
    });

    it('sets language to en', () => {
      store.setCurrentLanguage('en');
      expect(store.currentLanguage).toBe('en');
    });
  });

  describe('setCurrentRegion', () => {
    it('sets region to co', () => {
      store.setCurrentRegion('co');
      expect(store.currentRegion).toBe('co');
    });

    it('sets region to us', () => {
      store.setCurrentRegion('us');
      expect(store.currentRegion).toBe('us');
    });
  });

  describe('setCurrentLocale', () => {
    it('sets locale and splits into language and region', () => {
      store.setCurrentLocale('es-co');
      expect(store.currentLocale).toBe('es-co');
      expect(store.currentLanguage).toBe('es');
      expect(store.currentRegion).toBe('co');
    });

    it('handles en-us locale', () => {
      store.setCurrentLocale('en-us');
      expect(store.currentLocale).toBe('en-us');
      expect(store.currentLanguage).toBe('en');
      expect(store.currentRegion).toBe('us');
    });
  });

  describe('detectBrowserLanguageAndRegion', () => {
    it('sets locale to en-us and loads English messages', async () => {
      jest.spyOn(store, 'loadMessages').mockResolvedValue();

      await store.detectBrowserLanguageAndRegion();

      expect(store.currentLocale).toBe('en-us');
      expect(store.currentLanguage).toBe('en');
      expect(store.currentRegion).toBe('us');
      expect(store.loadMessages).toHaveBeenCalledWith('en');

      store.loadMessages.mockRestore();
    });

    it('uses stored preference from localStorage when available', async () => {
      jest.spyOn(store, 'loadMessages').mockResolvedValue();
      localStorage.setItem('preferred_locale', 'es-co');

      await store.detectBrowserLanguageAndRegion();

      expect(store.currentLocale).toBe('es-co');
      expect(store.loadMessages).toHaveBeenCalledWith('es');

      localStorage.removeItem('preferred_locale');
      store.loadMessages.mockRestore();
    });

    it('uses stored en-us preference from localStorage', async () => {
      jest.spyOn(store, 'loadMessages').mockResolvedValue();
      localStorage.setItem('preferred_locale', 'en-us');

      await store.detectBrowserLanguageAndRegion();

      expect(store.currentLocale).toBe('en-us');
      expect(store.loadMessages).toHaveBeenCalledWith('en');

      localStorage.removeItem('preferred_locale');
      store.loadMessages.mockRestore();
    });

    it('ignores invalid stored preference', async () => {
      jest.spyOn(store, 'loadMessages').mockResolvedValue();
      localStorage.setItem('preferred_locale', 'fr-fr');

      await store.detectBrowserLanguageAndRegion();

      expect(store.currentLocale).not.toBe('fr-fr');

      localStorage.removeItem('preferred_locale');
      store.loadMessages.mockRestore();
    });

    it('defaults to en-us when navigator.language is empty', async () => {
      jest.spyOn(store, 'loadMessages').mockResolvedValue();
      const origLanguage = navigator.language;
      Object.defineProperty(navigator, 'language', { value: '', writable: true });

      await store.detectBrowserLanguageAndRegion();

      expect(store.currentLocale).toBe('en-us');

      Object.defineProperty(navigator, 'language', { value: origLanguage, writable: true });
      store.loadMessages.mockRestore();
    });

    it('detects Spanish browser language and sets es-co', async () => {
      jest.spyOn(store, 'loadMessages').mockResolvedValue();
      const origLanguage = navigator.language;
      Object.defineProperty(navigator, 'language', { value: 'es-MX', writable: true });

      await store.detectBrowserLanguageAndRegion();

      expect(store.currentLocale).toBe('es-co');
      expect(store.currentLanguage).toBe('es');
      expect(store.loadMessages).toHaveBeenCalledWith('es');

      Object.defineProperty(navigator, 'language', { value: origLanguage, writable: true });
      store.loadMessages.mockRestore();
    });
  });

  describe('detectBrowserLanguage', () => {
    it('delegates to detectBrowserLanguageAndRegion', async () => {
      jest.spyOn(store, 'detectBrowserLanguageAndRegion').mockResolvedValue();

      await store.detectBrowserLanguage();

      expect(store.detectBrowserLanguageAndRegion).toHaveBeenCalled();

      store.detectBrowserLanguageAndRegion.mockRestore();
    });
  });

  describe('loadMessages', () => {
    it('loads global messages for the given language', async () => {
      await store.loadMessages('en');

      expect(store.messages.global).toBeDefined();
    });
  });

  describe('loadMessagesForView', () => {
    it('loads view-specific messages using currentLanguage', async () => {
      store.currentLanguage = 'en';

      await store.loadMessagesForView('home');

      expect(store.messages.home).toBeDefined();
    });
  });

  describe('getters', () => {
    it('getMessagesForView returns messages for loaded view', () => {
      store.messages = { home: { title: 'Welcome' } };
      expect(store.getMessagesForView('home')).toEqual({ title: 'Welcome' });
    });

    it('getMessagesForView returns empty object for missing view', () => {
      expect(store.getMessagesForView('missing')).toEqual({});
    });

    it('getGlobalMessages returns section messages', () => {
      store.messages = { global: { navbar: { home: 'Home' } } };
      expect(store.getGlobalMessages('navbar')).toEqual({ home: 'Home' });
    });

    it('getGlobalMessages returns empty object for missing section', () => {
      store.messages = { global: {} };
      expect(store.getGlobalMessages('missing')).toEqual({});
    });

    it('getGlobalMessages returns empty object when global is undefined', () => {
      expect(store.getGlobalMessages('navbar')).toEqual({});
    });

    it('getLocalePrefix returns locale path when set', () => {
      store.currentLocale = 'es-co';
      expect(store.getLocalePrefix).toBe('/es-co');
    });

    it('getLocalePrefix returns empty string when no locale', () => {
      expect(store.getLocalePrefix).toBe('');
    });

    it('isSpanishColombia returns true for es-co', () => {
      store.currentLocale = 'es-co';
      expect(store.isSpanishColombia).toBe(true);
    });

    it('isSpanishColombia returns false for en-us', () => {
      store.currentLocale = 'en-us';
      expect(store.isSpanishColombia).toBe(false);
    });

    it('isEnglishUS returns true for en-us', () => {
      store.currentLocale = 'en-us';
      expect(store.isEnglishUS).toBe(true);
    });

    it('isEnglishUS returns false for es-co', () => {
      store.currentLocale = 'es-co';
      expect(store.isEnglishUS).toBe(false);
    });
  });
});
