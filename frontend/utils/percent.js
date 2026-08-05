/**
 * Percentage helpers for the accounting composition tabs (pocket, hostings,
 * recurring, ads, cards): each row's weight over the table's total.
 *
 * Rounding policy: row percentages round independently to one decimal. The
 * worst-case drift of the visible sum is ±0.05% per row — under half a point
 * for the volumes these tabs handle — and no table renders a "sum of %" cell,
 * so the drift is invisible. Group headers, which ARE read together as a
 * complete set, go through largestRemainder() so they add up to exactly 100.0.
 */

/** Percentage of `value` over `total`, unrounded. Total 0/negative/NaN → 0. */
export function percentOf(value, total) {
  const numerator = Number(value);
  const denominator = Number(total);
  if (!Number.isFinite(numerator) || !Number.isFinite(denominator) || denominator <= 0) {
    return 0;
  }
  return (numerator / denominator) * 100;
}

/**
 * Format a percentage for display: es-CO locale, up to `decimals` fraction
 * digits (whole values stay bare: 25 → "25%", 12.34 → "12,3%"). Not clamped —
 * a historical card snapshot can legitimately exceed 100% of today's debt.
 */
export function formatPercent(percent, { decimals = 1 } = {}) {
  const value = Number(percent);
  const safe = Number.isFinite(value) ? value : 0;
  const formatted = new Intl.NumberFormat('es-CO', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(safe);
  return `${formatted}%`;
}

/**
 * Decorate rows with a numeric, unrounded `weight_pct` field: the row's share
 * of the table total. `getValue(row)` is the row's contribution (return 0 for
 * rows that must show 0% and stay out of the base, e.g. inactive records).
 * The base defaults to the sum of contributions; pass `base` when the total
 * lives elsewhere (cards: current debt across latest snapshots).
 */
export function addWeightPct(rows = [], getValue, { base } = {}) {
  const total = base !== undefined
    ? Number(base)
    : rows.reduce((sum, row) => sum + (Number(getValue(row)) || 0), 0);
  return rows.map((row) => ({
    ...row,
    weight_pct: percentOf(getValue(row), total),
  }));
}

/**
 * Round a set of percentages to `decimals` so the rounded values keep the
 * input's exact sum (largest-remainder method). An input summing to ~100
 * comes out summing to exactly 100.0; an all-zero input stays all zeros.
 * Order is preserved.
 */
export function largestRemainder(percents = [], { decimals = 1 } = {}) {
  const factor = 10 ** decimals;
  const scaled = percents.map((value) => {
    const safe = Number.isFinite(Number(value)) ? Number(value) : 0;
    return safe * factor;
  });
  const floors = scaled.map(Math.floor);
  const targetTotal = Math.round(scaled.reduce((sum, value) => sum + value, 0));
  let leftover = targetTotal - floors.reduce((sum, value) => sum + value, 0);

  const byRemainder = scaled
    .map((value, index) => ({ index, remainder: value - floors[index] }))
    .sort((a, b) => b.remainder - a.remainder);

  const result = [...floors];
  for (const { index } of byRemainder) {
    if (leftover <= 0) break;
    result[index] += 1;
    leftover -= 1;
  }
  return result.map((value) => value / factor);
}
