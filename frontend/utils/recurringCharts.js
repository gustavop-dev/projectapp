import { largestRemainder, percentOf } from '~/utils/percent';
import {
  UNCATEGORIZED_KEY,
  UNCATEGORIZED_LABEL,
  countsTowardRecurringBudget,
  sumMonthlyCop,
} from '~/utils/recurring';

/**
 * Aggregations behind the recurring-payments charts modal.
 *
 * Every figure here is built on `monthly_cop_cost` — the server-prorated
 * monthly equivalent — and never on the raw `price`. A domain renewed every
 * three years costs $161.964 per charge and $4.499 per month; charting the
 * former would rank GoDaddy above Netflix when it is in fact an order of
 * magnitude cheaper.
 */

/** Bucket key for the categories folded past the palette's slot count. */
export const OTHER_CATEGORIES_KEY = 'other-categories';
export const OTHER_CATEGORIES_LABEL = 'Otras categorías';

/** Same, for the items of a single category once the donut drills into one. */
export const OTHER_ITEMS_KEY = 'other-items';
export const OTHER_ITEMS_LABEL = 'Otros ítems';

const DAYS_IN_MONTH_MAX = 31;

/**
 * Fixed value order per split field, so a share keeps its color when the
 * other one overtakes it. Sorting these by weight would mean a filter that
 * flips which currency dominates also swaps the two colors, and a reader who
 * learned "blue is COP" is then misled.
 */
export const SPLIT_ORDERS = {
  currency: ['COP', 'USD'],
  payment_method: ['credit_card', 'cash'],
  cost_type: ['fixed', 'variable'],
};

/**
 * Rows the charts should count. Inactive payments are out by default: a
 * cancelled subscription sits at $0 and contributes nothing to a
 * distribution, but it still claims a legend entry and a color slot.
 */
export function visibleRows(rows = []) {
  return rows.filter(countsTowardRecurringBudget);
}

/** Monthly COP cost of a single row, coerced. */
function monthlyCop(row) {
  return Number(row?.monthly_cop_cost) || 0;
}

/**
 * Attach exact-summing percentages to a list of `{ total }` buckets.
 *
 * These are read together as a complete set — a donut legend, a stacked bar —
 * so they go through largestRemainder() and add up to exactly 100,0, unlike
 * the table's per-row weights which round independently.
 */
function withExactPercents(buckets, base) {
  const rounded = largestRemainder(buckets.map((bucket) => percentOf(bucket.total, base)));
  return buckets.map((bucket, index) => ({ ...bucket, pct: rounded[index] }));
}

/**
 * Monthly COP totals per category, in the catalog's own order, with a
 * trailing bucket for rows the operator never categorized.
 *
 * Empty categories are dropped: a slice of zero is an invisible arc and a
 * wasted legend row.
 */
export function totalsByCategory(rows = [], categories = []) {
  const buckets = new Map(
    categories.map((category) => [
      category.id,
      { key: category.id, id: category.id, name: category.name, total: 0 },
    ]),
  );
  const uncategorized = {
    key: UNCATEGORIZED_KEY,
    id: UNCATEGORIZED_KEY,
    name: UNCATEGORIZED_LABEL,
    total: 0,
  };

  rows.forEach((row) => {
    const bucket = (row.category != null && buckets.get(row.category)) || uncategorized;
    bucket.total += monthlyCop(row);
  });

  const entries = [...buckets.values()].filter((bucket) => bucket.total > 0);
  if (uncategorized.total > 0) entries.push(uncategorized);

  return withExactPercents(entries, sumMonthlyCop(rows));
}

/**
 * Collapse the buckets the palette cannot color into a single trailing slice.
 *
 * The reason to fold is palette exhaustion, which is true of any bucket list:
 * categories in the general view, and the items of one category once the donut
 * drills into it — hence the caller-supplied key and label.
 *
 * Which ones fold is decided by position, not by weight: a weight-based tail
 * would reshuffle the donut every time a filter changes the ranking. For
 * categories the position is the catalog order the operator drags, so they
 * control which categories keep a hue.
 *
 * Only the CHART folds — the legend keeps listing every bucket with its own
 * value, because it doubles as the table view and nothing may be hidden there.
 */
export function foldChartBuckets(
  buckets = [],
  slotCount = 4,
  { key = OTHER_CATEGORIES_KEY, label = OTHER_CATEGORIES_LABEL } = {},
) {
  if (buckets.length <= slotCount) return [...buckets];

  const kept = buckets.slice(0, slotCount);
  const folded = buckets.slice(slotCount);

  return [
    ...kept,
    {
      key,
      id: key,
      // A single folded bucket keeps its own name: calling one leftover
      // category "Otras categorías (1)" hides a name the reader could have had.
      name: folded.length === 1
        ? folded[0].name
        : `${label} (${folded.length})`,
      total: folded.reduce((sum, bucket) => sum + bucket.total, 0),
      pct: folded.reduce((sum, bucket) => sum + bucket.pct, 0),
    },
  ];
}

/**
 * Payments ranked by monthly COP cost, richest first.
 *
 * Carries the original price, currency and periodicity alongside the
 * normalized figure so the tooltip can show both — "$4.499/mes" alone hides
 * that the charge is really $161.964 every three years.
 */
export function itemsByMonthlyCost(rows = []) {
  const items = [...rows]
    .map((row) => ({
      key: row.id,
      id: row.id,
      name: row.name,
      total: monthlyCop(row),
      categoryId: row.category ?? UNCATEGORIZED_KEY,
      price: Number(row.price) || 0,
      currency: row.currency || 'COP',
      frequencyLabel: row.frequency_label || '',
      isActive: Boolean(row.is_active),
    }))
    .sort((a, b) => b.total - a.total);

  return withExactPercents(items, sumMonthlyCop(rows));
}

/**
 * Monthly COP split across the values of one field (currency, payment
 * method, cost type). Reads `<field>_label` when the API exposes one, the
 * same convention the store's `recurringMonthlyTotalsBy` getter follows.
 *
 * Buckets come out in the field's fixed order (see SPLIT_ORDERS), with any
 * unrecognized value trailing in insertion order.
 */
export function splitBy(rows = [], field) {
  const buckets = new Map();

  rows.forEach((row) => {
    const key = row[field];
    if (key == null || key === '') return;
    const label = row[`${field}_label`] || String(key);
    const bucket = buckets.get(key) || { key, label, total: 0 };
    bucket.total += monthlyCop(row);
    buckets.set(key, bucket);
  });

  const order = SPLIT_ORDERS[field] || [];
  const rank = (key) => {
    const index = order.indexOf(key);
    return index === -1 ? order.length : index;
  };
  const entries = [...buckets.values()].sort((a, b) => rank(a.key) - rank(b.key));

  return withExactPercents(entries, sumMonthlyCop(rows));
}

/**
 * Monthly COP laid out across the days of the month.
 *
 * Two things the caller has to surface rather than bury:
 * - `withoutDay` collects the payments with no `billing_day`. It is not a
 *   rounding error — today it holds the two ad budgets, over half the
 *   monthly spend — and folding it into the axis or dropping it would make
 *   the chart lie about where the money leaves.
 * - `proratedDays` marks the days carrying at least one non-monthly payment,
 *   whose amount is an amortized twelfth (or thirty-sixth), not a charge that
 *   actually lands every month.
 */
export function byBillingDay(rows = []) {
  const days = Array.from({ length: DAYS_IN_MONTH_MAX }, (_, index) => ({
    day: index + 1,
    total: 0,
    names: [],
    prorated: false,
  }));
  const withoutDayRows = [];

  rows.forEach((row) => {
    const day = Number(row.billing_day);
    if (!Number.isInteger(day) || day < 1 || day > DAYS_IN_MONTH_MAX) {
      withoutDayRows.push(row);
      return;
    }
    const bucket = days[day - 1];
    bucket.total += monthlyCop(row);
    bucket.names.push(row.name);
    if (row.frequency && row.frequency !== 'monthly') bucket.prorated = true;
  });

  const total = sumMonthlyCop(rows);
  const withoutDayTotal = sumMonthlyCop(withoutDayRows);

  return {
    days,
    scheduledTotal: total - withoutDayTotal,
    withoutDay: {
      total: withoutDayTotal,
      pct: percentOf(withoutDayTotal, total),
      names: withoutDayRows.map((row) => row.name),
    },
  };
}

/**
 * Stable category → color map.
 *
 * Three rules, all of them load-bearing:
 * - the hue follows the category's slot in the catalog, never its current
 *   value, so filtering the chart cannot repaint the survivors;
 * - "Sin categoría" is always the neutral ink — it is an absence, not an
 *   entity that deserves a hue of its own;
 * - past the palette's slot count categories share that same neutral instead
 *   of getting generated hues, which would be indistinguishable from the
 *   existing ones under color-vision deficiency. The chart folds them into
 *   one slice (see foldChartBuckets); the legend still names each of them.
 */
export function categoryColorMap(categories = [], categoricalPalette = [], neutral = '#9CA3AF') {
  const colors = new Map();
  categories.forEach((category, index) => {
    colors.set(category.id, categoricalPalette[index] || neutral);
  });
  colors.set(UNCATEGORIZED_KEY, neutral);
  colors.set(OTHER_CATEGORIES_KEY, neutral);
  return colors;
}
