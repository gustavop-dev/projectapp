import { ensureProposalTaxLabel, proposalTaxLabel } from '../../utils/proposalTax';

describe('proposalTax', () => {
  it('returns IVA for COP amounts', () => {
    expect(proposalTaxLabel('COP')).toBe('+ IVA');
  });

  it('returns Tax for USD amounts', () => {
    expect(proposalTaxLabel('USD')).toBe('+ Tax');
  });

  it('adds IVA to a monetary value without a tax label', () => {
    expect(ensureProposalTaxLabel('$112.000.000 COP', 'COP'))
      .toBe('$112.000.000 COP + IVA');
  });

  it('does not duplicate an existing IVA label', () => {
    expect(ensureProposalTaxLabel('$112.000.000 COP + IVA', 'COP'))
      .toBe('$112.000.000 COP + IVA');
  });

  it('leaves non-monetary copy unchanged', () => {
    expect(ensureProposalTaxLabel('Valor definido en el contrato', 'COP'))
      .toBe('Valor definido en el contrato');
  });
});
