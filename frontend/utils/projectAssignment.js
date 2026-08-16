/**
 * Bulk project (un)assignment: everything the confirmation needs to say,
 * with no Vue in the way — the project mirror of `clientAssignment.js`.
 *
 * The extra group the client flavour does not have is
 * `blockedClientMismatch`: a project belongs to one client, so selected rows
 * of any OTHER client (or with no client at all) are excluded from the plan
 * and listed apart. The backend enforces the same rule with a 409; the plan
 * exists so the operator sees it before submitting, not after.
 */

const projectLabelOf = (row) => row.project_name || `Proyecto #${row.project}`;

/**
 * Turn a selection into the groups the confirmation talks about.
 *
 * Resolves ids against the FULL record list (the selection survives filter
 * and page changes); ids with no matching record are dropped — the backend
 * would 409 on them anyway and the page reconciles via `missing_ids`.
 *
 * `mode`:
 * - 'assign' needs `targetProject` (a catalog row carrying `id`, `name` and
 *   `client.profile_id`) and splits the selection into `toAssign` (no
 *   project yet), `toReassign` (pointing at another of the SAME client's
 *   projects), `unchanged` (already on target) and `blockedClientMismatch`
 *   (rows the action will not touch).
 * - 'unlink' collects every selected row that has a project into `toUnlink`;
 *   clearing needs no owner, so nothing is ever blocked.
 */
export function buildProjectAssignmentPlan({
  rows = [],
  selectedIds = [],
  mode = 'assign',
  targetProject = null,
} = {}) {
  const byId = new Map(rows.map((row) => [row.id, row]));
  const selected = selectedIds
    .map((id) => byId.get(id))
    .filter(Boolean);

  const targetProjectId = targetProject?.id ?? null;
  const targetClientProfileId = targetProject?.client?.profile_id ?? null;

  const plan = {
    mode,
    targetProjectId,
    targetProjectLabel: targetProject?.name ?? '',
    targetClientLabel: targetProject?.client?.name ?? '',
    selectedCount: selected.length,
    toAssign: [],
    toReassign: [],
    toUnlink: [],
    unchanged: [],
    blockedClientMismatch: [],
  };

  selected.forEach((row) => {
    if (mode === 'unlink') {
      if (row.project == null) plan.unchanged.push(row);
      else plan.toUnlink.push(row);
      return;
    }
    if (row.client == null || row.client !== targetClientProfileId) {
      plan.blockedClientMismatch.push(row);
      return;
    }
    if (row.project == null) plan.toAssign.push(row);
    else if (row.project === targetProjectId) plan.unchanged.push(row);
    else plan.toReassign.push(row);
  });

  plan.affected = mode === 'unlink'
    ? plan.toUnlink
    : [...plan.toAssign, ...plan.toReassign];

  // Source projects, biggest group first: the "de qué proyecto" half of a
  // reassignment or an unlink. Rows without a project have no origin to name.
  const buckets = new Map();
  plan.affected.forEach((row) => {
    if (row.project == null) return;
    const bucket = buckets.get(row.project)
      || { id: row.project, label: projectLabelOf(row), count: 0 };
    bucket.count += 1;
    buckets.set(row.project, bucket);
  });
  plan.byCurrentProject = [...buckets.values()].sort((a, b) => b.count - a.count);

  return plan;
}

/** "2 de Kore Web, 1 de Vastago" — the origin breakdown, inline. */
function originList(groups) {
  return groups.map((group) => `${group.count} de ${group.label}`).join(', ');
}

/** Pluralised entity noun: 1 → 'hosting', 3 → 'hostings'. */
function countLabel(count, entity) {
  return `${count} ${count === 1 ? entity.singular : entity.plural}`;
}

function unchangedNote(plan, entity) {
  const count = plan.unchanged.length;
  if (count === 0) return '';
  if (plan.mode === 'unlink') {
    return ` ${countLabel(count, entity)} ya ${count === 1 ? 'está' : 'están'} sin proyecto y no ${count === 1 ? 'cambia' : 'cambian'}.`;
  }
  return ` ${countLabel(count, entity)} ya ${count === 1 ? 'tiene' : 'tienen'} el proyecto y no ${count === 1 ? 'cambia' : 'cambian'}.`;
}

/** The rows the action deliberately leaves alone, named out loud. */
function blockedNote(plan, entity) {
  const count = plan.blockedClientMismatch.length;
  if (count === 0) return '';
  return ` ${countLabel(count, entity)} ${count === 1 ? 'pertenece' : 'pertenecen'} a otro cliente y no se ${count === 1 ? 'toca' : 'tocan'}: reasigna primero su cliente.`;
}

/**
 * Copy for the confirmation, one message per scenario, mirroring
 * `describeAssignmentPlan`. `entity` is `{ singular, plural }`.
 */
export function describeProjectAssignmentPlan(plan, { entity }) {
  const target = plan.targetProjectLabel
    ? `el proyecto "${plan.targetProjectLabel}"`
    : 'el proyecto seleccionado';
  const note = `${unchangedNote(plan, entity)}${blockedNote(plan, entity)}`;

  if (plan.mode === 'unlink') {
    const origins = originList(plan.byCurrentProject);
    return {
      title: 'Quitar proyecto',
      message: `${countLabel(plan.toUnlink.length, entity)} ${plan.toUnlink.length === 1 ? 'quedará' : 'quedarán'} sin proyecto${origins ? `: ${origins}` : ''}.${note}`,
      confirmText: 'Quitar proyecto',
      variant: 'danger',
    };
  }

  const assigning = plan.toAssign.length;
  const reassigning = plan.toReassign.length;

  if (reassigning > 0 && assigning > 0) {
    return {
      title: 'Asignar proyecto',
      message: `Se asignará ${target} a ${countLabel(assigning + reassigning, entity)}: ${assigning} sin proyecto y ${reassigning} que ${reassigning === 1 ? 'cambia' : 'cambian'} de proyecto (${originList(plan.byCurrentProject)}).${note}`,
      confirmText: 'Asignar',
      variant: 'warning',
    };
  }

  if (reassigning > 0) {
    return {
      title: 'Cambiar el proyecto',
      message: `${countLabel(reassigning, entity)} ${reassigning === 1 ? 'cambiará' : 'cambiarán'} de proyecto a ${target}: ${originList(plan.byCurrentProject)}.${note}`,
      confirmText: 'Cambiar proyecto',
      variant: 'warning',
    };
  }

  return {
    title: 'Asignar proyecto',
    message: `Se asignará ${target} a ${countLabel(assigning, entity)} sin proyecto.${note}`,
    confirmText: 'Asignar',
    variant: 'info',
  };
}

/**
 * Result toast after the call: how many rows the backend actually wrote.
 * `updated` counts the confirmed parents (the endpoint skips rows already on
 * target), so it can be lower than what was selected.
 */
export function describeProjectAssignmentResult(plan, updated, { entity }) {
  const attempted = plan.affected.length;
  const verb = plan.mode === 'unlink' ? 'desvinculado' : 'actualizado';
  const base = `${updated} de ${countLabel(attempted, entity)} ${updated === 1 ? verb : `${verb}s`}`;
  const notes = [];
  if (plan.unchanged.length > 0) notes.push(`${plan.unchanged.length} sin cambios`);
  if (plan.blockedClientMismatch.length > 0) {
    notes.push(`${plan.blockedClientMismatch.length} de otro cliente sin tocar`);
  }
  return notes.length > 0 ? `${base}; ${notes.join('; ')}.` : `${base}.`;
}
