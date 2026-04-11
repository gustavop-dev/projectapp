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
      unrepeatable: {
        title: 'unrepeatable.',
        processTitle1: 'A Thoughtful Process Designed for',
        processTitle2: 'Outstanding Results',
        card1Title: 'Architecture & Planning',
        card2Title: 'UI/UX Design',
        card3Title: 'Development & Implementation',
      },
    }),
  })),
}));

import UnrepeatableSection from '../../components/home/UnrepeatableSection.vue';

function mountSection() {
  return mount(UnrepeatableSection, {
    global: {
      stubs: {
        ClientOnly: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('UnrepeatableSection', () => {
  it('renders the section element', () => {
    const wrapper = mountSection();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the unrepeatable title', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain('unrepeatable.');
  });

  it('renders the process section title', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain('A Thoughtful Process Designed for');
  });

  it('renders process card titles', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain('Architecture & Planning');
    expect(wrapper.text()).toContain('UI/UX Design');
  });

  it('renders the Development card', () => {
    const wrapper = mountSection();

    expect(wrapper.text()).toContain('Development & Implementation');
  });
});
