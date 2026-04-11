import { mount } from '@vue/test-utils';

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: {
      marquee: {
        line1: "Let's build something remarkable together!",
        line2: 'Creative tech for all.',
      },
    },
  })),
}));

import MarqueeStrips from '../../components/home/MarqueeStrips.vue';

function mountMarquee() {
  return mount(MarqueeStrips);
}

describe('MarqueeStrips', () => {
  it('renders the section element', () => {
    const wrapper = mountMarquee();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders two ribbon wrappers', () => {
    const wrapper = mountMarquee();

    expect(wrapper.findAll('.ribbon-wrapper')).toHaveLength(2);
  });

  it('renders the marquee line1 text in ribbons', () => {
    const wrapper = mountMarquee();

    expect(wrapper.text()).toContain("Let's build something remarkable together!");
  });

  it('renders the top ribbon with esmerald background class', () => {
    const wrapper = mountMarquee();

    expect(wrapper.find('.ribbon.bg-esmerald').exists()).toBe(true);
  });

  it('renders the bottom ribbon with lemon background class', () => {
    const wrapper = mountMarquee();

    expect(wrapper.find('.ribbon.bg-lemon').exists()).toBe(true);
  });
});
