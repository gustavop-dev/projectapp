import { formatDate, formatDateTime, formatDayMonth } from '../../utils/formatDate';

describe('formatDate', () => {
  it('formats a date-only string without day shifting', () => {
    expect(formatDate('2026-07-16')).toBe('Jue, 16 jul 2026');
    expect(formatDate('2026-01-01')).toBe('Jue, 1 ene 2026');
  });

  it('converts ISO datetimes to the Bogotá calendar day', () => {
    // 02:30 UTC = 21:30 del día anterior en Bogotá.
    expect(formatDate('2026-08-01T02:30:00Z')).toBe('Vie, 31 jul 2026');
  });

  it('accepts Date instances', () => {
    expect(formatDate(new Date(Date.UTC(2026, 7, 3, 20, 20)))).toBe('Lun, 3 ago 2026');
  });

  it('formats in English when requested', () => {
    expect(formatDate('2026-07-16', { locale: 'en' })).toBe('Thu, Jul 16, 2026');
  });

  it('returns the fallback for nullish, empty or invalid values', () => {
    expect(formatDate(null)).toBe('—');
    expect(formatDate(undefined)).toBe('—');
    expect(formatDate('')).toBe('—');
    expect(formatDate('not-a-date')).toBe('—');
    expect(formatDate(null, { fallback: 'Sin fecha' })).toBe('Sin fecha');
  });
});

describe('formatDateTime', () => {
  it('appends the Bogotá time to the standard date', () => {
    expect(formatDateTime('2026-08-03T20:20:00Z')).toBe('Lun, 3 ago 2026, 15:20');
  });

  it('omits the time for date-only values', () => {
    expect(formatDateTime('2026-07-16')).toBe('Jue, 16 jul 2026');
  });

  it('returns the fallback for nullish or invalid values', () => {
    expect(formatDateTime(null)).toBe('—');
    expect(formatDateTime('nope', { fallback: '' })).toBe('');
  });
});

describe('formatDayMonth', () => {
  it('formats compact day + month per locale', () => {
    expect(formatDayMonth('2026-05-15')).toBe('15 may');
    expect(formatDayMonth('2026-05-15', { locale: 'en' })).toBe('May 15');
  });

  it('returns the fallback for nullish or invalid values', () => {
    expect(formatDayMonth(null)).toBe('');
    expect(formatDayMonth('bad', { fallback: '—' })).toBe('—');
  });
});
