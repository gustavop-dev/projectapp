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
});
