function normalizeSelectedIds(raw) {
  if (!Array.isArray(raw)) return [];
  const seen = new Set();
  const out = [];
  for (const value of raw) {
    if (typeof value !== 'string') continue;
    const trimmed = value.trim();
    if (!trimmed || seen.has(trimmed)) continue;
    seen.add(trimmed);
    out.push(trimmed);
  }
  return out;
}

export function getProposalModuleSelectionStorageKey(proposalUuid) {
  return `proposal-${proposalUuid}-modules`;
}

export function getProposalModuleSelectionConfirmedKey(proposalUuid) {
  return `proposal-${proposalUuid}-modules-confirmed`;
}

export function readStoredProposalModuleSelection(proposalUuid) {
  if (!proposalUuid) {
    return { hasStoredSelection: false, selectedIds: [] };
  }

  try {
    const raw = localStorage.getItem(getProposalModuleSelectionStorageKey(proposalUuid));
    if (raw == null) {
      return { hasStoredSelection: false, selectedIds: [] };
    }
    return {
      hasStoredSelection: true,
      selectedIds: normalizeSelectedIds(JSON.parse(raw)),
    };
  } catch (_e) {
    return { hasStoredSelection: false, selectedIds: [] };
  }
}

export function hasStoredConfirmedProposalModuleSelection(proposalUuid) {
  if (!proposalUuid) return false;
  try {
    return localStorage.getItem(getProposalModuleSelectionConfirmedKey(proposalUuid)) === '1';
  } catch (_e) {
    return false;
  }
}

export function writeStoredProposalModuleSelectionConfirmation(proposalUuid, confirmed = true) {
  if (!proposalUuid) return;
  try {
    localStorage.setItem(
      getProposalModuleSelectionConfirmedKey(proposalUuid),
      confirmed ? '1' : '0',
    );
  } catch (_e) { /* ignore */ }
}

// Rebuilds persisted selected_modules ids into the canonical prefixed form
// (module-<id>/group-<id>) used by the calculator catalog. Older payloads
// or template copies can ship bare group ids, which would break equality
// checks against `item.id` on the frontend. *calcItems* is the resolved
// calculator catalog (typically `allGroupCalculatorItems.value`).
export function normalizePersistedSelectedIds(persisted, calcItems) {
  if (!Array.isArray(persisted) || !persisted.length) return [];
  const byGroupId = new Map();
  for (const item of calcItems || []) {
    if (item?.groupId != null) byGroupId.set(String(item.groupId), item.id);
  }
  const out = [];
  const seen = new Set();
  for (const raw of persisted) {
    if (raw == null || raw === '') continue;
    const id = String(raw);
    const canonical = id.startsWith('module-') || id.startsWith('group-')
      ? id
      : (byGroupId.get(id) || id);
    if (!seen.has(canonical)) {
      seen.add(canonical);
      out.push(canonical);
    }
  }
  return out;
}
