const formatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });

export function formatMoney(amount, currency = '') {
  if (amount === null || amount === undefined) return '';
  const n = Number(amount);
  if (!Number.isFinite(n)) return '';
  const formatted = formatter.format(n);
  return currency ? `$${formatted} ${currency}` : `$${formatted}`;
}

const compactFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 });

/**
 * Short money for chart axes: 1234567 -> "$1,2M", -850000 -> "-$850K".
 * Tooltips and KPIs keep the full formatMoney value.
 */
export function formatCompactMoney(amount) {
  if (amount === null || amount === undefined) return '';
  const n = Number(amount);
  if (!Number.isFinite(n)) return '';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1_000_000) return `${sign}$${compactFormatter.format(abs / 1_000_000)}M`;
  if (abs >= 1_000) return `${sign}$${compactFormatter.format(abs / 1_000)}K`;
  return `${sign}$${compactFormatter.format(abs)}`;
}
