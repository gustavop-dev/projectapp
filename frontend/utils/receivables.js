export const RECEIVABLE_CONFIDENCE = [
  {
    value: 'high',
    label: 'Cobro muy probable',
    shortLabel: 'Verde',
    badgeVariant: 'success',
  },
  {
    value: 'medium',
    label: 'Cobro incierto (50/50)',
    shortLabel: 'Naranja',
    badgeVariant: 'warning',
  },
  {
    value: 'low',
    label: 'Alto riesgo de pérdida',
    shortLabel: 'Rojo',
    badgeVariant: 'danger',
  },
];

export const RECEIVABLE_CONFIDENCE_OPTIONS = [
  { value: '', label: 'Sin clasificar' },
  ...RECEIVABLE_CONFIDENCE.map(({ value, label }) => ({ value, label })),
];

export function confidenceDefinition(value) {
  return RECEIVABLE_CONFIDENCE.find((item) => item.value === value) || {
    value: '',
    label: 'Sin clasificar',
    shortLabel: 'Sin clasificar',
    badgeVariant: 'neutral',
  };
}

export function isReceivableEligible(row) {
  return row?.kind === 'expected'
    && row?.ledger === 'company'
    && ['pending', 'partial'].includes(row?.payment_status);
}

function emptyGroup() {
  return { count: 0, total_amount: 0, paid_amount: 0, pending_amount: 0 };
}

export function buildReceivablesSummary(rows = []) {
  const byConfidence = {
    high: emptyGroup(),
    medium: emptyGroup(),
    low: emptyGroup(),
    unclassified: emptyGroup(),
  };
  const selectedRows = rows.filter((row) => row.is_receivable_candidate);
  selectedRows.forEach((row) => {
    const key = row.collection_confidence || 'unclassified';
    const group = byConfidence[key] || byConfidence.unclassified;
    group.count += 1;
    group.total_amount += Number(row.total_amount) || 0;
    group.paid_amount += Number(row.paid_amount) || 0;
    group.pending_amount += Number(row.pending_amount) || 0;
  });
  return {
    high_total: byConfidence.high.total_amount,
    high_count: byConfidence.high.count,
    selected_count: selectedRows.length,
    selected_total: selectedRows.reduce(
      (sum, row) => sum + (Number(row.total_amount) || 0), 0,
    ),
    paid_total: selectedRows.reduce(
      (sum, row) => sum + (Number(row.paid_amount) || 0), 0,
    ),
    pending_total: selectedRows.reduce(
      (sum, row) => sum + (Number(row.pending_amount) || 0), 0,
    ),
    by_confidence: byConfidence,
  };
}
