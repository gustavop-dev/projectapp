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
