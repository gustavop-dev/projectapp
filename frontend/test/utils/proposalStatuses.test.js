/**
 * Tests for the shared proposal status catalog (utils/proposalStatuses).
 *
 * Covers: catalog completeness/order, Spanish labels, badge classes,
 * and natural-transition detection.
 */

const {
  PROPOSAL_STATUSES,
  statusLabel,
  statusClass,
  isNaturalTransition,
} = require('../../utils/proposalStatuses');

describe('proposalStatuses', () => {
  it('exposes the 8 proposal statuses', () => {
    expect(PROPOSAL_STATUSES.map((s) => s.value)).toEqual([
      'draft', 'sent', 'viewed', 'negotiating', 'accepted', 'finished', 'rejected', 'expired',
    ]);
  });

  it('statusLabel returns the Spanish singular label', () => {
    expect(statusLabel('sent')).toBe('Enviada');
    expect(statusLabel('negotiating')).toBe('En negociación');
  });

  it('statusLabel falls back to the raw value for unknown statuses', () => {
    expect(statusLabel('bogus')).toBe('bogus');
  });

  it('statusClass returns semantic token classes per status', () => {
    expect(statusClass('rejected')).toBe('bg-danger-soft text-danger-strong');
    expect(statusClass('draft')).toBe('bg-surface-raised text-text-muted');
  });

  it('statusClass falls back to the neutral badge for unknown statuses', () => {
    expect(statusClass('bogus')).toBe('bg-surface-raised text-text-muted');
  });

  it('isNaturalTransition checks available_transitions', () => {
    const proposal = { status: 'sent', available_transitions: ['negotiating', 'rejected'] };
    expect(isNaturalTransition(proposal, 'negotiating')).toBe(true);
    expect(isNaturalTransition(proposal, 'finished')).toBe(false);
  });

  it('isNaturalTransition tolerates missing transitions', () => {
    expect(isNaturalTransition({ status: 'draft' }, 'sent')).toBe(false);
    expect(isNaturalTransition(null, 'sent')).toBe(false);
  });
});
