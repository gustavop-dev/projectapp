/**
 * Pure helpers feeding the accounting dashboard charts.
 */

/** Slice summary.monthly (12 rows) to the inclusive 1-12 month range. */
export function sliceMonthly(monthly, fromMonth = 1, toMonth = 12) {
  const rows = Array.isArray(monthly) ? monthly : [];
  const from = Math.min(fromMonth, toMonth);
  const to = Math.max(fromMonth, toMonth);
  return rows.slice(from - 1, to);
}

/** Apex series + categories for the expected/liquid/expenses evolution. */
export function monthlySeries(monthly) {
  const rows = Array.isArray(monthly) ? monthly : [];
  return {
    categories: rows.map((row) => row.label),
    series: [
      { name: 'Esperado', data: rows.map((row) => Number(row.expected) || 0) },
      { name: 'Líquido', data: rows.map((row) => Number(row.liquid) || 0) },
      { name: 'Gastos', data: rows.map((row) => Number(row.expenses) || 0) },
    ],
  };
}

/**
 * Group card snapshots into one datetime series per card (fixed
 * alphabetical order so colors follow the entity across filters).
 */
export function cardDebtSeries(snapshots, { fromMonth = 1, toMonth = 12 } = {}) {
  const rows = Array.isArray(snapshots) ? snapshots : [];
  const from = Math.min(fromMonth, toMonth);
  const to = Math.max(fromMonth, toMonth);
  const byCard = new Map();
  for (const row of rows) {
    if (!row.snapshot_date) continue;
    const month = Number(String(row.snapshot_date).slice(5, 7));
    if (month < from || month > to) continue;
    if (!byCard.has(row.card_name)) byCard.set(row.card_name, []);
    byCard.get(row.card_name).push({
      x: row.snapshot_date,
      y: Number(row.debt_amount) || 0,
    });
  }
  return [...byCard.keys()].sort().map((card) => ({
    name: card,
    data: byCard.get(card).sort((a, b) => a.x.localeCompare(b.x)),
  }));
}
