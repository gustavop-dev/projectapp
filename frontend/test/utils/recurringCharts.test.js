import {
  OTHER_CATEGORIES_KEY,
  OTHER_ITEMS_KEY,
  byBillingDay,
  categoryColorMap,
  foldChartBuckets,
  itemsByMonthlyCost,
  splitBy,
  totalsByCategory,
  visibleRows,
} from '../../utils/recurringCharts';
import { UNCATEGORIZED_KEY } from '../../utils/recurring';

const CATEGORIES = [
  { id: 1, name: 'Suscripciones de IA' },
  { id: 2, name: 'Anuncios / publicidad' },
  { id: 3, name: 'Arquitectura e infraestructura' },
];

function payment(overrides = {}) {
  return {
    id: 1,
    name: 'Pago',
    price: '10000.00',
    currency: 'COP',
    monthly_price: '10000.00',
    monthly_cop_cost: '10000.00',
    payment_method: 'credit_card',
    payment_method_label: 'T.C',
    frequency: 'monthly',
    frequency_label: 'Mensual',
    cost_type: 'fixed',
    cost_type_label: 'Fijo',
    billing_day: 1,
    category: 1,
    is_active: true,
    ...overrides,
  };
}

describe('visibleRows', () => {
  it('drops inactive payments so a cancelled $0 row does not claim a legend slot', () => {
    const rows = [payment({ id: 1 }), payment({ id: 2, is_active: false })];
    expect(visibleRows(rows).map((row) => row.id)).toEqual([1]);
  });

  it('drops archived payments from every chart', () => {
    const rows = [payment({ id: 1 }), payment({ id: 2, is_archived: true })];
    expect(visibleRows(rows).map((row) => row.id)).toEqual([1]);
  });
});

describe('totalsByCategory', () => {
  it('totals each category in catalog order and shares add up to exactly 100', () => {
    const rows = [
      payment({ id: 1, category: 2, monthly_cop_cost: '1200000.00' }),
      payment({ id: 2, category: 1, monthly_cop_cost: '800000.00' }),
      payment({ id: 3, category: 3, monthly_cop_cost: '4499.00' }),
    ];

    const buckets = totalsByCategory(rows, CATEGORIES);

    expect(buckets.map((bucket) => [bucket.name, bucket.total])).toEqual([
      ['Suscripciones de IA', 800000],
      ['Anuncios / publicidad', 1200000],
      ['Arquitectura e infraestructura', 4499],
    ]);
    expect(buckets.reduce((sum, bucket) => sum + bucket.pct, 0)).toBe(100);
  });

  it('drops empty categories and collects uncategorized rows in a trailing bucket', () => {
    const rows = [
      payment({ id: 1, category: 1, monthly_cop_cost: '600000.00' }),
      payment({ id: 2, category: null, monthly_cop_cost: '400000.00' }),
    ];

    const buckets = totalsByCategory(rows, CATEGORIES);

    expect(buckets.map((bucket) => bucket.key)).toEqual([1, UNCATEGORIZED_KEY]);
    expect(buckets[1].pct).toBe(40);
  });

  it('is empty when there is nothing to distribute', () => {
    expect(totalsByCategory([], CATEGORIES)).toEqual([]);
  });
});

describe('foldChartBuckets', () => {
  it('folds what the palette cannot color into one slice instead of inventing hues', () => {
    const buckets = [1, 2, 3, 4, 5].map((id) => ({
      key: id, id, name: `Cat ${id}`, total: id * 100, pct: id,
    }));

    const folded = foldChartBuckets(buckets, 3);

    expect(folded).toHaveLength(4);
    expect(folded[3]).toMatchObject({ key: OTHER_CATEGORIES_KEY, total: 900, pct: 9 });
    expect(folded[3].name).toContain('(2)');
  });

  it('keeps a lone leftover under its own name rather than hiding it behind "Otras"', () => {
    const buckets = [1, 2].map((id) => ({ key: id, id, name: `Cat ${id}`, total: 10, pct: 50 }));
    expect(foldChartBuckets(buckets, 1)[1].name).toBe('Cat 2');
  });

  it('leaves the list untouched when every bucket fits', () => {
    const buckets = [{ key: 1, id: 1, name: 'Cat 1', total: 10, pct: 100 }];
    expect(foldChartBuckets(buckets, 4)).toEqual(buckets);
  });

  it('folds under the name the caller gives it, for the items of one category', () => {
    // Drilled into a category, the buckets are payments — "Otras categorías"
    // would be a lie about what got merged.
    const buckets = [1, 2, 3, 4, 5, 6].map((id) => ({
      key: id, id, name: `Pago ${id}`, total: 100, pct: 100 / 6,
    }));

    const folded = foldChartBuckets(buckets, 4, {
      key: OTHER_ITEMS_KEY,
      label: 'Otros ítems',
    });

    expect(folded).toHaveLength(5);
    expect(folded[4]).toMatchObject({ key: OTHER_ITEMS_KEY, id: OTHER_ITEMS_KEY, total: 200 });
    expect(folded[4].name).toBe('Otros ítems (2)');
  });

  it('names a lone leftover item after itself, whatever label the caller passed', () => {
    const buckets = [1, 2].map((id) => ({ key: id, id, name: `Pago ${id}`, total: 10, pct: 50 }));

    const folded = foldChartBuckets(buckets, 1, {
      key: OTHER_ITEMS_KEY,
      label: 'Otros ítems',
    });

    expect(folded[1].name).toBe('Pago 2');
  });

  it('still folds into the category bucket when no names are given', () => {
    const buckets = [1, 2].map((id) => ({ key: id, id, name: `Cat ${id}`, total: 10, pct: 50 }));
    expect(foldChartBuckets(buckets, 1)[1].key).toBe(OTHER_CATEGORIES_KEY);
  });
});

describe('itemsByMonthlyCost', () => {
  it('ranks by the monthly equivalent, not by the raw price', () => {
    const rows = [
      // A three-year domain: $161.964 per charge, $4.499 a month.
      payment({ id: 1, name: 'GoDaddy', price: '161964.00', monthly_cop_cost: '4499.00' }),
      payment({ id: 2, name: 'Netflix', price: '39800.00', monthly_cop_cost: '39800.00' }),
    ];

    expect(itemsByMonthlyCost(rows).map((item) => item.name)).toEqual(['Netflix', 'GoDaddy']);
  });

  it('carries the original price and periodicity for the tooltip', () => {
    const rows = [payment({
      name: 'NameCheap', price: '10.98', currency: 'USD',
      frequency: 'annual', frequency_label: 'Anual', monthly_cop_cost: '3660.00',
    })];

    expect(itemsByMonthlyCost(rows)[0]).toMatchObject({
      price: 10.98, currency: 'USD', frequencyLabel: 'Anual', total: 3660,
    });
  });
});

describe('splitBy', () => {
  it('splits the monthly total across a field using its own labels', () => {
    const rows = [
      payment({ id: 1, currency: 'COP', monthly_cop_cost: '700000.00' }),
      payment({ id: 2, currency: 'USD', monthly_cop_cost: '300000.00' }),
    ];

    expect(splitBy(rows, 'currency')).toEqual([
      { key: 'COP', label: 'COP', total: 700000, pct: 70 },
      { key: 'USD', label: 'USD', total: 300000, pct: 30 },
    ]);
  });

  it('holds the field order when the minority share overtakes the other', () => {
    // Colors follow the value, not its rank: USD leading must not repaint COP.
    const rows = [
      payment({ id: 1, currency: 'COP', monthly_cop_cost: '100000.00' }),
      payment({ id: 2, currency: 'USD', monthly_cop_cost: '900000.00' }),
    ];

    expect(splitBy(rows, 'currency').map((bucket) => bucket.key)).toEqual(['COP', 'USD']);
  });

  it('reads the label field the API exposes', () => {
    const rows = [payment({ payment_method: 'cash', payment_method_label: 'Efectivo' })];
    expect(splitBy(rows, 'payment_method')[0].label).toBe('Efectivo');
  });
});

describe('byBillingDay', () => {
  it('separates the payments with no billing day instead of dropping them', () => {
    // The two ad budgets carry no day and are over half the monthly spend.
    const rows = [
      payment({ id: 1, name: 'Google Ads', billing_day: null, monthly_cop_cost: '1200000.00' }),
      payment({ id: 2, name: 'FB Anuncios', billing_day: null, monthly_cop_cost: '400000.00' }),
      payment({ id: 3, name: 'Claude', billing_day: 8, monthly_cop_cost: '800000.00' }),
    ];

    const { withoutDay, scheduledTotal } = byBillingDay(rows);

    expect(withoutDay.total).toBe(1600000);
    expect(withoutDay.pct).toBeCloseTo(66.67, 1);
    expect(withoutDay.names).toEqual(['Google Ads', 'FB Anuncios']);
    expect(scheduledTotal).toBe(800000);
  });

  it('stacks same-day payments and names them for the tooltip', () => {
    const rows = [
      payment({ id: 1, name: 'Claude', billing_day: 8, monthly_cop_cost: '800000.00' }),
      payment({ id: 2, name: 'Netflix', billing_day: 8, monthly_cop_cost: '39800.00' }),
    ];

    const day = byBillingDay(rows).days[7];

    expect(day).toMatchObject({ day: 8, total: 839800, prorated: false });
    expect(day.names).toEqual(['Claude', 'Netflix']);
  });

  it('flags a day carrying a prorated charge that does not really land monthly', () => {
    const rows = [payment({ billing_day: 29, frequency: 'biennial', monthly_cop_cost: '32900.00' })];
    expect(byBillingDay(rows).days[28].prorated).toBe(true);
  });

  it('treats an out-of-range day as no day at all', () => {
    expect(byBillingDay([payment({ billing_day: 45 })]).withoutDay.total).toBe(10000);
  });
});

describe('categoryColorMap', () => {
  const PALETTE = ['#1D4ED8', '#B45309'];

  it('assigns hues by catalog position so filtering never repaints a category', () => {
    const map = categoryColorMap(CATEGORIES, PALETTE, '#9CA3AF');
    expect(map.get(1)).toBe('#1D4ED8');
    expect(map.get(2)).toBe('#B45309');
  });

  it('gives the neutral ink to what the palette cannot color', () => {
    const map = categoryColorMap(CATEGORIES, PALETTE, '#9CA3AF');
    expect(map.get(3)).toBe('#9CA3AF');
    expect(map.get(UNCATEGORIZED_KEY)).toBe('#9CA3AF');
    expect(map.get(OTHER_CATEGORIES_KEY)).toBe('#9CA3AF');
  });
});
