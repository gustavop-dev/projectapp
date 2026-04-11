import { useTooltipTexts } from '../../composables/useTooltipTexts';

describe('useTooltipTexts', () => {
  it('returns the admin tooltip groups with representative entries', () => {
    const { analytics, dashboard, proposalEdit } = useTooltipTexts();

    expect(analytics.engagementScore).toContain('Puntuación de 0 a 100');
    expect(dashboard.conversionRate).toContain('Porcentaje de propuestas aceptadas');
    expect(proposalEdit.activeStatus).toContain('propuesta expirada');
  });
});
