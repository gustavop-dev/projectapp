import { mount } from '@vue/test-utils';

jest.mock('gsap', () => ({
  __esModule: true,
  default: {
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
  },
}));

import AnimatedTestimonials from '../../components/ui/AnimatedTestimonials.vue';

const testimonials = [
  {
    name: 'Jane Doe',
    designation: 'CEO',
    quote: 'Amazing work done here.',
    src: '/images/jane.jpg',
    watchVideo: true,
    watchVideoText: 'Watch demo',
  },
  {
    name: 'John Smith',
    designation: 'CTO',
    quote: 'Excellent platform quality.',
    src: '/images/john.jpg',
  },
];

function mountAnimatedTestimonials(props = {}) {
  return mount(AnimatedTestimonials, {
    props: { testimonials, ...props },
  });
}

describe('AnimatedTestimonials', () => {
  it('renders the active testimonial name', () => {
    const wrapper = mountAnimatedTestimonials();

    expect(wrapper.text()).toContain('Jane Doe');
  });

  it('renders the testimonial designation', () => {
    const wrapper = mountAnimatedTestimonials();

    expect(wrapper.text()).toContain('CEO');
  });

  it('renders the quote words', () => {
    const wrapper = mountAnimatedTestimonials();

    expect(wrapper.text()).toContain('Amazing');
  });

  it('renders the watch-video button when testimonial has watchVideo', () => {
    const wrapper = mountAnimatedTestimonials();

    const watchBtn = wrapper.findAll('button').find(b => b.text().includes('Watch demo'));
    expect(watchBtn).toBeTruthy();
  });

  it('emits watch-video when the watch video button is clicked', async () => {
    const wrapper = mountAnimatedTestimonials();

    const watchBtn = wrapper.findAll('button').find(b => b.text().includes('Watch demo'));
    await watchBtn.trigger('click');

    expect(wrapper.emitted('watch-video')).toBeTruthy();
    expect(wrapper.emitted('watch-video')[0][0].name).toBe('Jane Doe');
  });
});
