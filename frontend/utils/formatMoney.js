const formatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });

export function formatMoney(amount, currency = '') {
  if (amount === null || amount === undefined) return '';
  const n = Number(amount);
  if (!Number.isFinite(n)) return '';
  const formatted = formatter.format(n);
  return currency ? `$${formatted} ${currency}` : `$${formatted}`;
}
