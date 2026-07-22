/**
 * Proposal status labels and pill classes shared by the dashboard
 * section and the proposals stats modal. FUNNEL_ORDER follows the
 * commercial lifecycle for funnel-style charts.
 */

export const STATUS_LABELS = {
  draft: 'Borrador',
  sent: 'Enviada',
  viewed: 'Vista',
  negotiating: 'Negociando',
  accepted: 'Aceptada',
  finished: 'Finalizada',
  rejected: 'Rechazada',
  expired: 'Expirada',
};

export const PILL_CLASSES = {
  draft: 'bg-surface-raised text-text-muted',
  sent: 'bg-info-soft text-info-strong',
  viewed: 'bg-success-soft text-success-strong',
  negotiating: 'bg-warning-soft text-warning-strong',
  accepted: 'bg-primary-soft text-text-brand',
  finished: 'bg-primary-soft text-text-brand',
  rejected: 'bg-danger-soft text-danger-strong',
  expired: 'bg-warning-soft text-warning-strong',
};

export const FUNNEL_ORDER = [
  'draft', 'sent', 'viewed', 'negotiating',
  'accepted', 'finished', 'rejected', 'expired',
];

export function statusLabel(status) {
  return STATUS_LABELS[status] || status;
}

export function pillClass(status) {
  return PILL_CLASSES[status] || 'bg-surface-raised text-text-muted';
}
