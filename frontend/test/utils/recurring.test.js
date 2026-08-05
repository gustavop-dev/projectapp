import {
  formatMonthlyCop,
  formatMonthlyPrice,
  groupByCategory,
  sumMonthlyCop,
  withGroupWeights,
  UNCATEGORIZED_KEY,
} from '../../utils/recurring';

describe('formatMonthlyPrice', () => {
  it('keeps two decimals for foreign currencies so sub-dollar costs survive', () => {
    // NameCheap: $10,98 USD a year is $0,92 a month, not "$1".
    expect(formatMonthlyPrice({ monthly_price: '0.92', currency: 'USD' }))
      .toBe('$0,92 USD');
  });

  it('shows COP in whole pesos', () => {
    expect(formatMonthlyPrice({ monthly_price: '32900.00', currency: 'COP' }))
      .toBe('$32.900 COP');
  });

  it('defaults to COP when the row has no currency', () => {
    expect(formatMonthlyPrice({ monthly_price: '1000' })).toBe('$1.000 COP');
  });
});

describe('formatMonthlyCop', () => {
  it('formats whole pesos', () => {
    expect(formatMonthlyCop('4499.00')).toBe('$4.499 COP');
  });

  it('treats a missing value as zero', () => {
    expect(formatMonthlyCop(undefined)).toBe('$0 COP');
  });
});

describe('sumMonthlyCop', () => {
  it('adds the monthly COP cost of every row', () => {
    expect(sumMonthlyCop([
      { monthly_cop_cost: '800000.00' },
      { monthly_cop_cost: '80000.00' },
    ])).toBe(880000);
  });

  it('is zero for an empty list', () => {
    expect(sumMonthlyCop([])).toBe(0);
  });
});

describe('groupByCategory', () => {
  const categories = [
    { id: 1, name: 'Suscripciones de IA', order: 0 },
    { id: 2, name: 'Infraestructura', order: 1 },
    { id: 3, name: 'Vacía', order: 2 },
  ];

  it('groups rows in catalog order and skips empty categories', () => {
    const rows = [
      { id: 10, category: 2, monthly_cop_cost: '32900.00' },
      { id: 11, category: 1, monthly_cop_cost: '800000.00' },
    ];

    const groups = groupByCategory(rows, categories);

    expect(groups.map((g) => g.name)).toEqual([
      'Suscripciones de IA', 'Infraestructura',
    ]);
  });

  it('preserves the row order it was given, which is the manual order', () => {
    const rows = [
      { id: 11, category: 1, monthly_cop_cost: '800000.00' },
      { id: 10, category: 1, monthly_cop_cost: '80000.00' },
    ];

    const [group] = groupByCategory(rows, categories);

    expect(group.rows.map((r) => r.id)).toEqual([11, 10]);
  });

  it('subtotals each group in monthly COP', () => {
    const rows = [
      { id: 11, category: 1, monthly_cop_cost: '800000.00' },
      { id: 12, category: 1, monthly_cop_cost: '80000.00' },
    ];

    const [group] = groupByCategory(rows, categories);

    expect(group.monthlyCopTotal).toBe(880000);
  });

  it('collects uncategorized rows into a trailing bucket', () => {
    const rows = [
      { id: 10, category: null, monthly_cop_cost: '1000.00' },
      { id: 11, category: 1, monthly_cop_cost: '800000.00' },
    ];

    const groups = groupByCategory(rows, categories);

    expect(groups.at(-1)).toMatchObject({
      id: UNCATEGORIZED_KEY,
      name: 'Sin categoría',
      monthlyCopTotal: 1000,
    });
  });

  it('does not drop rows whose category is no longer in the catalog', () => {
    const rows = [{ id: 10, category: 999, monthly_cop_cost: '500.00' }];

    const groups = groupByCategory(rows, categories);

    expect(groups).toHaveLength(1);
    expect(groups[0].id).toBe(UNCATEGORIZED_KEY);
    expect(groups[0].rows.map((r) => r.id)).toEqual([10]);
  });

  it('returns no groups when there are no rows', () => {
    expect(groupByCategory([], categories)).toEqual([]);
  });
});

describe('withGroupWeights', () => {
  const groups = [
    { id: 1, name: 'IA', rows: [{ is_active: true, monthly_cop_cost: '100' }] },
    { id: 2, name: 'Infra', rows: [{ is_active: true, monthly_cop_cost: '100' }] },
    { id: 3, name: 'Otros', rows: [{ is_active: true, monthly_cop_cost: '100' }] },
  ];

  it('makes the group headers sum to exactly 100.0 despite thirds', () => {
    const weighted = withGroupWeights(groups, 300);
    const sum = weighted.reduce((total, group) => total + group.groupWeightPct, 0);
    expect(sum).toBeCloseTo(100, 10);
  });

  it('excludes inactive rows from a group\'s weight', () => {
    const mixed = [
      { id: 1, name: 'IA', rows: [{ is_active: true, monthly_cop_cost: '100' }] },
      {
        id: 2,
        name: 'Infra',
        rows: [
          { is_active: true, monthly_cop_cost: '100' },
          { is_active: false, monthly_cop_cost: '9999' },
        ],
      },
    ];
    const weighted = withGroupWeights(mixed, 200);
    expect(weighted.map((group) => group.groupWeightPct)).toEqual([50, 50]);
  });

  it('gives every group 0% when the base is zero', () => {
    const weighted = withGroupWeights(groups, 0);
    expect(weighted.map((group) => group.groupWeightPct)).toEqual([0, 0, 0]);
  });
});
