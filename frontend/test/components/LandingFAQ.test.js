import { mount } from '@vue/test-utils';

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      faq: {
        title: 'Frequently Asked Questions',
        questions: [
          { q: 'How long does it take?', a: 'Usually 30 days.' },
          { q: 'What platforms do you support?', a: 'iOS and Android.' },
          { q: 'Do you offer post-launch support?', a: 'Yes, we offer maintenance.' },
        ],
      },
    }),
  })),
}));

import LandingFAQ from '../../components/landing/LandingFAQ.vue';

function mountFAQ() {
  return mount(LandingFAQ);
}

describe('LandingFAQ', () => {
  it('renders the section element', () => {
    const wrapper = mountFAQ();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the FAQ title', () => {
    const wrapper = mountFAQ();

    expect(wrapper.text()).toContain('Frequently Asked Questions');
  });

  it('renders FAQ items as details elements', () => {
    const wrapper = mountFAQ();

    expect(wrapper.findAll('details')).toHaveLength(3);
  });

  it('renders question text', () => {
    const wrapper = mountFAQ();

    expect(wrapper.text()).toContain('How long does it take?');
  });

  it('renders answer text', () => {
    const wrapper = mountFAQ();

    expect(wrapper.text()).toContain('Usually 30 days.');
  });
});
