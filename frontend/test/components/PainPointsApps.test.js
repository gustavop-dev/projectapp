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
        title: 'App development challenges',
        bridge: 'We build apps that perform.',
        cards: [
          { title: 'Long time to market', description: 'We launch in 30 days.' },
          { title: 'Cross-platform issues', description: 'Native iOS and Android.' },
        ],
      },
    }),
  })),
}));

import PainPointsApps from '../../components/landing/PainPointsApps.vue';

function mountPainPointsApps() {
  return mount(PainPointsApps, {
    global: {
      stubs: { ClientOnly: { template: '<div><slot /></div>' } },
    },
  });
}

describe('PainPointsApps', () => {
  it('renders the section element', () => {
    const wrapper = mountPainPointsApps();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the section title', () => {
    const wrapper = mountPainPointsApps();

    expect(wrapper.text()).toContain('App development challenges');
  });

  it('renders the bridge text', () => {
    const wrapper = mountPainPointsApps();

    expect(wrapper.text()).toContain('We build apps that perform.');
  });

  it('renders desktop pain point card titles', () => {
    const wrapper = mountPainPointsApps();

    expect(wrapper.text()).toContain('Long time to market');
  });
});
