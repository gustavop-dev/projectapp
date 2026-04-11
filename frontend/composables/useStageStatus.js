/**
 * useStageStatus — pure helpers for ProposalProjectStage rendering.
 *
 * Mirrors the backend `ProposalStageTracker.format_remaining_time` logic:
 *   0  -> 'hoy'
 *   1  -> '1 día'
 *   6  -> '6 días'
 *   7  -> '1 semana'
 *   8  -> '1 semana 1 día'
 *   12 -> '1 semana 5 días'
 *   14 -> '2 semanas'
 *   15 -> '2 semanas 1 día'
 */

export function useStageStatus() {
  /**
   * Format a count of days as 'X semanas Y días' / 'X días' / 'hoy'.
   * Negative values are treated as their absolute value.
   * @param {number} days
   * @returns {string}
   */
  function formatRemainingTime(days) {
    const n = Math.abs(Math.trunc(Number(days) || 0));
    if (n === 0) return 'hoy';
    if (n < 7) return n === 1 ? '1 día' : `${n} días`;

    const weeks = Math.floor(n / 7);
    const remaining = n % 7;
    const weeksLabel = weeks === 1 ? '1 semana' : `${weeks} semanas`;
    if (remaining === 0) return weeksLabel;
    const daysLabel = remaining === 1 ? '1 día' : `${remaining} días`;
    return `${weeksLabel} ${daysLabel}`;
  }

  /**
   * Compute a derived status for rendering a stage badge.
   *
   * Returns one of:
   *   { kind: 'unscheduled' }     — no dates yet
   *   { kind: 'completed' }       — completed_at set
   *   { kind: 'not_started' }     — today < start_date
   *   { kind: 'pending', label }  — between start_date and end_date
   *   { kind: 'overdue', label }  — today > end_date
   *
   * @param {object} stage
   * @returns {{ kind: string, label?: string, percent?: number }}
   */
  function computeStageStatus(stage) {
    if (!stage) return { kind: 'unscheduled' };
    if (stage.completed_at) return { kind: 'completed' };
    if (!stage.start_date || !stage.end_date) return { kind: 'unscheduled' };

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const start = new Date(stage.start_date);
    const end = new Date(stage.end_date);

    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      return { kind: 'unscheduled' };
    }

    if (today < start) return { kind: 'not_started' };

    const dayMs = 24 * 60 * 60 * 1000;
    if (today > end) {
      const daysOverdue = Math.round((today - end) / dayMs);
      return { kind: 'overdue', label: formatRemainingTime(daysOverdue) };
    }

    const totalDays = Math.max(1, Math.round((end - start) / dayMs));
    const elapsedDays = Math.max(0, Math.round((today - start) / dayMs));
    const percent = Math.min(100, Math.round((elapsedDays / totalDays) * 100));
    const daysRemaining = Math.max(0, Math.round((end - today) / dayMs));
    return {
      kind: 'pending',
      label: formatRemainingTime(daysRemaining),
      percent,
    };
  }

  /**
   * Format a date / datetime string as '8 de abril, 2026' in Spanish.
   * Accepts ISO strings, Date instances, or null/undefined (returns '').
   * @param {string|Date|null|undefined} value
   * @returns {string}
   */
  function formatHumanDate(value) {
    if (!value) return '';
    const d = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(d.getTime())) return '';
    const months = [
      'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
      'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    ];
    return `${d.getDate()} de ${months[d.getMonth()]}, ${d.getFullYear()}`;
  }

  return {
    formatRemainingTime,
    computeStageStatus,
    formatHumanDate,
  };
}
