export const DIAGNOSTIC_STATUS = Object.freeze({
  DRAFT: 'draft',
  INITIAL_SENT: 'initial_sent',
  IN_ANALYSIS: 'in_analysis',
  FINAL_SENT: 'final_sent',
  ACCEPTED: 'accepted',
  REJECTED: 'rejected',
});

export const STATUS_META = Object.freeze({
  draft:        { label: 'Borrador',        cls: 'bg-gray-100 text-gray-700' },
  initial_sent: { label: 'Inicial enviada', cls: 'bg-blue-100 text-blue-700' },
  in_analysis:  { label: 'En análisis',     cls: 'bg-amber-100 text-amber-700' },
  final_sent:   { label: 'Final enviada',   cls: 'bg-purple-100 text-purple-700' },
  accepted:     { label: 'Aceptada',        cls: 'bg-emerald-100 text-emerald-700' },
  rejected:     { label: 'Rechazada',       cls: 'bg-rose-100 text-rose-700' },
});

export const STATUS_FILTER_OPTIONS = Object.freeze([
  { value: '', label: 'Todos los estados' },
  ...Object.entries(STATUS_META).map(([value, meta]) => ({ value, label: meta.label })),
]);
