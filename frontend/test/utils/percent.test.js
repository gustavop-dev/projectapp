import {
  addWeightPct,
  formatPercent,
  largestRemainder,
  percentOf,
} from '../../utils/percent';

describe('percentOf', () => {
  it('returns the share of the value over the total', () => {
    expect(percentOf(25, 200)).toBe(12.5);
  });

  it('returns 0 when the total is zero, so an empty tab never divides by zero', () => {
    expect(percentOf(500, 0)).toBe(0);
  });

  it('returns 0 for a negative or non-numeric total', () => {
    expect(percentOf(500, -10)).toBe(0);
    expect(percentOf(500, 'nope')).toBe(0);
  });
});

describe('formatPercent', () => {
  it('rounds to one decimal with the es-CO comma', () => {
    expect(formatPercent(12.34)).toBe('12,3%');
  });

  it('keeps whole values bare', () => {
    expect(formatPercent(25)).toBe('25%');
  });

  it('shows zero and invalid input as 0%', () => {
    expect(formatPercent(0)).toBe('0%');
    expect(formatPercent(null)).toBe('0%');
  });

  it('does not clamp above 100 — a historical card snapshot can exceed today\'s debt', () => {
    expect(formatPercent(133.33)).toBe('133,3%');
  });
});

describe('addWeightPct', () => {
  const rows = [
    { id: 1, amount: '750' },
    { id: 2, amount: '250' },
  ];

  it('decorates each row with its share of the summed contributions', () => {
    const weighted = addWeightPct(rows, (row) => Number(row.amount));
    expect(weighted.map((r) => r.weight_pct)).toEqual([75, 25]);
  });

  it('uses an explicit base instead of the sum when given', () => {
    const weighted = addWeightPct(rows, (row) => Number(row.amount), { base: 2000 });
    expect(weighted.map((r) => r.weight_pct)).toEqual([37.5, 12.5]);
  });

  it('gives every row 0% when the base is zero', () => {
    const weighted = addWeightPct(rows, () => 0);
    expect(weighted.map((r) => r.weight_pct)).toEqual([0, 0]);
  });

  it('keeps rows whose contribution is zeroed (inactive) at 0% and out of the base', () => {
    const mixed = [
      { id: 1, amount: 100, active: true },
      { id: 2, amount: 900, active: false },
    ];
    const weighted = addWeightPct(mixed, (row) => (row.active ? row.amount : 0));
    expect(weighted.map((r) => r.weight_pct)).toEqual([100, 0]);
  });

  it('does not mutate the input rows', () => {
    addWeightPct(rows, (row) => Number(row.amount));
    expect(rows[0].weight_pct).toBeUndefined();
  });
});

describe('largestRemainder', () => {
  it('rounds a set summing to 100 so the rounded set still sums to exactly 100', () => {
    // Independent rounding gives 33.3 + 33.3 + 33.3 = 99.9.
    const rounded = largestRemainder([100 / 3, 100 / 3, 100 / 3]);
    expect(rounded.reduce((sum, value) => sum + value, 0)).toBeCloseTo(100, 10);
  });

  it('preserves the input order while distributing the leftover', () => {
    const rounded = largestRemainder([16.66, 16.67, 66.67]);
    expect(rounded).toHaveLength(3);
    expect(rounded[2]).toBeGreaterThan(rounded[0]);
    expect(rounded.reduce((sum, value) => sum + value, 0)).toBeCloseTo(100, 10);
  });

  it('leaves an all-zero set at zero', () => {
    expect(largestRemainder([0, 0, 0])).toEqual([0, 0, 0]);
  });
});
