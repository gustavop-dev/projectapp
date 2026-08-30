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
