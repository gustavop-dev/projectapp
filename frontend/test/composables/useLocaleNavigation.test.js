/**
 * Tests for the useLocaleNavigation composable.
 *
 * Covers: navigateToRoute, switchLocale, getLocaleUrl,
 * isActiveLocale, currentBaseRouteName, availableLocales.
 */
import { ref } from 'vue';

let mockRouterPush;
let mockLocalePath;
let mockSwitchLocalePath;
let mockLocale;
let mockRouteName;
let useLocaleNavigation;

beforeEach(() => {
  mockRouterPush = jest.fn();
  mockLocalePath = jest.fn((path) => `/en-us${typeof path === 'string' ? path : ''}`);
  mockSwitchLocalePath = jest.fn((locale) => `/${locale}/current-page`);
  mockLocale = ref('en-us');
  mockRouteName = 'index___en-us';

  global.useI18n = () => ({
    locale: mockLocale,
    locales: ref([{ code: 'es-co' }, { code: 'en-us' }]),
  });
  global.useSwitchLocalePath = () => mockSwitchLocalePath;
  global.useLocalePath = () => mockLocalePath;
  global.useRouter = () => ({ push: mockRouterPush, replace: jest.fn(), back: jest.fn() });
  global.useRoute = () => ({ name: mockRouteName, params: {}, query: {}, path: '/', fullPath: '/' });

  jest.resetModules();
  const mod = require('../../composables/useLocaleNavigation');
  useLocaleNavigation = mod.useLocaleNavigation;
});

describe('useLocaleNavigation', () => {
  describe('navigateToRoute', () => {
    it('navigates to a legacy route name', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('home');

      expect(mockLocalePath).toHaveBeenCalledWith('/');
      expect(mockRouterPush).toHaveBeenCalledWith({ path: expect.any(String), query: {} });
    });

    it('navigates to aboutUs with correct path mapping', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('aboutUs');

      expect(mockLocalePath).toHaveBeenCalledWith('/about-us');
    });

    it('falls back to /<routeName> for unknown routes', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('custom-page');

      expect(mockLocalePath).toHaveBeenCalledWith('/custom-page');
    });

    it('appends params to the path', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('hosting', { plan: 'pro' });

      expect(mockLocalePath).toHaveBeenCalledWith('/hosting/pro');
    });

    it('passes query parameters', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('contact', {}, { ref: 'banner' });

      expect(mockRouterPush).toHaveBeenCalledWith(expect.objectContaining({ query: { ref: 'banner' } }));
    });

    it('ignores empty params', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('home', {});

      expect(mockLocalePath).toHaveBeenCalledWith('/');
    });

    it('filters out falsy param values', () => {
      const { navigateToRoute } = useLocaleNavigation();

      navigateToRoute('hosting', { plan: null, tier: '' });

      expect(mockLocalePath).toHaveBeenCalledWith('/hosting');
    });
  });

  describe('switchLocale', () => {
    it('pushes the switch locale path to router', () => {
      const { switchLocale } = useLocaleNavigation();

      switchLocale('es-co');

      expect(mockSwitchLocalePath).toHaveBeenCalledWith('es-co');
      expect(mockRouterPush).toHaveBeenCalledWith('/es-co/current-page');
    });

    it('does not push when switchLocalePath returns falsy', () => {
      mockSwitchLocalePath.mockReturnValue('');
      const { switchLocale } = useLocaleNavigation();

      switchLocale('es-co');

      expect(mockRouterPush).not.toHaveBeenCalled();
    });

    it('handles localStorage setItem error gracefully', () => {
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = jest.fn(() => { throw new Error('quota'); });
      const { switchLocale } = useLocaleNavigation();

      expect(() => switchLocale('es-co')).not.toThrow();
      expect(mockRouterPush).toHaveBeenCalled();

      Storage.prototype.setItem = original;
    });

    it('persists target locale in localStorage', () => {
      const { switchLocale } = useLocaleNavigation();

      switchLocale('es-co');

      expect(localStorage.getItem('preferred_locale')).toBe('es-co');
    });

    it('silently handles localStorage setItem errors', () => {
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = jest.fn(() => { throw new Error('quota'); });
      try {
        const { switchLocale } = useLocaleNavigation();

        expect(() => switchLocale('es-co')).not.toThrow();
        expect(mockRouterPush).toHaveBeenCalledWith('/es-co/current-page');
      } finally {
        Storage.prototype.setItem = original;
      }
    });
  });

  describe('getLocaleUrl', () => {
    it('returns locale-aware URL for a route', () => {
      const { getLocaleUrl } = useLocaleNavigation();

      getLocaleUrl('about-us');

      expect(mockLocalePath).toHaveBeenCalledWith({ name: 'about-us', params: {} }, 'en-us');
    });

    it('uses target locale when provided', () => {
      const { getLocaleUrl } = useLocaleNavigation();

      getLocaleUrl('contact', {}, 'es-co');

      expect(mockLocalePath).toHaveBeenCalledWith({ name: 'contact', params: {} }, 'es-co');
    });
  });

  describe('isActiveLocale', () => {
    it('returns true for current locale', () => {
      const { isActiveLocale } = useLocaleNavigation();

      expect(isActiveLocale('en-us')).toBe(true);
    });

    it('returns false for different locale', () => {
      const { isActiveLocale } = useLocaleNavigation();

      expect(isActiveLocale('es-co')).toBe(false);
    });
  });

  describe('currentBaseRouteName', () => {
    it('strips locale suffix from route name', () => {
      mockRouteName = 'about-us___en-us';
      jest.resetModules();
      const mod = require('../../composables/useLocaleNavigation');
      const { currentBaseRouteName } = mod.useLocaleNavigation();

      expect(currentBaseRouteName.value).toBe('about-us');
    });

    it('returns null for undefined route name', () => {
      mockRouteName = undefined;
      jest.resetModules();
      const mod = require('../../composables/useLocaleNavigation');
      const { currentBaseRouteName } = mod.useLocaleNavigation();

      expect(currentBaseRouteName.value).toBeNull();
    });

    it('returns null for non-string route name', () => {
      mockRouteName = 123;
      jest.resetModules();
      const mod = require('../../composables/useLocaleNavigation');
      const { currentBaseRouteName } = mod.useLocaleNavigation();

      expect(currentBaseRouteName.value).toBeNull();
    });
  });

  describe('availableLocales', () => {
    it('returns both locale options', () => {
      const { availableLocales } = useLocaleNavigation();

      expect(availableLocales.value).toHaveLength(2);
      expect(availableLocales.value[0].code).toBe('es-co');
      expect(availableLocales.value[1].code).toBe('en-us');
    });
  });
});
