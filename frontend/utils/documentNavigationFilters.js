/**
 * Build a complete document-navigation filter set.
 *
 * Project and client are mutually exclusive axes. Returning both keys is
 * intentional: Pinia only changes keys that are present, so omitting the
 * inactive axis would preserve a stale filter and could produce an empty
 * intersection after the user changes navigation context.
 */
export function navigationEntityFilters(mode, value, archiveScope = 'active') {
  const selected = value === 'all' || value == null ? null : value;
  const folder = selected == null
    ? (archiveScope === 'archived' ? 'root' : 'all')
    : 'root';

  return {
    folder,
    project: mode === 'project' ? selected : null,
    client: mode === 'client' ? selected : null,
  };
}

/** A manual-folder click leaves entity navigation and clears both axes. */
export function manualFolderFilters(folder) {
  return { folder, project: null, client: null };
}

/**
 * Keeps entity navigation only while the destination belongs to that entity.
 *
 * A project/client root and its descendant folders are one navigational path,
 * not competing filters. Own or unrelated folders still leave that path and
 * clear both association axes through `manualFolderFilters`.
 */
export function contextualFolderFilters({
  folderId, folder, mode, selection,
} = {}) {
  const selectedId = Number(selection);
  const hasSelectedEntity = (
    (mode === 'project' || mode === 'client')
    && Number.isInteger(selectedId)
    && selectedId > 0
  );
  const association = mode === 'project' ? folder?.project : folder?.client;
  const belongsToSelection = (
    folderId === 'root'
    || (association != null && Number(association) === selectedId)
  );

  if (!hasSelectedEntity || !belongsToSelection) {
    return manualFolderFilters(folderId);
  }

  return {
    folder: folderId,
    project: mode === 'project' ? selectedId : null,
    client: mode === 'client' ? selectedId : null,
  };
}
