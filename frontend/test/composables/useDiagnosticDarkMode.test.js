/**
 * Tests for the useDiagnosticDarkMode composable.
 *
 * The composable mirrors usePlatformTheme: a module-scoped `isDark` ref,
 * `hydrate()` that reads localStorage with a prefers-color-scheme fallback,
 * and `toggle()` that persists `'dark'` / `'light'`. It also migrates the
 * legacy `'diagnostic-dark-mode'` boolean key on first hydrate.
 */

let useDiagnosticDarkMode;

const STORAGE_KEY = 'diagnostic_theme';
const LEGACY_KEY = 'diagnostic-dark-mode';

function mockMatchMedia(matches) {
  window.matchMedia = jest.fn().mockImplementation((query) => ({
    matches,
    media: query,
    onchange: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    addListener: jest.fn(),
    removeListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
}

beforeEach(() => {
  localStorage.clear();
  mockMatchMedia(false);
  jest.resetModules();
  jest.isolateModules(() => {
    useDiagnosticDarkMode = require('../../composables/useDiagnosticDarkMode').useDiagnosticDarkMode;
  });
});

afterEach(() => {
  localStorage.clear();
});

describe('useDiagnosticDarkMode', () => {
  describe('hydrate', () => {
    it('reads "dark" from localStorage', () => {
      localStorage.setItem(STORAGE_KEY, 'dark');
      const { isDark, hydrate } = useDiagnosticDarkMode();

      hydrate();

      expect(isDark.value).toBe(true);
    });

    it('reads "light" from localStorage', () => {
      localStorage.setItem(STORAGE_KEY, 'light');
      const { isDark, hydrate } = useDiagnosticDarkMode();
      isDark.value = true; // start dirty to prove hydrate sets it

      hydrate();

      expect(isDark.value).toBe(false);
    });

    it('falls back to prefers-color-scheme: dark when no stored value', () => {
      mockMatchMedia(true);
      const { isDark, hydrate } = useDiagnosticDarkMode();

      hydrate();

      expect(isDark.value).toBe(true);
    });

    it('falls back to light when system prefers light and no stored value', () => {
      mockMatchMedia(false);
      const { isDark, hydrate } = useDiagnosticDarkMode();
      isDark.value = true;

      hydrate();

      expect(isDark.value).toBe(false);
    });

    it('migrates legacy "true" boolean from old storage key', () => {
      localStorage.setItem(LEGACY_KEY, 'true');
      const { isDark, hydrate } = useDiagnosticDarkMode();

      hydrate();

      expect(isDark.value).toBe(true);
      expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');
      expect(localStorage.getItem(LEGACY_KEY)).toBeNull();
    });

    it('migrates legacy "false" boolean from old storage key', () => {
      localStorage.setItem(LEGACY_KEY, 'false');
      const { isDark, hydrate } = useDiagnosticDarkMode();
      isDark.value = true;

      hydrate();

      expect(isDark.value).toBe(false);
      expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
      expect(localStorage.getItem(LEGACY_KEY)).toBeNull();
    });

    it('prefers the new key over the legacy key when both are present', () => {
      localStorage.setItem(STORAGE_KEY, 'dark');
      localStorage.setItem(LEGACY_KEY, 'false');
      const { isDark, hydrate } = useDiagnosticDarkMode();

      hydrate();

      expect(isDark.value).toBe(true);
      expect(localStorage.getItem(LEGACY_KEY)).toBe('false');
    });

    it('does not throw if matchMedia is missing', () => {
      const original = window.matchMedia;
      delete window.matchMedia;
      const { hydrate } = useDiagnosticDarkMode();

      expect(() => hydrate()).not.toThrow();

      window.matchMedia = original;
    });
  });

  describe('toggle', () => {
    it('flips isDark and persists "dark" when turning on', () => {
      const { isDark, toggle } = useDiagnosticDarkMode();
      isDark.value = false;

      toggle();

      expect(isDark.value).toBe(true);
      expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');
    });

    it('flips isDark and persists "light" when turning off', () => {
      const { isDark, toggle } = useDiagnosticDarkMode();
      isDark.value = true;

      toggle();

      expect(isDark.value).toBe(false);
      expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
    });

    it('does not throw if localStorage.setItem fails', () => {
      const { toggle } = useDiagnosticDarkMode();
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = jest.fn(() => { throw new Error('quota'); });

      expect(() => toggle()).not.toThrow();

      Storage.prototype.setItem = original;
    });
  });

  describe('shared module state', () => {
    it('exposes the same isDark ref across calls so consumers stay in sync', () => {
      const a = useDiagnosticDarkMode();
      const b = useDiagnosticDarkMode();

      a.toggle();

      expect(b.isDark.value).toBe(a.isDark.value);
    });
  });
});
