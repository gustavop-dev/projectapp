import {
  bestValuePackageId,
  effectiveRate,
  formatPackageMoney,
  totalPrice,
} from '../../utils/hourPackagePricing';

const pkg = (overrides = {}) => ({
  id: 1,
  hours: 10,
  hourly_rate: '100000',
  discount_percent: '20',
  is_active: true,
  ...overrides,
});

describe('hourPackagePricing', () => {
  it('applies the discount to the hourly rate', () => {
    expect(effectiveRate(pkg())).toBe(80000);
  });

  it('treats a missing discount as zero', () => {
    expect(effectiveRate(pkg({ discount_percent: undefined }))).toBe(100000);
  });

  it('multiplies hours by the effective rate for the total', () => {
    expect(totalPrice(pkg())).toBe(800000);
  });

  it('formats COP without decimals using dot grouping', () => {
    expect(formatPackageMoney(1234567.8, 'COP')).toBe('$1.234.568 COP');
  });

  it('formats USD keeping cents', () => {
    expect(formatPackageMoney(1234.56, 'USD')).toBe('$1,234.56 USD');
  });

  it('returns null as best value when no active discounted packages exist', () => {
    expect(bestValuePackageId([
      pkg({ discount_percent: '0' }),
      pkg({ id: 2, is_active: false }),
    ])).toBeNull();
  });

  it('picks the active package with the lowest effective rate', () => {
    expect(bestValuePackageId([
      pkg({ id: 1, discount_percent: '10' }),
      pkg({ id: 2, discount_percent: '30' }),
      pkg({ id: 3, discount_percent: '25', is_active: false }),
    ])).toBe(2);
  });
});
