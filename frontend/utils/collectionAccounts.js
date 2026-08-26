export const NO_COLLECTION_GROUP_KEY = 'none';

const STATUS_KEYS = ['draft', 'issued', 'overdue', 'paid', 'cancelled'];

function amountOf(row) {
  return Number(row?.total) || 0;
}

function emptyTotals() {
  return {
    count: 0,
    emitted: 0,
    pending: 0,
    collected: 0,
    cancelled: 0,
    statusCounts: Object.fromEntries(STATUS_KEYS.map((key) => [key, 0])),
  };
}

function totalsFor(rows) {
  return rows.reduce((totals, row) => {
    const amount = amountOf(row);
    const status = row.commercial_status;

    totals.count += 1;
    if (STATUS_KEYS.includes(status)) totals.statusCounts[status] += 1;
    if (status === 'issued' && row.is_overdue) totals.statusCounts.overdue += 1;
    if (status === 'issued' || status === 'paid') totals.emitted += amount;
    if (status === 'issued') totals.pending += amount;
    if (status === 'paid') totals.collected += amount;
    if (status === 'cancelled') totals.cancelled += amount;
    return totals;
  }, emptyTotals());
}

function clientIdentity(row) {
  if (row.client == null) {
    return { id: NO_COLLECTION_GROUP_KEY, name: 'Sin cliente', isUnassigned: true };
  }
  return {
    id: row.client,
    name: row.client_display_name || row.customer_name || `Cliente #${row.client}`,
  };
}

function projectIdentity(row) {
  if (row.project_id != null) {
    return {
      id: row.project_id,
      name: row.project_name || `Proyecto #${row.project_id}`,
    };
  }

  const snapshotName = String(row.project_name || '').trim();
  if (snapshotName) {
    return {
      id: `historical:${snapshotName}`,
      name: `${snapshotName} (histórico)`,
      isHistorical: true,
    };
  }

  return { id: NO_COLLECTION_GROUP_KEY, name: 'Sin proyecto', isUnassigned: true };
}

function compareGroups(a, b) {
  if (a.isUnassigned !== b.isUnassigned) return a.isUnassigned ? 1 : -1;
  if (a.pending !== b.pending) return b.pending - a.pending;
  return a.name.localeCompare(b.name, 'es', { sensitivity: 'base' });
}

/**
 * Groups the filtered collection-account rows by one business identity.
 * The grouping is intentionally one level deep; a second dimension remains
 * available through the existing filters.
 */
export function groupCollectionAccounts(rows = [], criterion = 'client') {
  const identityOf = criterion === 'project' ? projectIdentity : clientIdentity;
  const buckets = new Map();

  rows.forEach((row) => {
    const identity = identityOf(row);
    if (!buckets.has(identity.id)) buckets.set(identity.id, { ...identity, rows: [] });
    buckets.get(identity.id).rows.push(row);
  });

  return [...buckets.values()]
    .map((group) => ({ ...group, ...totalsFor(group.rows) }))
    .sort(compareGroups);
}

/** Totals for exactly the rows represented by the filtered groups. */
export function sumCollectionAccountGroups(groups = []) {
  return groups.reduce((totals, group) => {
    totals.count += group.count;
    totals.emitted += group.emitted;
    totals.pending += group.pending;
    totals.collected += group.collected;
    totals.cancelled += group.cancelled;
    STATUS_KEYS.forEach((key) => {
      totals.statusCounts[key] += group.statusCounts?.[key] || 0;
    });
    return totals;
  }, emptyTotals());
}
