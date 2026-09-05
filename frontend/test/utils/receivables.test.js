import {
  buildReceivablesSummary,
  groupReceivables,
  confidenceDefinition,
  isReceivableEligible,
  sumReceivableGroups,
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

  it('groups candidates by client with complete monetary totals', () => {
    const groups = groupReceivables([
      row({ id: 1, client: 10, client_name: 'Kore', total_amount: '1000', paid_amount: '250', pending_amount: '750' }),
      row({ id: 2, client: 10, client_name: 'Kore', total_amount: '500', paid_amount: '100', pending_amount: '400' }),
      row({ id: 3, client: 20, client_name: 'Acme', total_amount: '800', paid_amount: '0', pending_amount: '800' }),
    ]);

    expect(groups).toEqual([
      expect.objectContaining({
        id: 10,
        name: 'Kore',
        count: 2,
        total_amount: 1500,
        paid_amount: 350,
        pending_amount: 1150,
      }),
      expect.objectContaining({ id: 20, name: 'Acme', count: 1, total_amount: 800 }),
    ]);
  });

  it('groups candidates by project with unassigned rows last', () => {
    const groups = groupReceivables([
      row({ id: 1, project: null, project_name: null, total_amount: '5000' }),
      row({ id: 2, project: 40, project_name: 'Kore v2', total_amount: '1000' }),
      row({ id: 3, project: 30, project_name: 'Acme portal', total_amount: '2000' }),
    ], 'project');

    expect(groups.map(({ id, name }) => ({ id, name }))).toEqual([
      { id: 30, name: 'Acme portal' },
      { id: 40, name: 'Kore v2' },
      { id: 'none', name: 'Sin proyecto' },
    ]);
  });

  it('sums exactly the rows represented by filtered groups', () => {
    const groups = groupReceivables([
      row({ id: 1, client: 10, total_amount: '1000', paid_amount: '250', pending_amount: '750' }),
      row({ id: 2, client: 20, total_amount: '600', paid_amount: '100', pending_amount: '500' }),
    ]);

    expect(sumReceivableGroups(groups)).toEqual({
      count: 2,
      total_amount: 1600,
      paid_amount: 350,
      pending_amount: 1250,
    });
  });
});
