/**
 * Tests for the useProposalTracking composable.
 *
 * Covers: generateSessionId, getOrCreateSessionId, startSectionTimer,
 * stopSectionTimer, buildPayload, flush, flushBeacon, watch callback,
 * onMounted lifecycle, onBeforeUnmount lifecycle.
 */
let mountedCallbacks;
let unmountCallbacks;
let watchCallbacks;
let useProposalTracking;

const flushPromises = () => new Promise((r) => setTimeout(r, 0));

beforeEach(() => {
  mountedCallbacks = [];
  unmountCallbacks = [];
  watchCallbacks = [];

  jest.useFakeTimers();
  jest.setSystemTime(new Date('2026-03-07T12:00:00Z'));

  jest.clearAllMocks();
  jest.resetModules();

  jest.doMock('vue', () => {
    const actualVue = jest.requireActual('vue');
    return {
      ...actualVue,
      onMounted: (cb) => { mountedCallbacks.push(cb); },
      onBeforeUnmount: (cb) => { unmountCallbacks.push(cb); },
      watch: (source, cb, opts) => { watchCallbacks.push({ source, cb, opts }); },
    };
  });

  useProposalTracking = require('../../composables/useProposalTracking').useProposalTracking;
});

afterEach(() => {
  // Run all unmount callbacks to remove event listeners from previous test
  unmountCallbacks.forEach((cb) => cb());
  jest.useRealTimers();
  jest.restoreAllMocks();
  sessionStorage.clear();
  delete global.fetch;
});

function createRefs(uuid = 'test-uuid', panel = null) {
  const { ref } = jest.requireActual('vue');
  return {
    proposalUuid: ref(uuid),
    currentPanel: ref(panel),
  };
}

describe('useProposalTracking', () => {
  describe('initialization', () => {
    it('returns sessionId, sectionLog, and flush', () => {
      const { proposalUuid, currentPanel } = createRefs();
      const result = useProposalTracking(proposalUuid, currentPanel);

      expect(result).toHaveProperty('sessionId');
      expect(result).toHaveProperty('sectionLog');
      expect(result).toHaveProperty('flush');
    });

    it('registers onMounted and onBeforeUnmount callbacks', () => {
      const { proposalUuid, currentPanel } = createRefs();
      useProposalTracking(proposalUuid, currentPanel);

      expect(mountedCallbacks).toHaveLength(1);
      expect(unmountCallbacks).toHaveLength(1);
    });

    it('registers a watcher with immediate false', () => {
      const { proposalUuid, currentPanel } = createRefs();
      useProposalTracking(proposalUuid, currentPanel);

      expect(watchCallbacks).toHaveLength(1);
      expect(watchCallbacks[0].opts.immediate).toBe(false);
    });
  });

  describe('onMounted', () => {
    it('generates a session ID starting with ses_', () => {
      const mockRandom = jest.spyOn(Math, 'random').mockReturnValue(0.123456789);
      const { proposalUuid, currentPanel } = createRefs();
      const { sessionId } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();

      expect(sessionId.value).toMatch(/^ses_/);
      mockRandom.mockRestore();
    });

    it('reuses session ID from sessionStorage', () => {
      sessionStorage.setItem('proposal_session_test-uuid', 'ses_existing');
      const { proposalUuid, currentPanel } = createRefs();
      const { sessionId } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();

      expect(sessionId.value).toBe('ses_existing');
    });

    it('stores new session ID in sessionStorage', () => {
      const { proposalUuid, currentPanel } = createRefs();
      const { sessionId } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();

      expect(sessionStorage.getItem('proposal_session_test-uuid')).toBe(sessionId.value);
    });

    it('starts timer for initial panel if present', () => {
      const panel = { section_type: 'greeting', title: 'Hello' };
      const { proposalUuid, currentPanel } = createRefs('uuid-1', panel);
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      jest.spyOn(performance, 'now').mockReturnValue(1000);
      mountedCallbacks[0]();

      // Stop the timer by switching panels — entry lands in sectionLog
      jest.spyOn(performance, 'now').mockReturnValue(6000);
      watchCallbacks[0].cb(null, panel);

      expect(sectionLog.value).toHaveLength(1);
      expect(sectionLog.value[0].section_type).toBe('greeting');
      expect(sectionLog.value[0].time_spent_seconds).toBe(5);
    });

    it('registers beforeunload and visibilitychange listeners', () => {
      const addSpy = jest.spyOn(window, 'addEventListener');
      const docAddSpy = jest.spyOn(document, 'addEventListener');
      const { proposalUuid, currentPanel } = createRefs();
      useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();

      expect(addSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
      expect(docAddSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));

      addSpy.mockRestore();
      docAddSpy.mockRestore();
    });
  });

  describe('watch callback (section changes)', () => {
    it('starts timer when new panel is set', () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      const { proposalUuid, currentPanel } = createRefs();
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      const newPanel = { section_type: 'investment', title: 'Investment' };
      watchCallbacks[0].cb(newPanel, null);

      // Stop it by switching panels
      jest.spyOn(performance, 'now').mockReturnValue(4000);
      watchCallbacks[0].cb(null, newPanel);

      expect(sectionLog.value).toHaveLength(1);
      expect(sectionLog.value[0].section_type).toBe('investment');
      expect(sectionLog.value[0].time_spent_seconds).toBe(3);
    });

    it('stops old timer and starts new one on panel switch', () => {
      jest.spyOn(performance, 'now').mockReturnValue(0);
      const { proposalUuid, currentPanel } = createRefs();
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();

      const panel1 = { section_type: 'greeting', title: 'Hi' };
      watchCallbacks[0].cb(panel1, null);

      jest.spyOn(performance, 'now').mockReturnValue(2000);
      const panel2 = { section_type: 'timeline', title: 'Timeline' };
      watchCallbacks[0].cb(panel2, panel1);

      expect(sectionLog.value).toHaveLength(1);
      expect(sectionLog.value[0].section_type).toBe('greeting');
      expect(sectionLog.value[0].time_spent_seconds).toBe(2);
    });

    it('does nothing when panel is null', () => {
      const { proposalUuid, currentPanel } = createRefs();
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      watchCallbacks[0].cb(null, null);

      expect(sectionLog.value).toHaveLength(0);
    });
  });

  describe('flush', () => {
    it('sends POST to tracking endpoint on flush', async () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn().mockResolvedValue({ ok: true });
      const { proposalUuid, currentPanel } = createRefs('uuid-flush');
      const { sectionLog, flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      // Manually push an entry to sectionLog
      sectionLog.value.push({
        section_type: 'greeting',
        section_title: 'Hi',
        entered_at: '2026-03-07T12:00:00.000Z',
        time_spent_seconds: 5,
      });

      await flush();

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/proposals/uuid-flush/track/',
        expect.objectContaining({ method: 'POST' }),
      );
    });

    it('clears sectionLog after successful flush', async () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn().mockResolvedValue({ ok: true });
      const { proposalUuid, currentPanel } = createRefs('uuid-clear');
      const { sectionLog, flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({
        section_type: 'greeting',
        section_title: 'Hi',
        entered_at: '2026-03-07T12:00:00.000Z',
        time_spent_seconds: 5,
      });

      await flush();

      expect(sectionLog.value).toHaveLength(0);
    });

    it('does not clear sectionLog when response is not ok', async () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn().mockResolvedValue({ ok: false });
      const { proposalUuid, currentPanel } = createRefs('uuid-fail');
      const { sectionLog, flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({
        section_type: 'greeting',
        section_title: 'Hi',
        entered_at: '2026-03-07T12:00:00.000Z',
        time_spent_seconds: 5,
      });

      await flush();

      expect(sectionLog.value).toHaveLength(1);
    });

    it('skips flush when sectionLog is empty and no currentEntry', async () => {
      global.fetch = jest.fn();
      const { proposalUuid, currentPanel } = createRefs();
      const { flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      await flush();

      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('skips flush when proposalUuid is empty', async () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn();
      const { proposalUuid, currentPanel } = createRefs('');
      const { sectionLog, flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({ section_type: 'x', section_title: '', entered_at: '', time_spent_seconds: 1 });

      await flush();

      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('silently handles fetch errors', async () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn().mockRejectedValue(new Error('network'));
      const { proposalUuid, currentPanel } = createRefs('uuid-err');
      const { sectionLog, flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({ section_type: 'x', section_title: '', entered_at: '', time_spent_seconds: 1 });

      await expect(flush()).resolves.toBeUndefined();
    });

    it('includes current running entry snapshot in payload', async () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn().mockResolvedValue({ ok: true });
      const { proposalUuid, currentPanel } = createRefs('uuid-snap');
      const { flush } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      // Start a section timer via watcher
      const panel = { section_type: 'investment', title: 'Invest' };
      watchCallbacks[0].cb(panel, null);

      jest.spyOn(performance, 'now').mockReturnValue(3500);
      await flush();

      const body = JSON.parse(global.fetch.mock.calls[0][1].body);
      expect(body.sections).toHaveLength(1);
      expect(body.sections[0].section_type).toBe('investment');
      expect(body.sections[0].time_spent_seconds).toBe(2.5);
    });
  });

  describe('flushBeacon', () => {
    it('sends beacon on beforeunload', () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      const mockBeacon = jest.fn();
      navigator.sendBeacon = mockBeacon;
      const { proposalUuid, currentPanel } = createRefs('uuid-beacon');
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({ section_type: 'x', section_title: '', entered_at: '', time_spent_seconds: 1 });

      // Trigger beforeunload
      window.dispatchEvent(new Event('beforeunload'));

      expect(mockBeacon).toHaveBeenCalledWith(
        '/api/proposals/uuid-beacon/track/',
        expect.any(Blob),
      );
    });

    it('skips beacon when no sections to send', () => {
      const mockBeacon = jest.fn();
      navigator.sendBeacon = mockBeacon;
      const { proposalUuid, currentPanel } = createRefs('uuid-empty');
      useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();

      // Only check calls from THIS test's beacon mock
      const callsBefore = mockBeacon.mock.calls.length;
      window.dispatchEvent(new Event('beforeunload'));

      expect(mockBeacon.mock.calls.length).toBe(callsBefore);
    });

    it('sends beacon on visibilitychange to hidden', () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      const mockBeacon = jest.fn();
      navigator.sendBeacon = mockBeacon;
      const { proposalUuid, currentPanel } = createRefs('uuid-vis');
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({ section_type: 'x', section_title: '', entered_at: '', time_spent_seconds: 1 });

      Object.defineProperty(document, 'visibilityState', {
        value: 'hidden',
        writable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));

      expect(mockBeacon).toHaveBeenCalled();
    });

    it('silently handles sendBeacon errors', () => {
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      navigator.sendBeacon = jest.fn(() => { throw new Error('fail'); });
      const { proposalUuid, currentPanel } = createRefs('uuid-berr');
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      sectionLog.value.push({ section_type: 'x', section_title: '', entered_at: '', time_spent_seconds: 1 });

      expect(() => window.dispatchEvent(new Event('beforeunload'))).not.toThrow();
    });
  });

  describe('onBeforeUnmount', () => {
    it('stops current timer and flushes on unmount', async () => {
      jest.useRealTimers();
      jest.spyOn(performance, 'now').mockReturnValue(1000);
      global.fetch = jest.fn().mockResolvedValue({ ok: true });
      const { proposalUuid, currentPanel } = createRefs('uuid-unmount');
      useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      // Start a section
      const panel = { section_type: 'greeting', title: 'Hi' };
      watchCallbacks[0].cb(panel, null);

      jest.spyOn(performance, 'now').mockReturnValue(5000);
      unmountCallbacks[0]();
      await flushPromises();

      expect(global.fetch).toHaveBeenCalled();
    });

    it('removes beforeunload listener on unmount', () => {
      const removeSpy = jest.spyOn(window, 'removeEventListener');
      const { proposalUuid, currentPanel } = createRefs();
      useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      unmountCallbacks[0]();

      expect(removeSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
      removeSpy.mockRestore();
    });

    it('clears flush interval on unmount', () => {
      const clearSpy = jest.spyOn(global, 'clearInterval');
      const { proposalUuid, currentPanel } = createRefs();
      useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      unmountCallbacks[0]();

      expect(clearSpy).toHaveBeenCalled();
      clearSpy.mockRestore();
    });
  });

  describe('getOrCreateSessionId edge cases', () => {
    it('generates session ID when sessionStorage is unavailable', () => {
      // Re-mock with sessionStorage undefined
      jest.resetModules();
      jest.doMock('vue', () => {
        const actualVue = jest.requireActual('vue');
        return {
          ...actualVue,
          onMounted: (cb) => { mountedCallbacks.push(cb); },
          onBeforeUnmount: (cb) => { unmountCallbacks.push(cb); },
          watch: (source, cb, opts) => { watchCallbacks.push({ source, cb, opts }); },
        };
      });

      const originalStorage = global.sessionStorage;
      delete global.sessionStorage;

      const mod = require('../../composables/useProposalTracking');
      const { ref } = jest.requireActual('vue');
      const { sessionId } = mod.useProposalTracking(ref('uuid'), ref(null));

      // Use the second mounted callback (from re-require)
      mountedCallbacks[mountedCallbacks.length - 1]();

      expect(sessionId.value).toMatch(/^ses_/);

      global.sessionStorage = originalStorage;
    });
  });

  describe('startSectionTimer edge cases', () => {
    it('handles panel without section_type or title gracefully', () => {
      jest.spyOn(performance, 'now').mockReturnValue(0);
      const { proposalUuid, currentPanel } = createRefs();
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      watchCallbacks[0].cb({}, null);

      jest.spyOn(performance, 'now').mockReturnValue(1000);
      watchCallbacks[0].cb(null, {});

      expect(sectionLog.value).toHaveLength(1);
      expect(sectionLog.value[0].section_type).toBe('');
      expect(sectionLog.value[0].section_title).toBe('');
    });

    it('does nothing when startSectionTimer receives null panel', () => {
      const { proposalUuid, currentPanel } = createRefs();
      const { sectionLog } = useProposalTracking(proposalUuid, currentPanel);

      mountedCallbacks[0]();
      watchCallbacks[0].cb(null, null);

      expect(sectionLog.value).toHaveLength(0);
    });
  });
});
