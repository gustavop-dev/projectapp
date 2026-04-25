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
