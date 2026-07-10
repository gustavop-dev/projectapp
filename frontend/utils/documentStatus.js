/** Shared status/date/folder helpers for the documents list + gallery. */

const STATUS_BADGE = {
  draft: 'bg-surface-raised text-text-default',
  published: 'bg-primary-soft text-text-brand',
  archived: 'bg-warning-soft text-warning-strong',
};

const STATUS_LABEL = {
  draft: 'Borrador',
  published: 'Publicado',
  archived: 'Archivado',
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

export function folderRowSummary(folder) {
  const parts = [];
  const docs = folder.document_count || 0;
  const subs = folder.children_count || 0;
  if (docs) parts.push(`${docs} documento${docs !== 1 ? 's' : ''}`);
  if (subs) parts.push(`${subs} subcarpeta${subs !== 1 ? 's' : ''}`);
  return parts.length ? parts.join(' · ') : 'Vacía';
}
