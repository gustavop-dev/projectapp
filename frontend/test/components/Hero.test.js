import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));
global.useLocalePath = jest.fn(() => (path) => path);

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: {
      hero: {
        title_part1: 'Your Trusted',
        title_part2: 'Web Design Partner',
        subtitle: 'We design high-converting websites.',
        cta_primary: 'Get In Touch',
        cta_book_call: 'Book a Call',
        benefit2_title: 'A real advisor replies',
        benefit2_text: 'A senior specialist replies the same day.',
        benefit4_title: '+50 companies trust us',
        benefit4_text: 'Companies already transformed their operations with us.',
        nda_note: 'We sign an NDA so your project stays confidential.',
      },
    },
  })),
}));

jest.mock('../../composables/useGtagConversions', () => ({
  useGtagConversions: jest.fn(() => ({ trackWhatsAppClick: jest.fn() })),
}));

import Hero from '../../components/home/Hero.vue';

function mountHero() {
  return mount(Hero, {
    global: {
      stubs: { NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' } },
    },
  });
}

describe('Hero', () => {
  it('renders the section element', () => {
    const wrapper = mountHero();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the hero title parts', () => {
    const wrapper = mountHero();

    expect(wrapper.text()).toContain('Your Trusted');
    expect(wrapper.text()).toContain('Web Design Partner');
  });

  it('renders the primary CTA button', () => {
    const wrapper = mountHero();

    expect(wrapper.text()).toContain('Get In Touch');
  });

  it('renders the book a call CTA when provided', () => {
    const wrapper = mountHero();

    expect(wrapper.text()).toContain('Book a Call');
  });

  it('renders the two feature cards', () => {
    const wrapper = mountHero();

    expect(wrapper.text()).toContain('+50 companies trust us');
    expect(wrapper.text()).toContain('A real advisor replies');
  });

  it('renders the NDA confidentiality note', () => {
    const wrapper = mountHero();

    expect(wrapper.text()).toContain('We sign an NDA so your project stays 100% confidential.');
  });
});
