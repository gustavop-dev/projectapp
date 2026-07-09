/**
 * Shared catalog of business-proposal statuses for the admin panel.
 *
 * Labels are the Spanish singular forms, mirroring the backend
 * STATUS_LABELS_ES map (business_proposal.py). The plural map used by the
 * proposals filter tabs lives in that page, not here.
 */

export const PROPOSAL_STATUSES = [
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviada' },
  { value: 'viewed', label: 'Vista' },
  { value: 'negotiating', label: 'En negociación' },
  { value: 'accepted', label: 'Aceptada' },
  { value: 'finished', label: 'Finalizada' },
  { value: 'rejected', label: 'Rechazada' },
  { value: 'expired', label: 'Expirada' },
];

const LABELS = Object.fromEntries(PROPOSAL_STATUSES.map((s) => [s.value, s.label]));

const CLASSES = {
  draft: 'bg-surface-raised text-text-muted',
  sent: 'bg-info-soft text-info-strong',
  viewed: 'bg-success-soft text-success-strong',
  accepted: 'bg-primary-soft text-text-brand',
  finished: 'bg-primary-soft text-text-brand',
  rejected: 'bg-danger-soft text-danger-strong',
  negotiating: 'bg-warning-soft text-warning-strong',
  expired: 'bg-warning-soft text-warning-strong',
};

export function statusLabel(value) {
  return LABELS[value] || value;
}

export function statusClass(value) {
  return CLASSES[value] || 'bg-surface-raised text-text-muted';
}

/**
 * True when moving `proposal` to `target` follows the natural lifecycle
 * (backend ALLOWED_TRANSITIONS, surfaced as `available_transitions`).
 * Anything else is an admin-forced jump: allowed, but side-effect free.
 */
export function isNaturalTransition(proposal, target) {
  return (proposal?.available_transitions || []).includes(target);
}
