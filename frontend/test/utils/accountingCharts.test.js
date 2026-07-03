import {
  cardDebtSeries,
  monthlySeries,
  sliceMonthly,
} from '../../utils/accountingCharts';

const MONTHLY = Array.from({ length: 12 }, (_, index) => ({
  label: `Mes ${index + 1}`,
  expected: String((index + 1) * 100),
  liquid: String((index + 1) * 50),
  expenses: String((index + 1) * 20),
}));

describe('sliceMonthly', () => {
  it('slices the inclusive month range', () => {
    const rows = sliceMonthly(MONTHLY, 3, 5);
    expect(rows.map((r) => r.label)).toEqual(['Mes 3', 'Mes 4', 'Mes 5']);
  });

  it('swaps inverted bounds and tolerates non-arrays', () => {
    expect(sliceMonthly(MONTHLY, 5, 3)).toHaveLength(3);
    expect(sliceMonthly(null)).toEqual([]);
  });
});

describe('monthlySeries', () => {
  it('builds the three fixed series with numeric data', () => {
    const { series, categories } = monthlySeries(MONTHLY.slice(0, 2));
    expect(categories).toEqual(['Mes 1', 'Mes 2']);
    expect(series.map((s) => s.name)).toEqual(['Esperado', 'Líquido', 'Gastos']);
    expect(series[0].data).toEqual([100, 200]);
    expect(series[2].data).toEqual([20, 40]);
  });
});

describe('cardDebtSeries', () => {
  const SNAPSHOTS = [
    { card_name: 'T.C 0655', snapshot_date: '2026-06-05', debt_amount: '100' },
    { card_name: 'T.C 0064', snapshot_date: '2026-07-01', debt_amount: '900' },
    { card_name: 'T.C 0064', snapshot_date: '2026-06-17', debt_amount: '800' },
    { card_name: 'T.C 0064', snapshot_date: '2026-01-10', debt_amount: '50' },
  ];

  it('groups by card in fixed alphabetical order with sorted points', () => {
    const series = cardDebtSeries(SNAPSHOTS);
    expect(series.map((s) => s.name)).toEqual(['T.C 0064', 'T.C 0655']);
    expect(series[0].data.map((p) => p.x)).toEqual([
      '2026-01-10', '2026-06-17', '2026-07-01',
    ]);
    expect(series[0].data[1].y).toBe(800);
  });

  it('filters points to the month range', () => {
    const series = cardDebtSeries(SNAPSHOTS, { fromMonth: 6, toMonth: 6 });
    expect(series.map((s) => s.name)).toEqual(['T.C 0064', 'T.C 0655']);
    expect(series[0].data).toHaveLength(1);
    expect(series[0].data[0].x).toBe('2026-06-17');
  });
});
