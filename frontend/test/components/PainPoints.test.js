import { mount } from '@vue/test-utils';

jest.mock('swiper/vue', () => ({
  Swiper: { name: 'Swiper', template: '<div><slot /></div>' },
  SwiperSlide: { name: 'SwiperSlide', template: '<div><slot /></div>' },
}));
jest.mock('swiper/modules', () => ({ Pagination: {} }));
jest.mock('swiper/css', () => {}, { virtual: true });
jest.mock('swiper/css/pagination', () => {}, { virtual: true });

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      painPoints: {
        title: 'Challenges we solve',
        bridge: 'We turn your pain points into strengths.',
        cards: [
          { title: 'Slow development', description: 'We ship in weeks, not months.' },
          { title: 'High costs', description: 'Affordable without sacrificing quality.' },
          { title: 'Poor UX', description: 'User-first design always.' },
        ],
      },
    }),
  })),
}));

import PainPoints from '../../components/landing/PainPoints.vue';

function mountPainPoints() {
  return mount(PainPoints, {
    global: {
      stubs: { ClientOnly: { template: '<div><slot /></div>' } },
    },
  });
}

describe('PainPoints', () => {
  it('renders the section element', () => {
    const wrapper = mountPainPoints();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the section title', () => {
    const wrapper = mountPainPoints();

    expect(wrapper.text()).toContain('Challenges we solve');
  });

  it('renders the bridge text', () => {
    const wrapper = mountPainPoints();

    expect(wrapper.text()).toContain('We turn your pain points into strengths.');
  });

  it('renders desktop pain point cards', () => {
    const wrapper = mountPainPoints();

    expect(wrapper.text()).toContain('Slow development');
    expect(wrapper.text()).toContain('High costs');
  });
});
