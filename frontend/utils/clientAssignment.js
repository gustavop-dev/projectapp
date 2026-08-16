import { clientLabelOf } from '~/utils/incomeClients';

/**
 * Bulk client (un)assignment: everything the confirmation needs to say, with
 * no Vue in the way.
 *
 * Assigning and unlinking used to be the same button — a filled picker meant
 * "assign", an empty one meant "unlink" — so the operator only learned the
 * scope of a mass edit after it had happened. These helpers turn a selection
 * into an explicit plan (who gains a client, who changes one, who loses it,
 * who is already there) so the UI can name the operation before running it.
 */

/**
 * Turn a selection into the groups the confirmation talks about.
 *
 * Resolves ids against the FULL record list rather than the filtered rows:
 * the selection outlives filter and page changes, so it legitimately holds
 * ids that are off-screen. Ids with no matching record (deleted elsewhere,
 * or a stale refetch) are dropped — the backend would skip them anyway.
 *
 * `mode`:
 * - 'assign' splits the selection into `toAssign` (no client yet),
 *   `toReassign` (pointing somewhere else) and `unchanged` (already on the
 *   target, which the backend skips without writing).
 * - 'unlink' collects every selected row that has a client into `toUnlink`;
 *   rows without one are already where unlinking would leave them.
 */
export function buildAssignmentPlan({
  rows = [],
  selectedIds = [],
  mode = 'assign',
  targetClientId = null,
  targetClientLabel = '',
} = {}) {
  const byId = new Map(rows.map((row) => [row.id, row]));
  const selected = selectedIds
    .map((id) => byId.get(id))
    .filter(Boolean);

  const plan = {
    mode,
    targetClientId,
    targetClientLabel,
    selectedCount: selected.length,
    toAssign: [],
    toReassign: [],
    toUnlink: [],
    unchanged: [],
  };

  selected.forEach((row) => {
    if (mode === 'unlink') {
      if (row.client == null) plan.unchanged.push(row);
      else plan.toUnlink.push(row);
      return;
    }
    if (row.client == null) plan.toAssign.push(row);
    else if (row.client === targetClientId) plan.unchanged.push(row);
    else plan.toReassign.push(row);
  });

  plan.affected = mode === 'unlink'
    ? plan.toUnlink
    : [...plan.toAssign, ...plan.toReassign];

  // Source clients, biggest group first: the "de qué cliente" half of a
  // reassignment or an unlink. Rows without a client never enter here — they
  // have no origin to name.
  const buckets = new Map();
  plan.affected.forEach((row) => {
    if (row.client == null) return;
    const bucket = buckets.get(row.client)
      || { id: row.client, label: clientLabelOf(row), count: 0 };
    bucket.count += 1;
    buckets.set(row.client, bucket);
  });
  plan.byCurrentClient = [...buckets.values()].sort((a, b) => b.count - a.count);

  // Rows that will ALSO lose their project: the server clears `project`
  // whenever the client changes hands (a record must never point at someone
  // else's project). Only rows leaving a client qualify — a row with no
  // client being assigned one keeps a project its new client already owns.
  plan.projectCleared = (mode === 'unlink' ? plan.toUnlink : plan.toReassign)
    .filter((row) => row.project != null);

  return plan;
}

/** "2 de Kore SAS, 1 de Juan Pérez" — the origin breakdown, inline. */
function originList(groups) {
  return groups.map((group) => `${group.count} de ${group.label}`).join(', ');
}

/** Pluralised entity noun: 1 → 'hosting', 3 → 'hostings'. */
function countLabel(count, entity) {
  return `${count} ${count === 1 ? entity.singular : entity.plural}`;
}

/**
 * Sentence about the rows the backend will skip. Declared apart from the
 * affected count on purpose: the toast afterwards reports how many rows
 * actually changed, and the two numbers have to agree.
 */
function unchangedNote(plan, entity) {
  const count = plan.unchanged.length;
  if (count === 0) return '';
  if (plan.mode === 'unlink') {
    return ` ${countLabel(count, entity)} ya ${count === 1 ? 'está' : 'están'} sin cliente y no ${count === 1 ? 'cambia' : 'cambian'}.`;
  }
  return ` ${countLabel(count, entity)} ya ${count === 1 ? 'tiene' : 'tienen'} a ${plan.targetClientLabel} y no ${count === 1 ? 'cambia' : 'cambian'}.`;
}

/** The project side effect, said before it happens instead of after. */
function projectClearedNote(plan) {
  const count = plan.projectCleared?.length ?? 0;
  if (count === 0) return '';
  return ` ${count} ${count === 1 ? 'pierde' : 'pierden'} también su proyecto (era del cliente anterior).`;
}

/**
 * Copy for the confirmation, one message per scenario — assigning to rows
 * with no client, replacing the client of rows that already have one, the
 * mixed selection where both happen at once, and unlinking. A mixed
 * selection is never flattened into a single "assign N": the operator has to
 * see how many rows are being *taken* from another client.
 *
 * `entity` is `{ singular, plural }` ('hosting' / 'hostings').
 */
export function describeAssignmentPlan(plan, { entity }) {
  const target = plan.targetClientLabel || 'el cliente seleccionado';
  const note = `${unchangedNote(plan, entity)}${projectClearedNote(plan)}`;

  if (plan.mode === 'unlink') {
    const origins = originList(plan.byCurrentClient);
    return {
      title: 'Desvincular cliente',
      message: `${countLabel(plan.toUnlink.length, entity)} ${plan.toUnlink.length === 1 ? 'quedará' : 'quedarán'} sin cliente${origins ? `: ${origins}` : ''}.${note}`,
      confirmText: 'Desvincular',
      variant: 'danger',
    };
  }

  const assigning = plan.toAssign.length;
  const reassigning = plan.toReassign.length;

  if (reassigning > 0 && assigning > 0) {
    return {
      title: 'Asignar cliente',
      message: `Se asignará ${target} a ${countLabel(assigning + reassigning, entity)}: ${assigning} sin cliente y ${reassigning} que ${reassigning === 1 ? 'cambia' : 'cambian'} de cliente (${originList(plan.byCurrentClient)}).${note}`,
      confirmText: 'Asignar',
      variant: 'warning',
    };
  }

  if (reassigning > 0) {
    return {
      title: 'Cambiar el cliente',
      message: `${countLabel(reassigning, entity)} ${reassigning === 1 ? 'cambiará' : 'cambiarán'} de cliente a ${target}: ${originList(plan.byCurrentClient)}.${note}`,
      confirmText: 'Cambiar cliente',
      variant: 'warning',
    };
  }

  return {
    title: 'Asignar cliente',
    message: `Se asignará ${target} a ${countLabel(assigning, entity)} sin cliente.${note}`,
    confirmText: 'Asignar',
    variant: 'info',
  };
}

/**
 * Result toast after the call: how many rows the backend actually wrote.
 * `updated` comes back from the endpoint, which skips rows already pointing
 * at the target — so it can legitimately be lower than what was selected.
 */
export function describeAssignmentResult(plan, updated, { entity }) {
  const attempted = plan.affected.length;
  const verb = plan.mode === 'unlink' ? 'desvinculado' : 'actualizado';
  const base = `${updated} de ${countLabel(attempted, entity)} ${updated === 1 ? verb : `${verb}s`}`;
  return plan.unchanged.length > 0
    ? `${base}; ${plan.unchanged.length} sin cambios.`
    : `${base}.`;
}
