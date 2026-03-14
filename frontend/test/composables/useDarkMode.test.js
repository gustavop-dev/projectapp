/**
 * Tests for the useDarkMode composable.
 *
 * Covers: toggle, applyTheme (dark/light/SSR), watch persistence,
 * onMounted restore from localStorage, matchMedia fallback, error handling.
 */

const mockMountedCbs = [];
const mockWatchCbs = [];

jest.mock('vue', () => {
  const actualVue = jest.requireActual('vue');
  return {
    ...actualVue,
    onMounted: jest.fn((cb) => { mockMountedCbs.push(cb); }),
    watch: jest.fn((source, cb) => { mockWatchCbs.push({ source, cb }); }),
  };
});

let useDarkMode;

beforeEach(() => {
  mockMountedCbs.length = 0;
  mockWatchCbs.length = 0;
  localStorage.clear();
  document.documentElement.classList.remove('dark');
  jest.resetModules();
  jest.isolateModules(() => {
    useDarkMode = require('../../composables/useDarkMode').useDarkMode;
  });
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove('dark');
});

describe('useDarkMode', () => {
  describe('toggle', () => {
    it('flips isDark from false to true', () => {
      const { isDark, toggle } = useDarkMode();

      expect(isDark.value).toBe(false);
      toggle();
      expect(isDark.value).toBe(true);
    });

    it('flips isDark from true to false', () => {
      const { isDark, toggle } = useDarkMode();

      isDark.value = true;
      toggle();
      expect(isDark.value).toBe(false);
    });
  });

  describe('applyTheme via watch', () => {
    it('adds dark class when value is true', () => {
      useDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(true);

      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('removes dark class when value is false', () => {
      document.documentElement.classList.add('dark');
      useDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(false);

      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('persists true to localStorage', () => {
      useDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(true);

      expect(localStorage.getItem('projectapp-dark-mode')).toBe('true');
    });

    it('persists false to localStorage', () => {
      useDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(false);

      expect(localStorage.getItem('projectapp-dark-mode')).toBe('false');
    });

    it('handles localStorage setItem error gracefully', () => {
      useDarkMode();
      const { cb } = mockWatchCbs[0];

      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = jest.fn(() => { throw new Error('quota'); });

      expect(() => cb(true)).not.toThrow();

      Storage.prototype.setItem = original;
    });
  });

  describe('onMounted — restore from localStorage', () => {
    it('restores dark mode from stored true value', () => {
      localStorage.setItem('projectapp-dark-mode', 'true');
      const { isDark } = useDarkMode();

      mockMountedCbs[0]();

      expect(isDark.value).toBe(true);
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('restores light mode from stored false value', () => {
      localStorage.setItem('projectapp-dark-mode', 'false');
      const { isDark } = useDarkMode();
      isDark.value = true;

      mockMountedCbs[0]();

      expect(isDark.value).toBe(false);
    });

    it('falls back to matchMedia system preference when no stored value', () => {
      const mockMatchMedia = jest.fn(() => ({ matches: true }));
      Object.defineProperty(window, 'matchMedia', { value: mockMatchMedia, writable: true });

      const { isDark } = useDarkMode();

      mockMountedCbs[0]();

      expect(isDark.value).toBe(true);
      expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)');
    });

    it('defaults to false when matchMedia returns no match', () => {
      Object.defineProperty(window, 'matchMedia', {
        value: jest.fn(() => ({ matches: false })),
        writable: true,
      });
      const { isDark } = useDarkMode();

      mockMountedCbs[0]();

      expect(isDark.value).toBe(false);
    });

    it('handles localStorage getItem error gracefully', () => {
      const original = Storage.prototype.getItem;
      Storage.prototype.getItem = jest.fn(() => { throw new Error('access denied'); });

      const { isDark } = useDarkMode();

      expect(() => mockMountedCbs[0]()).not.toThrow();
      expect(isDark.value).toBe(false);

      Storage.prototype.getItem = original;
    });

    it('applies theme after restoring value', () => {
      localStorage.setItem('projectapp-dark-mode', 'true');
      useDarkMode();

      mockMountedCbs[0]();

      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
  });

  describe('applyTheme SSR guard', () => {
    it('does not throw when document is undefined', () => {
      const originalDocument = global.document;
      delete global.document;

      useDarkMode();
      const { cb } = mockWatchCbs[0];

      expect(() => cb(true)).not.toThrow();

      global.document = originalDocument;
    });
  });
});
