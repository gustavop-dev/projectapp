/**
 * Tests for the useReducedMotion composable.
 *
 * Covers: reduce preference, no-preference, and environments without
 * window.matchMedia (SSR-like), which must default to false.
 */
import { useReducedMotion } from '../../composables/useReducedMotion';

function mockMatchMedia(matches) {
  return jest.fn().mockImplementation((query) => ({
    matches,
    media: query,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    addListener: jest.fn(),
    removeListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
}

describe('useReducedMotion', () => {
  const originalMatchMedia = window.matchMedia;

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it('is true when the user prefers reduced motion', () => {
    window.matchMedia = mockMatchMedia(true);
    const { reducedMotion } = useReducedMotion();
    expect(reducedMotion.value).toBe(true);
  });

  it('is false when there is no motion preference', () => {
    window.matchMedia = mockMatchMedia(false);
    const { reducedMotion } = useReducedMotion();
    expect(reducedMotion.value).toBe(false);
  });

  it('defaults to false when matchMedia is unavailable', () => {
    delete window.matchMedia;
    const { reducedMotion } = useReducedMotion();
    expect(reducedMotion.value).toBe(false);
  });
});
