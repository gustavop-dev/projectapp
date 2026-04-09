/**
 * Tests for useStageStatus composable.
 *
 * Covers: formatRemainingTime (full pluralization table),
 *         computeStageStatus (all branches),
 *         formatHumanDate (date / ISO / null).
 */

import { useStageStatus } from '../../composables/useStageStatus';

const { formatRemainingTime, computeStageStatus, formatHumanDate } = useStageStatus();

describe('useStageStatus.formatRemainingTime', () => {
  it('returns "hoy" for zero days', () => {
    expect(formatRemainingTime(0)).toBe('hoy');
  });

  it('returns "1 día" for 1 day (singular)', () => {
    expect(formatRemainingTime(1)).toBe('1 día');
  });

  it('returns "2 días" for 2 days (plural)', () => {
    expect(formatRemainingTime(2)).toBe('2 días');
  });

  it('returns "6 días" for 6 days', () => {
    expect(formatRemainingTime(6)).toBe('6 días');
  });

  it('returns "1 semana" for exactly 7 days', () => {
    expect(formatRemainingTime(7)).toBe('1 semana');
  });

  it('returns "1 semana 1 día" for 8 days', () => {
    expect(formatRemainingTime(8)).toBe('1 semana 1 día');
  });

  it('returns "1 semana 5 días" for 12 days', () => {
    expect(formatRemainingTime(12)).toBe('1 semana 5 días');
  });

  it('returns "2 semanas" for exactly 14 days', () => {
    expect(formatRemainingTime(14)).toBe('2 semanas');
  });

  it('returns "2 semanas 1 día" for 15 days', () => {
    expect(formatRemainingTime(15)).toBe('2 semanas 1 día');
  });

  it('returns "3 semanas" for exactly 21 days', () => {
    expect(formatRemainingTime(21)).toBe('3 semanas');
  });

  it('treats negative values as their absolute value', () => {
    expect(formatRemainingTime(-12)).toBe('1 semana 5 días');
  });
});

describe('useStageStatus.computeStageStatus', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2026-04-09T12:00:00Z'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('returns unscheduled when stage is missing', () => {
    expect(computeStageStatus(null).kind).toBe('unscheduled');
  });

  it('returns unscheduled when start_date is missing', () => {
    expect(
      computeStageStatus({ start_date: null, end_date: '2026-04-15' }).kind,
    ).toBe('unscheduled');
  });

  it('returns completed when completed_at is set', () => {
    expect(
      computeStageStatus({
        completed_at: '2026-04-08T12:00:00Z',
        start_date: '2026-04-01',
        end_date: '2026-04-10',
      }).kind,
    ).toBe('completed');
  });

  it('returns not_started when today is before start_date', () => {
    expect(
      computeStageStatus({
        start_date: '2026-04-15',
        end_date: '2026-04-30',
      }).kind,
    ).toBe('not_started');
  });

  it('returns pending with formatted label when within the window', () => {
    // start=Apr 1, end=Apr 11, today=Apr 9 → 2 days remaining
    const status = computeStageStatus({
      start_date: '2026-04-01',
      end_date: '2026-04-11',
    });
    expect(status.kind).toBe('pending');
    expect(status.label).toBe('2 días');
  });

  it('returns overdue with formatted label when today is past end_date', () => {
    // end_date = 3 days ago
    const status = computeStageStatus({
      start_date: '2026-03-20',
      end_date: '2026-04-06',
    });
    expect(status.kind).toBe('overdue');
    expect(status.label).toBe('3 días');
  });

  it('returns pending with percent for elapsed progress', () => {
    // start=Apr 1, end=Apr 11, today=Apr 9 → 8/10 = 80%
    const status = computeStageStatus({
      start_date: '2026-04-01',
      end_date: '2026-04-11',
    });
    expect(status.percent).toBe(80);
  });
});

describe('useStageStatus.formatHumanDate', () => {
  it('returns empty string for null', () => {
    expect(formatHumanDate(null)).toBe('');
  });

  it('returns empty string for invalid date', () => {
    expect(formatHumanDate('not-a-date')).toBe('');
  });

  it('formats an ISO datetime as "8 de abril, 2026"', () => {
    expect(formatHumanDate('2026-04-08T15:30:00Z')).toBe('8 de abril, 2026');
  });

  it('formats a Date instance', () => {
    expect(formatHumanDate(new Date('2026-12-25'))).toBe('25 de diciembre, 2026');
  });
});
