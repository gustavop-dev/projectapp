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

export function documentStatusBadgeClass(status) {
  return STATUS_BADGE[status] || STATUS_BADGE.draft;
}

export function documentStatusLabel(status) {
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
 * Documentos y subcarpetas de una carpeta, en el scope pedido.
 *
 * Los `active_*`/`archived_*` son absolutos; `document_count` es relativo al
 * estado de la fila y sumarlo con el archivado duplicaría una carpeta
 * archivada. El fallback cubre payloads viejos (tests, respuestas cacheadas).
 */
/**
 * Clases de raíz que el sistema posee: representan a un proyecto o a un cliente.
 *
 * Vive acá y no repetido en cada componente para que sumar una clase nueva sea
 * una sola edición: las guardas de arrastrar, editar y borrar preguntan por
 * este conjunto, no por un valor suelto.
 */
export const MANAGED_FOLDER_KINDS = Object.freeze(['project', 'client']);

/**
 * ¿La carpeta es una raíz gestionada, y por lo tanto intocable desde el gestor?
 *
 * Se pregunta por la NEGATIVA («no es de las gestionadas») en vez de exigir
 * `folder_kind === 'manual'`: el campo llega en todo payload del serializer,
 * pero una fila sin él —una fixture parcial, un resultado de búsqueda— debe
 * seguir comportándose como propia y no quedar inerte en silencio.
 */
export function isManagedFolderKind(folder) {
  return MANAGED_FOLDER_KINDS.includes(folder?.folder_kind);
}

export function scopedCounts(folder, scope) {
  if (!folder) return { docs: 0, subs: 0 };
  const activeDocs = folder.active_document_count
    ?? (folder.is_archived ? 0 : folder.document_count || 0);
  const activeSubs = folder.active_children_count
    ?? (folder.is_archived ? 0 : folder.children_count || 0);
  // El fallback es simétrico: `document_count` es relativo al estado de la
  // fila, así que alimenta el lado que coincide con ese estado y cero el otro.
  const archivedDocs = folder.archived_document_count
    ?? (folder.is_archived ? folder.document_count || 0 : 0);
  const archivedSubs = folder.archived_children_count
    ?? (folder.is_archived ? folder.children_count || 0 : 0);

  if (scope === 'archived') return { docs: archivedDocs, subs: archivedSubs };
  if (scope === 'all') {
    return { docs: activeDocs + archivedDocs, subs: activeSubs + archivedSubs };
  }
  return { docs: activeDocs, subs: activeSubs };
}

/**
 * Inventario legible a partir de un par de conteos ya resuelto.
 *
 * Se separó de `folderRowSummary` porque el mismo texto lo necesitan los
 * conteos recursivos del árbol, que no salen de una sola carpeta sino del
 * rollup — y duplicar la pluralización era garantizar que se separaran.
 */
export function folderSummaryFrom({ docs = 0, subs = 0 } = {}) {
  const parts = [];
  if (docs) parts.push(`${docs} documento${docs !== 1 ? 's' : ''}`);
  if (subs) parts.push(`${subs} subcarpeta${subs !== 1 ? 's' : ''}`);
  return parts.length ? parts.join(' · ') : 'Vacía';
}

/**
 * Inventario legible de una carpeta, en el scope pedido.
 *
 * Con `'all'` suma los dos estados: es lo que necesita el tooltip del ícono de
 * eliminar, porque el 409 del backend cuenta todo el contenido y un resumen
 * que sólo mirara lo activo diría «Vacía» de una carpeta imborrable.
 */
export function folderRowSummary(folder, scope = 'active') {
  return folderSummaryFrom(scopedCounts(folder, scope));
}

/**
 * Nombre accesible de una fila de carpeta: «Familia — 1 subcarpeta, 12 documentos».
 *
 * La fila muestra dos cifras desnudas junto a dos íconos, y los íconos van
 * `aria-hidden` para no ensuciar el nombre del botón. Sin este rótulo un lector
 * de pantalla anunciaría «Familia 1 12», que no significa nada.
 */
export function folderRowLabel(name, { docs = 0, subs = 0 } = {}) {
  const parts = [];
  if (subs) parts.push(`${subs} subcarpeta${subs !== 1 ? 's' : ''}`);
  parts.push(`${docs} documento${docs !== 1 ? 's' : ''}`);
  return `${name} — ${parts.join(', ')}`;
}
