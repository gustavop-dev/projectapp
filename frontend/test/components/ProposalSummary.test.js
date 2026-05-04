import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import ProposalSummary from '../../components/BusinessProposal/ProposalSummary.vue';

function mountSummary(props = {}) {
  return mount(ProposalSummary, { props });
}

describe('ProposalSummary', () => {
  it('renders the section title from content.title', () => {
    const wrapper = mountSummary({ content: { title: 'Resumen del Proyecto' } });

    expect(wrapper.text()).toContain('Resumen del Proyecto');
  });

  it('renders the subtitle when content.subtitle is provided', () => {
    const wrapper = mountSummary({ content: { title: 'Resumen', subtitle: 'Todo lo que necesitas saber.' } });

    expect(wrapper.text()).toContain('Todo lo que necesitas saber.');
  });

  it('hides the subtitle when content.subtitle is absent', () => {
    const wrapper = mountSummary({ content: { title: 'Resumen' } });

    expect(wrapper.find('p.text-esmerald\\/70').exists()).toBe(false);
  });

  it('renders auto-generated cards when no content.cards are provided', () => {
    const wrapper = mountSummary({ content: {} });

    // Auto-generates designer, analytics, and best_practices cards
    expect(wrapper.findAll('.summary-card').length).toBeGreaterThan(0);
  });

  it('renders investment modules card when investmentModules are provided', () => {
    const wrapper = mountSummary({
      content: {},
      investmentModules: [{ id: 1 }, { id: 2 }],
    });

    expect(wrapper.text()).toContain('2');
  });

  describe('total_investment card description sync', () => {
    const investmentCardContent = (description) => ({
      cards: [
        {
          icon: '💰',
          title: 'Inversión',
          source: 'total_investment',
          description,
        },
      ],
    });

    it('rewrites a stale amount in the description with the live customizedTotal', () => {
      const wrapper = mountSummary({
        content: investmentCardContent('Monto total del proyecto: $4.900.000 COP.'),
        proposal: { total_investment: 3200000, currency: 'COP' },
        customizedTotal: 4320000,
        isCustomized: false,
      });

      const card = wrapper.find('.summary-card');
      expect(card.text()).toContain('$4.320.000 COP');
      expect(card.text()).not.toContain('$4.900.000');
    });

    it('falls back to proposal.total_investment when customizedTotal is null', () => {
      const wrapper = mountSummary({
        content: investmentCardContent('Monto total del proyecto: $4.900.000 COP.'),
        proposal: { total_investment: 3200000, currency: 'COP' },
        customizedTotal: null,
        isCustomized: false,
      });

      const card = wrapper.find('.summary-card');
      expect(card.text()).toContain('$3.200.000 COP');
      expect(card.text()).not.toContain('$4.900.000');
    });

    it('uses the customized copy and skips the regex when isCustomized is true', () => {
      const wrapper = mountSummary({
        content: investmentCardContent('Monto total del proyecto: $4.900.000 COP.'),
        proposal: { total_investment: 3200000, currency: 'COP' },
        customizedTotal: 4320000,
        isCustomized: true,
        language: 'es',
      });

      const card = wrapper.find('.summary-card');
      expect(card.text()).toContain('$4.320.000 COP');
      expect(card.text()).not.toContain('$4.900.000');
      expect(card.text()).not.toContain('Monto total del proyecto');
    });

    it('preserves narrative text when there is no monetary amount in the description', () => {
      const wrapper = mountSummary({
        content: investmentCardContent('Inversión total acordada para el proyecto.'),
        proposal: { total_investment: 3200000, currency: 'COP' },
        customizedTotal: 4320000,
        isCustomized: false,
      });

      const card = wrapper.find('.summary-card');
      expect(card.text()).toContain('Inversión total acordada para el proyecto.');
      expect(card.text()).toContain('$4.320.000 COP');
    });
  });
});
