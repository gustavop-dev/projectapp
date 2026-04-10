import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../utils/technicalProposalPanels', () => ({
  technicalFragmentHasContent: jest.fn(() => true),
  FRAGMENT_ORDER: ['intro', 'stack', 'architecture'],
  TECH_PANEL_TITLES: {
    es: { intro: 'Introducción', stack: 'Stack Técnico', architecture: 'Arquitectura' },
    en: { intro: 'Introduction', stack: 'Tech Stack', architecture: 'Architecture' },
  },
}));

import TechnicalDocumentPublicPanel from '../../components/BusinessProposal/TechnicalDocumentPublicPanel.vue';

function mountPanel(props = {}) {
  return mount(TechnicalDocumentPublicPanel, {
    props: { fragment: 'intro', contentJson: {}, language: 'es', ...props },
    global: { stubs: { Teleport: true } },
  });
}

describe('TechnicalDocumentPublicPanel', () => {
  it('renders the section element', () => {
    const wrapper = mountPanel();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the intro heading when fragment is intro', () => {
    const wrapper = mountPanel({ fragment: 'intro' });

    expect(wrapper.text()).toContain('Introducción');
  });

  it('renders the stack heading when fragment is stack', () => {
    const wrapper = mountPanel({ fragment: 'stack' });

    expect(wrapper.text()).toContain('Stack Técnico');
  });

  it('renders English intro heading when language is en', () => {
    const wrapper = mountPanel({ fragment: 'intro', language: 'en' });

    expect(wrapper.text()).toContain('Introduction');
  });

  it('renders the stack table when fragment is stack', () => {
    const wrapper = mountPanel({ fragment: 'stack' });

    expect(wrapper.find('table').exists()).toBe(true);
  });
});
