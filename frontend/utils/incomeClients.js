import { largestRemainder, percentOf } from '~/utils/percent';

/** Bucket id for incomes with no client; never collides with a real FK. */
export const NO_CLIENT_KEY = 'none';
export const NO_CLIENT_LABEL = 'Sin cliente';

function toNumber(value) {
  return Number(value) || 0;
}

/**
 * Totals of one client's incomes.
 *
 * `billed` is what was projected (expected records) and `collected` what
 * actually arrived (liquid records) — they are separate rows in the ledger,
 * so summing everything together would double-count a settled income.
 * `pending` comes from the server-computed `pending_amount`, which already
 * credits linked deductions, instead of being re-derived here.
 */
function totalsFor(rows) {
  return rows.reduce(
    (totals, row) => {
      if (row.kind === 'expected') {
        totals.billed += toNumber(row.total_amount);
        totals.pending += toNumber(row.pending_amount);
      } else if (row.kind === 'liquid') {
        totals.collected += toNumber(row.total_amount);
      } else if (row.kind === 'lost') {
        totals.lost += toNumber(row.total_amount);
      }
      return totals;
    },
    { billed: 0, collected: 0, pending: 0, lost: 0 },
  );
}

/**
 * Group income rows by client, biggest billed amount first, with the
 * unassigned rows collecting into a trailing "Sin cliente" bucket so the
 * pending completion work stays visible instead of disappearing.
 *
 * Operates on whatever rows it receives — the page passes the FILTERED
 * ones, so the active period and filters define the scope.
 */
export function groupByClient(rows = []) {
  const buckets = new Map();

  rows.forEach((row) => {
    const id = row.client ?? NO_CLIENT_KEY;
    if (!buckets.has(id)) {
      buckets.set(id, {
        id,
        name: row.client ? (row.client_name || `Cliente #${row.client}`) : NO_CLIENT_LABEL,
        rows: [],
      });
    }
    buckets.get(id).rows.push(row);
  });

  const groups = [...buckets.values()].map((group) => ({
    ...group,
    count: group.rows.length,
    ...totalsFor(group.rows),
  }));

  const named = groups.filter((group) => group.id !== NO_CLIENT_KEY);
  const unassigned = groups.filter((group) => group.id === NO_CLIENT_KEY);
  named.sort((a, b) => b.billed - a.billed);
  return [...named, ...unassigned];
}

/**
 * Attach `weightPct`: each group's billed amount as a share of the total.
 * The shares are read together as a set, so largestRemainder() keeps them
 * adding up to exactly 100.0. A zero base yields all zeros.
 */
export function withClientWeights(groups = []) {
  const base = groups.reduce((total, group) => total + group.billed, 0);
  const rounded = largestRemainder(
    groups.map((group) => percentOf(group.billed, base)),
  );
  return groups.map((group, index) => ({ ...group, weightPct: rounded[index] }));
}

/** Sum a set of groups into the modal's footer row. */
export function sumClientGroups(groups = []) {
  return groups.reduce(
    (totals, group) => ({
      count: totals.count + group.count,
      billed: totals.billed + group.billed,
      collected: totals.collected + group.collected,
      pending: totals.pending + group.pending,
      lost: totals.lost + group.lost,
    }),
    { count: 0, billed: 0, collected: 0, pending: 0, lost: 0 },
  );
}
