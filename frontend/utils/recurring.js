import { formatMoney } from '~/utils/formatMoney';
import { largestRemainder, percentOf } from '~/utils/percent';

/** Bucket id for rows with no category; never collides with a real FK. */
export const UNCATEGORIZED_KEY = 'uncategorized';
export const UNCATEGORIZED_LABEL = 'Sin categoría';

/**
 * Format a monthly price in the record's own currency.
 *
 * COP stays in whole pesos; anything else keeps two decimals, because a
 * yearly USD charge prorated to a month is often under a dollar and
 * rounding it would show "$1" for $0,92.
 */
export function formatMonthlyPrice(row) {
  const currency = row?.currency || 'COP';
  return formatMoney(row?.monthly_price, currency, {
    decimals: currency === 'COP' ? 0 : 2,
  });
}

/** Format the COP equivalent of a monthly cost. Always whole pesos. */
export function formatMonthlyCop(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

/** Sum the monthly COP cost of a list of rows. */
export function sumMonthlyCop(rows = []) {
  return rows.reduce((total, row) => total + (Number(row.monthly_cop_cost) || 0), 0);
}

/**
 * Group rows into display buckets, one per category, in the catalog's own
 * order. Empty categories are skipped; uncategorized rows collect into a
 * trailing bucket so nothing silently disappears from the table.
 *
 * Row order inside each group is preserved, so whatever the API returned —
 * which is the manual order the operator dragged — survives untouched.
 */
export function groupByCategory(rows = [], categories = []) {
  const buckets = new Map();
  categories.forEach((category) => {
    buckets.set(category.id, { id: category.id, name: category.name, rows: [] });
  });

  const uncategorized = { id: UNCATEGORIZED_KEY, name: UNCATEGORIZED_LABEL, rows: [] };

  rows.forEach((row) => {
    const bucket = row.category != null ? buckets.get(row.category) : null;
    (bucket || uncategorized).rows.push(row);
  });

  const groups = [...buckets.values()].filter((group) => group.rows.length > 0);
  if (uncategorized.rows.length) groups.push(uncategorized);

  return groups.map((group) => ({
    ...group,
    monthlyCopTotal: sumMonthlyCop(group.rows),
  }));
}

/**
 * Attach `groupWeightPct` to each group: the group's ACTIVE monthly COP cost
 * as a share of `base` (the active total across all groups). Group headers
 * are read together as a complete set, so the shares go through
 * largestRemainder() and add up to exactly 100.0. Base <= 0 → all zeros.
 */
export function withGroupWeights(groups = [], base = 0) {
  const raw = groups.map((group) =>
    percentOf(
      group.rows.reduce(
        (total, row) => total + (row.is_active ? Number(row.monthly_cop_cost) || 0 : 0),
        0,
      ),
      base,
    ));
  const rounded = largestRemainder(raw);
  return groups.map((group, index) => ({
    ...group,
    groupWeightPct: rounded[index],
  }));
}
