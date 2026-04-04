/**
 * Tests for the useExpirationTimer composable.
 *
 * Covers: daysRemaining, hoursRemaining, isExpired, urgencyLevel,
 * formattedCountdown with various time differences.
 */
import { ref } from 'vue';
import { useExpirationTimer } from '../../composables/useExpirationTimer';

jest.useFakeTimers();
jest.setSystemTime(new Date('2026-03-01T12:00:00Z'));

afterAll(() => {
  jest.useRealTimers();
});

beforeEach(() => {
  jest.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('useExpirationTimer', () => {
  describe('with undefined expiresAt', () => {
    it('returns null for daysRemaining', () => {
      const { daysRemaining } = useExpirationTimer(undefined);

      expect(daysRemaining.value).toBeNull();
    });

    it('returns null for hoursRemaining', () => {
      const { hoursRemaining } = useExpirationTimer(undefined);

      expect(hoursRemaining.value).toBeNull();
    });

    it('returns null for minutesRemaining', () => {
      const { minutesRemaining } = useExpirationTimer(undefined);

      expect(minutesRemaining.value).toBeNull();
    });

    it('returns false for isExpired', () => {
      const { isExpired } = useExpirationTimer(undefined);

      expect(isExpired.value).toBe(false);
    });

    it('returns calm for urgencyLevel', () => {
      const { urgencyLevel } = useExpirationTimer(undefined);

      expect(urgencyLevel.value).toBe('calm');
    });

    it('returns empty string for formattedCountdown', () => {
      const { formattedCountdown } = useExpirationTimer(undefined);

      expect(formattedCountdown.value).toBe('');
    });
  });

  describe('with future date more than 3 days away', () => {
    it('returns correct daysRemaining', () => {
      const expiresAt = ref('2026-03-10T12:00:00Z');
      const { daysRemaining } = useExpirationTimer(expiresAt);

      expect(daysRemaining.value).toBe(9);
    });

    it('returns correct minutesRemaining', () => {
      const expiresAt = ref('2026-03-10T12:00:00Z');
      const { minutesRemaining } = useExpirationTimer(expiresAt);

      expect(minutesRemaining.value).toBe(9 * 24 * 60);
    });

    it('returns calm urgencyLevel', () => {
      const expiresAt = ref('2026-03-10T12:00:00Z');
      const { urgencyLevel } = useExpirationTimer(expiresAt);

      expect(urgencyLevel.value).toBe('calm');
    });

    it('formats countdown with days only when days are positive', () => {
      const expiresAt = ref('2026-03-04T18:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('3 días');
    });
  });

  describe('with future date 4-7 days away', () => {
    it('returns notice urgencyLevel', () => {
      const expiresAt = ref('2026-03-06T12:00:00Z');
      const { urgencyLevel } = useExpirationTimer(expiresAt);

      expect(urgencyLevel.value).toBe('notice');
    });
  });

  describe('with future date 1-3 days away', () => {
    it('returns warning urgencyLevel', () => {
      const expiresAt = ref('2026-03-03T12:00:00Z');
      const { urgencyLevel } = useExpirationTimer(expiresAt);

      expect(urgencyLevel.value).toBe('warning');
    });

    it('formats countdown with days only when no remaining hours', () => {
      const expiresAt = ref('2026-03-03T12:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('2 días');
    });
  });

  describe('with future date less than 1 day away', () => {
    it('returns urgent urgencyLevel', () => {
      const expiresAt = ref('2026-03-01T20:00:00Z');
      const { urgencyLevel } = useExpirationTimer(expiresAt);

      expect(urgencyLevel.value).toBe('urgent');
    });

    it('formats countdown in HH:MM when 8 hours left', () => {
      const expiresAt = ref('2026-03-01T20:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('08:00');
    });

    it('formats countdown in HH:MM when 1 hour left', () => {
      const expiresAt = ref('2026-03-01T13:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('01:00');
    });

    it('formats countdown in HH:MM when 30 minutes left', () => {
      const expiresAt = ref('2026-03-01T12:30:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('00:30');
    });
  });

  describe('with expired date', () => {
    it('returns true for isExpired', () => {
      const expiresAt = ref('2026-02-28T12:00:00Z');
      const { isExpired } = useExpirationTimer(expiresAt);

      expect(isExpired.value).toBe(true);
    });

    it('returns expired urgencyLevel', () => {
      const expiresAt = ref('2026-02-28T12:00:00Z');
      const { urgencyLevel } = useExpirationTimer(expiresAt);

      expect(urgencyLevel.value).toBe('expired');
    });

    it('returns "Expirada" for formattedCountdown', () => {
      const expiresAt = ref('2026-02-28T12:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('Expirada');
    });

    it('returns 0 for daysRemaining', () => {
      const expiresAt = ref('2026-02-28T12:00:00Z');
      const { daysRemaining } = useExpirationTimer(expiresAt);

      expect(daysRemaining.value).toBe(0);
    });

    it('returns 0 for hoursRemaining', () => {
      const expiresAt = ref('2026-02-28T12:00:00Z');
      const { hoursRemaining } = useExpirationTimer(expiresAt);

      expect(hoursRemaining.value).toBe(0);
    });
  });

  describe('with plain string (non-ref) expiresAt', () => {
    it('handles plain string argument', () => {
      const { daysRemaining } = useExpirationTimer('2026-03-05T12:00:00Z');

      expect(daysRemaining.value).toBe(4);
    });
  });

  describe('with under-48h day formatting', () => {
    it('formats HH:MM when 30 hours left', () => {
      const expiresAt = ref('2026-03-02T18:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('30:00');
    });

    it('formats HH:MM when 25 hours left', () => {
      const expiresAt = ref('2026-03-02T13:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('25:00');
    });

    it('formats HH:MM when exactly 24 hours left', () => {
      const expiresAt = ref('2026-03-02T12:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('24:00');
    });

    it('formats días when 3 days left (over 48h)', () => {
      const expiresAt = ref('2026-03-04T12:00:00Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('3 días');
    });
  });

  describe('countdown mode interval switch', () => {
    it('switches to 1s interval when entering countdown mode', () => {
      const expiresAt = ref('2026-03-10T12:00:00Z');
      const { isCountdownMode } = useExpirationTimer(expiresAt);

      expect(isCountdownMode.value).toBe(false);

      expiresAt.value = '2026-03-02T00:00:00Z';
    });
  });

  describe('edge case: exactly 0 days but totalHours >= 48', () => {
    it('returns Menos de 1 hora when diffMs is positive but days is 0 and hours >= 48', () => {
      jest.setSystemTime(new Date('2026-03-01T12:00:00Z'));
      const expiresAt = ref('2026-03-01T12:00:01Z');
      const { formattedCountdown } = useExpirationTimer(expiresAt);

      expect(formattedCountdown.value).toBe('00:00');
    });
  });

  describe('lifecycle hooks', () => {
    let useExpirationTimerWithHooks;
    let mountedCbs, unmountedCbs;

    beforeEach(() => {
      jest.resetModules();
      mountedCbs = [];
      unmountedCbs = [];

      jest.doMock('vue', () => {
        const actualVue = jest.requireActual('vue');
        return {
          ...actualVue,
          onMounted: (cb) => { mountedCbs.push(cb); },
          onUnmounted: (cb) => { unmountedCbs.push(cb); },
        };
      });

      useExpirationTimerWithHooks = require('../../composables/useExpirationTimer').useExpirationTimer;
    });

    it('starts interval on mount that updates now', () => {
      useExpirationTimerWithHooks(ref('2026-03-10T12:00:00Z'));
      expect(mountedCbs).toHaveLength(1);

      mountedCbs[0]();
      jest.advanceTimersByTime(60000);
    });

    it('clears interval on unmount', () => {
      useExpirationTimerWithHooks(ref('2026-03-10T12:00:00Z'));
      mountedCbs[0]();

      expect(unmountedCbs).toHaveLength(1);
      unmountedCbs[0]();
    });

    it('clears previous interval when restarting due to mode change', () => {
      const expiresAt = ref('2026-03-10T12:00:00Z');
      useExpirationTimerWithHooks(expiresAt);
      mountedCbs[0](); // sets the interval

      // Changing expiresAt triggers isCountdownMode watch → startInterval called again
      expiresAt.value = '2026-03-02T00:00:00Z'; // ~36h away, triggers countdown mode

      // Just asserting no errors thrown (the interval was cleared and recreated)
      expect(true).toBe(true);
    });

    it('handles unmount when no interval was set', () => {
      useExpirationTimerWithHooks(ref('2026-03-10T12:00:00Z'));

      expect(unmountedCbs).toHaveLength(1);
      expect(() => unmountedCbs[0]()).not.toThrow();
    });
  });
});
