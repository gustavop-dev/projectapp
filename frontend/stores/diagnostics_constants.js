export const DIAGNOSTIC_STATUS = Object.freeze({
  DRAFT: 'draft',
  SENT: 'sent',
  VIEWED: 'viewed',
  NEGOTIATING: 'negotiating',
  ACCEPTED: 'accepted',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
  FINISHED: 'finished',
});

export const STATUS_META = Object.freeze({
  draft:       { label: 'Borrador',      cls: 'bg-gray-100 text-gray-700' },
  sent:        { label: 'Enviada',       cls: 'bg-blue-100 text-blue-700' },
  viewed:      { label: 'Vista',         cls: 'bg-indigo-100 text-indigo-700' },
  negotiating: { label: 'En negociación', cls: 'bg-amber-100 text-amber-700' },
  accepted:    { label: 'Aceptada',      cls: 'bg-emerald-100 text-emerald-700' },
  rejected:    { label: 'Rechazada',     cls: 'bg-rose-100 text-rose-700' },
  expired:     { label: 'Expirada',      cls: 'bg-slate-100 text-slate-600' },
  finished:    { label: 'Finalizada',    cls: 'bg-purple-100 text-purple-700' },
});

export const STATUS_FILTER_OPTIONS = Object.freeze([
  { value: '', label: 'Todos los estados' },
  ...Object.entries(STATUS_META).map(([value, meta]) => ({ value, label: meta.label })),
]);

export const SECTION_VISIBILITY = Object.freeze({
  INITIAL: 'initial',
  FINAL: 'final',
  BOTH: 'both',
});

export const VISIBILITY_OPTIONS = Object.freeze([
  { value: SECTION_VISIBILITY.BOTH,    label: 'Ambos envíos' },
  { value: SECTION_VISIBILITY.INITIAL, label: 'Sólo envío inicial' },
  { value: SECTION_VISIBILITY.FINAL,   label: 'Sólo envío final' },
]);

export const SEVERITY_LEVELS = Object.freeze(['Crítico', 'Alto', 'Medio', 'Bajo']);

export const SEVERITY_LEVEL_CLASSES = Object.freeze({
  'Crítico': 'bg-rose-100 text-rose-700',
  'Alto':    'bg-amber-100 text-amber-700',
  'Medio':   'bg-yellow-100 text-yellow-700',
  'Bajo':    'bg-emerald-100 text-emerald-700',
});

export function severityLevelClass(level) {
  return SEVERITY_LEVEL_CLASSES[level] || 'bg-gray-100 text-gray-600';
}

export const ACTIVITY_CHANGE_TYPES = Object.freeze([
  { value: 'note',     label: 'Nota' },
  { value: 'call',     label: 'Llamada' },
  { value: 'meeting',  label: 'Reunión' },
  { value: 'followup', label: 'Seguimiento' },
]);
