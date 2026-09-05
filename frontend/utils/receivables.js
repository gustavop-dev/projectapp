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

export const NO_RECEIVABLE_GROUP_KEY = 'none';

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

function groupIdentity(row, criterion) {
  const isProject = criterion === 'project';
  const id = isProject ? row?.project : row?.client;
  if (id == null) {
    return {
      id: NO_RECEIVABLE_GROUP_KEY,
      name: isProject ? 'Sin proyecto' : 'Sin cliente',
      isUnassigned: true,
    };
  }
  return {
    id,
    name: (
      isProject ? row?.project_name : row?.client_name
    ) || `${isProject ? 'Proyecto' : 'Cliente'} #${id}`,
    isUnassigned: false,
  };
}

function receivableTotals(rows = []) {
  return rows.reduce((totals, row) => ({
    count: totals.count + 1,
    total_amount: totals.total_amount + (Number(row?.total_amount) || 0),
    paid_amount: totals.paid_amount + (Number(row?.paid_amount) || 0),
    pending_amount: totals.pending_amount + (Number(row?.pending_amount) || 0),
  }), {
    count: 0,
    total_amount: 0,
    paid_amount: 0,
    pending_amount: 0,
  });
}

function compareReceivableGroups(left, right) {
  if (left.isUnassigned !== right.isUnassigned) return left.isUnassigned ? 1 : -1;
  if (left.total_amount !== right.total_amount) return right.total_amount - left.total_amount;
  return left.name.localeCompare(right.name, 'es', { sensitivity: 'base' });
}

/**
 * Group the candidate rows already visible in the modal. The endpoint remains
 * authoritative for row order; only the group bands are ordered here, biggest
 * original amount first with incomplete assignments kept in a trailing bucket.
 */
export function groupReceivables(rows = [], criterion = 'client') {
  const buckets = new Map();

  rows.forEach((row) => {
    const identity = groupIdentity(row, criterion);
    if (!buckets.has(identity.id)) {
      buckets.set(identity.id, { ...identity, rows: [] });
    }
    buckets.get(identity.id).rows.push(row);
  });

  return [...buckets.values()]
    .map((group) => ({ ...group, ...receivableTotals(group.rows) }))
    .sort(compareReceivableGroups);
}

/** Totals for exactly the filtered rows represented by a grouped view. */
export function sumReceivableGroups(groups = []) {
  return receivableTotals(groups.flatMap((group) => group.rows));
}
