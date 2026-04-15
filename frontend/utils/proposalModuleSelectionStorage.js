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
