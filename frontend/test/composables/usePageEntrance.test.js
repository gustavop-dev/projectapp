/**
 * Tests for the usePageEntrance composable.
 *
 * Covers: default container (document.body), custom containerSelector,
 * no container found, no [data-enter] elements found, gsap calls.
 */
import { usePageEntrance } from '../../composables/usePageEntrance';

const mockGsapSet = jest.fn();
const mockGsapTo = jest.fn();

jest.mock('gsap', () => ({
  gsap: {
    set: (...args) => mockGsapSet(...args),
    to: (...args) => mockGsapTo(...args),
  },
}));

jest.mock('vue', () => ({
  ...jest.requireActual('vue'),
  onMounted: (fn) => fn(),
  nextTick: (fn) => (fn ? fn() : Promise.resolve()),
}));

describe('usePageEntrance', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockGsapSet.mockClear();
    mockGsapTo.mockClear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('animates [data-enter] elements in document.body by default', () => {
    const el1 = document.createElement('div');
    el1.setAttribute('data-enter', '');
    const el2 = document.createElement('div');
    el2.setAttribute('data-enter', '');
    document.body.appendChild(el1);
    document.body.appendChild(el2);

    usePageEntrance();
    jest.advanceTimersByTime(100);

    expect(mockGsapSet).toHaveBeenCalledTimes(1);
    expect(mockGsapTo).toHaveBeenCalledTimes(1);
    expect(mockGsapTo).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        opacity: 1,
        y: 0,
        duration: 0.6,
        stagger: 0.08,
      }),
    );

    document.body.removeChild(el1);
    document.body.removeChild(el2);
  });

  it('uses custom containerSelector when provided', () => {
    const container = document.createElement('div');
    container.id = 'test-container';
    const el = document.createElement('span');
    el.setAttribute('data-enter', '');
    container.appendChild(el);
    document.body.appendChild(container);

    usePageEntrance('#test-container');
    jest.advanceTimersByTime(100);

    expect(mockGsapSet).toHaveBeenCalledTimes(1);
    expect(mockGsapTo).toHaveBeenCalledTimes(1);

    document.body.removeChild(container);
  });

  it('does nothing when container is not found', () => {
    usePageEntrance('#nonexistent-container');
    jest.advanceTimersByTime(100);

    expect(mockGsapSet).not.toHaveBeenCalled();
    expect(mockGsapTo).not.toHaveBeenCalled();
  });

  it('does nothing when no [data-enter] elements exist', () => {
    usePageEntrance();
    jest.advanceTimersByTime(100);

    expect(mockGsapSet).not.toHaveBeenCalled();
    expect(mockGsapTo).not.toHaveBeenCalled();
  });
});
