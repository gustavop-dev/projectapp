import { formatCompactMoney, formatMoney } from '../../utils/formatMoney';

describe('formatMoney', () => {
  it('formats COP with the currency suffix', () => {
    expect(formatMoney(1234567, 'COP')).toBe('$1.234.567 COP');
  });

  it('returns an empty string for nullish or non-finite values', () => {
    expect(formatMoney(null)).toBe('');
    expect(formatMoney(Number.NaN)).toBe('');
  });

  it('rounds to whole units by default', () => {
    expect(formatMoney(0.915, 'USD')).toBe('$1 USD');
  });

  it('keeps decimals when asked, so sub-unit amounts stay readable', () => {
    expect(formatMoney(0.915, 'USD', { decimals: 2 })).toBe('$0,92 USD');
    expect(formatMoney(20, 'USD', { decimals: 2 })).toBe('$20,00 USD');
  });
});

describe('formatCompactMoney', () => {
  it('shortens millions and thousands', () => {
    expect(formatCompactMoney(1234567)).toBe('$1,2M');
    expect(formatCompactMoney(850000)).toBe('$850K');
  });

  it('keeps small amounts and the sign', () => {
    expect(formatCompactMoney(0)).toBe('$0');
    expect(formatCompactMoney(-1234567)).toBe('-$1,2M');
  });

  it('returns an empty string for nullish or non-finite values', () => {
    expect(formatCompactMoney(undefined)).toBe('');
    expect(formatCompactMoney('abc')).toBe('');
  });
});
