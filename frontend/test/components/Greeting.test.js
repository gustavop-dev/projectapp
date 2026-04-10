import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import Greeting from '../../components/BusinessProposal/Greeting.vue';

function mountGreeting(props = {}) {
  return mount(Greeting, {
    props: {
      proposalTitle: 'Propuesta Digital',
      clientName: 'Juan',
      inspirationalQuote: 'Innovation is key',
      ...props,
    },
  });
}

describe('Greeting', () => {
  it('renders the proposalTitle and clientName together', () => {
    const wrapper = mountGreeting();

    expect(wrapper.text()).toContain('Propuesta Digital, Juan');
  });

  it('renders the inspirationalQuote', () => {
    const wrapper = mountGreeting({ inspirationalQuote: 'Think different' });

    expect(wrapper.text()).toContain('Think different');
  });

  it('renders with custom proposalTitle', () => {
    const wrapper = mountGreeting({ proposalTitle: 'Plataforma SaaS' });

    expect(wrapper.text()).toContain('Plataforma SaaS');
  });
});
