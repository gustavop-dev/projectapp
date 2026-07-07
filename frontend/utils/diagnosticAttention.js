/**
 * Attention signal for a diagnostic row: tells the seller which diagnostics
 * need action today, straight in the list (the same intelligence the
 * analytics suggestions engine applies per-diagnostic).
 *
 * Returns `null` when nothing needs attention, or:
 *   { key: 'hot' | 'stale', label: string, tone: 'danger' | 'warning' }
 *
 * Tone maps to the shared semantic chips: warning-soft → “act soon”,
 * danger-soft → “act now”. Same visual language as the editor scorecard
 * and the analytics suggestions.
 */

export const ATTENTION_THRESHOLDS = Object.freeze({
  /** Views without a response that mark a hot lead. */
  HOT_VIEWS_MIN: 3,
  /** Days since send/last view before a SENT diagnostic needs a follow-up. */
  STALE_WARNING_DAYS: 3,
  /** Days after which the follow-up is urgent. */
  STALE_DANGER_DAYS: 7,
});

const DAY_MS = 86_400_000;

function daysSince(iso, now) {
  if (!iso) return null;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return null;
  return Math.floor((now.getTime() - t) / DAY_MS);
}

export function getDiagnosticAttention(diagnostic, now = new Date()) {
  if (!diagnostic || diagnostic.status !== 'sent' || diagnostic.responded_at) {
    return null;
  }

  const views = Number(diagnostic.view_count || 0);
  if (views >= ATTENTION_THRESHOLDS.HOT_VIEWS_MIN) {
    return {
      key: 'hot',
      label: `${views} vistas sin respuesta`,
      tone: 'danger',
    };
  }

  const reference = diagnostic.last_viewed_at || diagnostic.initial_sent_at;
  const days = daysSince(reference, now);
  if (days === null || days < ATTENTION_THRESHOLDS.STALE_WARNING_DAYS) {
    return null;
  }

  return {
    key: 'stale',
    label: `${days} d sin respuesta`,
    tone: days >= ATTENTION_THRESHOLDS.STALE_DANGER_DAYS ? 'danger' : 'warning',
  };
}

/** Tailwind classes per tone — same pairs the status chips use. */
export const ATTENTION_TONE_CLASSES = Object.freeze({
  warning: 'bg-warning-soft text-warning-strong',
  danger: 'bg-danger-soft text-danger-strong',
});
