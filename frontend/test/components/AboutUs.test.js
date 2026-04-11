import { mount } from '@vue/test-utils';

jest.mock('gsap', () => ({
  gsap: {
    from: jest.fn(),
    to: jest.fn(),
    set: jest.fn(),
    fromTo: jest.fn(),
    timeline: jest.fn(() => ({
      from: jest.fn().mockReturnThis(),
      to: jest.fn().mockReturnThis(),
    })),
    registerPlugin: jest.fn(),
    killTweensOf: jest.fn(),
    context: jest.fn(() => ({ revert: jest.fn() })),
  },
}));

jest.mock('gsap/ScrollTrigger', () => ({
  ScrollTrigger: { refresh: jest.fn(), kill: jest.fn() },
}), { virtual: true });

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      about: {
        label: 'About us',
        main_title_1: 'We are',
        main_title_2: 'Creative',
        main_title_3: 'Developers',
        sub_title_1: 'We build',
        sub_title_2: 'great websites',
      },
      digital_landscape: {
        title: 'Digital Landscape',
        section_label: 'Our approach',
        text_1: 'We work with',
        text_2: 'great clients',
        text_3: 'to build great products',
      },
      team_support: {
        title: 'Team Support',
        text_1: 'We are here',
        text_2: 'for you',
      },
      creatives: {
        title_1: 'Creative minds',
        title_2_part_1: 'We build',
        title_2_part_2: 'the future',
      },
      motivation: {
        title_1: 'We are',
        title_2: 'motivated',
        title_3: 'everyday',
      },
    }),
  })),
}));

import AboutUs from '../../components/pages/AboutUs.vue';

function mountAboutUs() {
  return mount(AboutUs, {
    global: {
      stubs: {
        PastelGradient: { template: '<div class="pastel-gradient" />' },
        Footer: { template: '<footer class="stub-footer" />' },
        Contact: { template: '<div class="stub-contact" />' },
      },
    },
  });
}

describe('AboutUs', () => {
  it('renders the main element', () => {
    const wrapper = mountAboutUs();

    expect(wrapper.find('main').exists()).toBe(true);
  });

  it('renders about title content', () => {
    const wrapper = mountAboutUs();

    expect(wrapper.text()).toContain('We are');
    expect(wrapper.text()).toContain('Creative');
  });

  it('renders the digital landscape section title', () => {
    const wrapper = mountAboutUs();

    expect(wrapper.text()).toContain('Digital Landscape');
  });

  it('renders the PastelGradient component', () => {
    const wrapper = mountAboutUs();

    expect(wrapper.find('.pastel-gradient').exists()).toBe(true);
  });

  it('renders the team support section title', () => {
    const wrapper = mountAboutUs();

    expect(wrapper.text()).toContain('Team Support');
  });
});
