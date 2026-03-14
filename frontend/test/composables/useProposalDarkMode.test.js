/**
 * Tests for the useProposalDarkMode composable.
 *
 * Covers: toggle, applyTheme (dark/light/SSR), watch persistence,
 * onMounted theme reapplication, and regression for dark mode
 * not resetting on component remount.
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

let useProposalDarkMode;

beforeEach(() => {
  mockMountedCbs.length = 0;
  mockWatchCbs.length = 0;
  localStorage.clear();
  // Clean up any data-proposal-wrapper elements
  document.querySelectorAll('[data-proposal-wrapper]').forEach(el => el.remove());
  jest.resetModules();
  jest.isolateModules(() => {
    useProposalDarkMode = require('../../composables/useProposalDarkMode').useProposalDarkMode;
  });
});

afterEach(() => {
  localStorage.clear();
  document.querySelectorAll('[data-proposal-wrapper]').forEach(el => el.remove());
});

/** Helper: creates a wrapper element with [data-proposal-wrapper] in the DOM */
function createWrapper() {
  const el = document.createElement('div');
  el.setAttribute('data-proposal-wrapper', '');
  document.body.appendChild(el);
  return el;
}

describe('useProposalDarkMode', () => {
  describe('toggle', () => {
    it('flips isDark from false to true', () => {
      const { isDark, toggle } = useProposalDarkMode();

      expect(isDark.value).toBe(false);
      toggle();
      expect(isDark.value).toBe(true);
    });

    it('flips isDark from true to false', () => {
      const { isDark, toggle } = useProposalDarkMode();

      isDark.value = true;
      toggle();
      expect(isDark.value).toBe(false);
    });
  });

  describe('applyTheme', () => {
    it('sets data-theme to dark on wrapper element', () => {
      const wrapper = createWrapper();
      const { applyTheme } = useProposalDarkMode();

      applyTheme(true);

      expect(wrapper.getAttribute('data-theme')).toBe('dark');
    });

    it('sets data-theme to light on wrapper element', () => {
      const wrapper = createWrapper();
      const { applyTheme } = useProposalDarkMode();

      applyTheme(false);

      expect(wrapper.getAttribute('data-theme')).toBe('light');
    });

    it('does not throw when no wrapper element exists', () => {
      const { applyTheme } = useProposalDarkMode();

      expect(() => applyTheme(true)).not.toThrow();
    });
  });

  describe('watch persistence', () => {
    it('persists true to localStorage when isDark changes', () => {
      useProposalDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(true);

      expect(localStorage.getItem('proposal-dark-mode')).toBe('true');
    });

    it('persists false to localStorage when isDark changes', () => {
      useProposalDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(false);

      expect(localStorage.getItem('proposal-dark-mode')).toBe('false');
    });

    it('applies dark theme via watch callback', () => {
      const wrapper = createWrapper();
      useProposalDarkMode();
      const { cb } = mockWatchCbs[0];

      cb(true);

      expect(wrapper.getAttribute('data-theme')).toBe('dark');
    });

    it('handles localStorage setItem error gracefully', () => {
      useProposalDarkMode();
      const { cb } = mockWatchCbs[0];

      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = jest.fn(() => { throw new Error('quota'); });

      expect(() => cb(true)).not.toThrow();

      Storage.prototype.setItem = original;
    });
  });

  describe('onMounted — theme reapplication', () => {
    it('applies light theme on initial mount when isDark is false', () => {
      const wrapper = createWrapper();
      useProposalDarkMode();

      mockMountedCbs[0]();

      expect(wrapper.getAttribute('data-theme')).toBe('light');
    });

    it('applies dark theme on mount when isDark is true', () => {
      const wrapper = createWrapper();
      const { isDark } = useProposalDarkMode();
      isDark.value = true;

      mockMountedCbs[0]();

      expect(wrapper.getAttribute('data-theme')).toBe('dark');
    });

    it('does not reset isDark to false on mount (regression)', () => {
      const { isDark } = useProposalDarkMode();
      isDark.value = true;

      mockMountedCbs[0]();

      expect(isDark.value).toBe(true);
    });

    it('preserves dark mode when a second consumer mounts (regression)', () => {
      const wrapper = createWrapper();
      const { isDark } = useProposalDarkMode();

      // Simulate user toggling dark mode
      isDark.value = true;
      const watchCb = mockWatchCbs[0].cb;
      watchCb(true);
      expect(wrapper.getAttribute('data-theme')).toBe('dark');

      // Simulate a second component calling useProposalDarkMode (same shared module)
      // e.g. FunctionalRequirementsModal mounting after section navigation
      useProposalDarkMode();
      // Execute the second onMounted callback
      const secondMountedCb = mockMountedCbs[mockMountedCbs.length - 1];
      secondMountedCb();

      // isDark must remain true — the bug was that it was reset to false
      expect(isDark.value).toBe(true);
      expect(wrapper.getAttribute('data-theme')).toBe('dark');
    });
  });

  describe('applyTheme SSR guard', () => {
    it('does not throw when document is undefined', () => {
      const originalDocument = global.document;
      delete global.document;

      const { applyTheme } = useProposalDarkMode();

      expect(() => applyTheme(true)).not.toThrow();

      global.document = originalDocument;
    });
  });
});
