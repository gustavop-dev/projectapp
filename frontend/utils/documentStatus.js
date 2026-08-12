/** Shared status/date/folder helpers for the documents list + gallery. */

// `archived` ya no vive acá: "Archivado" es ahora el estado que SACA de la
// vista (Document.is_archived), no un estado editorial que no ocultaba nada.
// Se dejó de ofrecer en el selector del editor; producción tenía 0 documentos
// usándolo. Una fila legacy con status='archived' cae al fallback y se muestra
// con su valor crudo en vez de mentir con la insignia de archivado.
const STATUS_BADGE = {
  draft: 'bg-surface-raised text-text-default',
  published: 'bg-primary-soft text-text-brand',
};

const STATUS_LABEL = {
  draft: 'Borrador',
  published: 'Publicado',
};

export function statusBadgeClass(status) {
  return STATUS_BADGE[status] || STATUS_BADGE.draft;
}

export function statusLabel(status) {
  return STATUS_LABEL[status] || status;
}

export function formatDocumentDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' });
}

/**
 * Antigüedad legible de un archivado: 'hoy' | 'hace 3 días' | 'hace 2 meses'.
 * Es la señal de triage de la vista de archivados — responde "¿qué lleva mucho
 * tiempo guardado?" sin obligar a comparar fechas a ojo.
 */
export function archivedAgeLabel(dateStr) {
  if (!dateStr) return '';
  const then = new Date(dateStr);
  if (Number.isNaN(then.getTime())) return '';
  const days = Math.floor((Date.now() - then.getTime()) / 86400000);
  if (days <= 0) return 'hoy';
  if (days === 1) return 'ayer';
  if (days < 30) return `hace ${days} días`;
  const months = Math.floor(days / 30);
  if (months < 12) return `hace ${months} ${months === 1 ? 'mes' : 'meses'}`;
  const years = Math.floor(days / 365);
  return `hace ${years} ${years === 1 ? 'año' : 'años'}`;
}

/**
 * Inventario legible de una carpeta, en el scope pedido.
 *
 * Con `'all'` suma los dos estados: es lo que necesita el tooltip del ícono de
 * eliminar, porque el 409 del backend cuenta todo el contenido y un resumen
 * que sólo mirara lo activo diría «Vacía» de una carpeta imborrable.
 */
export function folderRowSummary(folder, scope = 'active') {
  // Los `active_*`/`archived_*` son absolutos; `document_count` es relativo al
  // estado de la fila y sumarlo con el archivado duplicaría una carpeta
  // archivada. El fallback cubre payloads viejos (tests, respuestas cacheadas).
  const activeDocs = folder.active_document_count
    ?? (folder.is_archived ? 0 : folder.document_count || 0);
  const activeSubs = folder.active_children_count
    ?? (folder.is_archived ? 0 : folder.children_count || 0);
  const archivedDocs = folder.archived_document_count || 0;
  const archivedSubs = folder.archived_children_count || 0;

  let docs = activeDocs;
  let subs = activeSubs;
  if (scope === 'archived') {
    docs = archivedDocs;
    subs = archivedSubs;
  } else if (scope === 'all') {
    docs = activeDocs + archivedDocs;
    subs = activeSubs + archivedSubs;
  }

  const parts = [];
  if (docs) parts.push(`${docs} documento${docs !== 1 ? 's' : ''}`);
  if (subs) parts.push(`${subs} subcarpeta${subs !== 1 ? 's' : ''}`);
  return parts.length ? parts.join(' · ') : 'Vacía';
}
