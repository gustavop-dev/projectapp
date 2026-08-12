/**
 * Presentation vocabulary of a cuenta de cobro, shared by the list and the
 * detail modal so a row and its modal can never disagree about a status.
 */

/** Tailwind classes for the commercial-status pill. Overdue wins. */
export function statusBadgeClass(row) {
  if (row?.is_overdue) return 'bg-warning-soft text-warning-strong';
  return {
    draft: 'bg-surface-raised text-text-muted',
    issued: 'bg-info-soft text-info-strong',
    paid: 'bg-success-soft text-success-strong',
    cancelled: 'bg-danger-soft text-danger-strong',
  }[row?.commercial_status] || 'bg-surface-raised text-text-muted';
}

/**
 * Which record the cuenta was raised from. The backend used to append the
 * hosting's client / the income's concept to this label; those now have
 * columns of their own, so only the type is left.
 */
export const ORIGIN_LABELS = {
  hosting: 'Hosting',
  income: 'Ingreso',
  project: 'Proyecto',
  other: 'Otro',
};

export const ORIGIN_TONES = {
  hosting: 'bg-info-soft text-info-strong',
  income: 'bg-primary-soft text-text-brand',
  project: 'bg-surface-raised text-text-muted',
  other: 'bg-surface-raised text-text-muted',
};

export function originLabel(origin) {
  return ORIGIN_LABELS[origin] || ORIGIN_LABELS.other;
}

export function originTone(origin) {
  return ORIGIN_TONES[origin] || ORIGIN_TONES.other;
}
