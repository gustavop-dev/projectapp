import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));
global.useLocalePath = jest.fn(() => (path) => path);

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      hero: {
        title_part1: 'Your App Ready',
        title_part2: 'in 30 Days.',
        subtitle: 'We are mobile app developers.',
        cta_primary: 'Get In Touch',
        benefit1_title: 'Fast Development',
        benefit1_text: 'Delivered in weeks',
        benefit2_title: 'Cross Platform',
        benefit2_text: 'iOS and Android',
      },
    }),
  })),
}));

jest.mock('../../composables/useGtagConversions', () => ({
  useGtagConversions: jest.fn(() => ({ trackWhatsAppClick: jest.fn() })),
}));

import HeroApps from '../../components/landing/HeroApps.vue';

function mountHeroApps() {
  return mount(HeroApps);
}

describe('HeroApps', () => {
  it('renders the section element', () => {
    const wrapper = mountHeroApps();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the hero title parts', () => {
    const wrapper = mountHeroApps();

    expect(wrapper.text()).toContain('Your App Ready');
    expect(wrapper.text()).toContain('in 30 Days.');
  });

  it('renders the primary CTA button', () => {
    const wrapper = mountHeroApps();

    expect(wrapper.text()).toContain('Get In Touch');
  });

  it('renders the benefits section', () => {
    const wrapper = mountHeroApps();

    expect(wrapper.text()).toContain('Fast Development');
  });
});
