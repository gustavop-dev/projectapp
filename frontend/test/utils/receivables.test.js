import {
  buildReceivablesSummary,
  confidenceDefinition,
  isReceivableEligible,
} from '../../utils/receivables';

const row = (overrides = {}) => ({
  id: 1,
  kind: 'expected',
  ledger: 'company',
  payment_status: 'partial',
  is_receivable_candidate: true,
  collection_confidence: 'high',
  total_amount: '1000.00',
  paid_amount: '400.00',
  pending_amount: '600.00',
  ...overrides,
});

describe('receivables utilities', () => {
  it('counts the original green amount', () => {
    const summary = buildReceivablesSummary([row()]);

    expect(summary.high_total).toBe(1000);
  });

  it('keeps unclassified selected income in selection totals', () => {
    const summary = buildReceivablesSummary([
      row({ collection_confidence: '', total_amount: '2500.00' }),
    ]);

    expect(summary.selected_total).toBe(2500);
    expect(summary.by_confidence.unclassified.count).toBe(1);
  });

  it('excludes unselected income from every total', () => {
    const summary = buildReceivablesSummary([
      row({ is_receivable_candidate: false }),
    ]);

    expect(summary.selected_count).toBe(0);
    expect(summary.high_total).toBe(0);
  });

  it('accepts only open company expected income as manageable', () => {
    expect(isReceivableEligible(row())).toBe(true);
    expect(isReceivableEligible(row({ ledger: 'personal' }))).toBe(false);
    expect(isReceivableEligible(row({ payment_status: 'paid' }))).toBe(false);
    expect(isReceivableEligible(row({ kind: 'liquid' }))).toBe(false);
  });

  it('maps medium confidence to its explanatory label', () => {
    expect(confidenceDefinition('medium').label).toBe('Cobro incierto (50/50)');
  });
});
