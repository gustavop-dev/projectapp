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

// Mirrors statusClass() in pages/panel/proposals/index.vue (semantic tokens
// flip automatically in dark mode).
export const STATUS_META = Object.freeze({
  draft:       { label: 'Borrador',      cls: 'bg-surface-raised text-text-muted' },
  sent:        { label: 'Enviada',       cls: 'bg-info-soft text-info-strong' },
  viewed:      { label: 'Vista',         cls: 'bg-success-soft text-success-strong' },
  negotiating: { label: 'En negociación', cls: 'bg-warning-soft text-warning-strong' },
  accepted:    { label: 'Aceptada',      cls: 'bg-primary-soft text-text-brand' },
  rejected:    { label: 'Rechazada',     cls: 'bg-danger-soft text-danger-strong' },
  expired:     { label: 'Expirada',      cls: 'bg-warning-soft text-warning-strong' },
  finished:    { label: 'Finalizada',    cls: 'bg-primary-soft text-text-brand' },
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
  'Crítico': 'bg-danger-soft text-danger-strong',
  'Alto':    'bg-warning-soft text-warning-strong',
  'Medio':   'bg-warning-soft text-warning-strong',
  'Bajo':    'bg-success-soft text-success-strong',
});

export function severityLevelClass(level) {
  return SEVERITY_LEVEL_CLASSES[level] || 'bg-surface-raised text-text-muted';
}

/**
 * Single source for the analytics magic numbers (colors, emojis and the
 * section-completeness bar in the editor all read from here).
 */
export const DIAGNOSTIC_ANALYTICS_THRESHOLDS = Object.freeze({
  ENGAGEMENT: Object.freeze({ HIGH: 70, MEDIUM: 40 }),
  COVERAGE: Object.freeze({ GOOD: 80, WARN: 50 }),
  SECTION_AVG_SECONDS: Object.freeze({ HIGH: 60, MID: 20, LOW: 5 }),
  SECTION_BAR_MAX_SECONDS: 180,
  FUNNEL_DROPOFF: Object.freeze({ LOW: 10, MID: 30, HIGH: 50 }),
  HEAT_RATIOS: Object.freeze([0.15, 0.35, 0.55, 0.75]),
});

export const ACTIVITY_CHANGE_TYPES = Object.freeze([
  { value: 'note',     label: 'Nota' },
  { value: 'call',     label: 'Llamada' },
  { value: 'meeting',  label: 'Reunión' },
  { value: 'followup', label: 'Seguimiento' },
]);
