/**
 * Filter technical_document content_json by the same module ids as the commercial calculator
 * (module-*, group-*, or investment module string ids).
 */

function normIds(raw) {
  if (!raw) return [];
  if (typeof raw === 'string') {
    const s = raw.trim();
    return s ? [s] : [];
  }
  if (Array.isArray(raw)) {
    return raw.filter((x) => typeof x === 'string' && x.trim()).map((x) => x.trim());
  }
  return [];
}

function reqVisible(req, selectedSet) {
  const ids = normIds(req.linked_module_ids || req.linkedModuleIds);
  if (!ids.length) return true;
  if (selectedSet == null) return true;
  return ids.some((id) => selectedSet.has(id));
}

function epicGatedOut(epic, selectedSet) {
  const ids = normIds(epic.linked_module_ids || epic.linkedModuleIds);
  if (!ids.length || selectedSet == null) return false;
  return !ids.some((id) => selectedSet.has(id));
}

function epicMeaningfulHeader(epic) {
  const t = (k) => typeof epic[k] === 'string' && epic[k].trim();
  return t('title') || t('description') || t('epicKey');
}

/**
 * @param {Record<string, unknown>} contentJson
 * @param {string[]|null|undefined} selectedModuleIds - null/undefined = no filtering (legacy)
 * @returns {Record<string, unknown>}
 */
export function filterTechnicalDocumentByModules(contentJson, selectedModuleIds) {
  if (!contentJson || typeof contentJson !== 'object') return {};
  const out = JSON.parse(JSON.stringify(contentJson));
  const selectedSet = selectedModuleIds == null ? null : new Set(selectedModuleIds);

  const epics = out.epics;
  if (!Array.isArray(epics)) return out;

  const newEpics = [];
  for (const epic of epics) {
    if (!epic || typeof epic !== 'object') continue;
    if (epicGatedOut(epic, selectedSet)) continue;
    const reqsIn = Array.isArray(epic.requirements) ? epic.requirements : [];
    const filteredReqs = reqsIn.filter(
      (r) => r && typeof r === 'object' && reqVisible(r, selectedSet),
    );
    if (filteredReqs.length) {
      newEpics.push({ ...epic, requirements: filteredReqs });
    } else if (epicMeaningfulHeader(epic)) {
      newEpics.push({ ...epic, requirements: [] });
    }
  }
  out.epics = newEpics;
  return out;
}
