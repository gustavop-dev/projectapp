import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));
global.useLocalePath = jest.fn(() => (path) => path);

// ICO file not in moduleNameMapper
jest.mock('../../assets/images/recentWork/andrearchitecture.ico', () => '', { virtual: true });

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to: jest.fn(), add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { __esModule: true, default: mock, gsap: mock, ...mock };
});

jest.mock('swiper/vue', () => ({
  Swiper: { name: 'Swiper', template: '<div><slot /></div>' },
  SwiperSlide: { name: 'SwiperSlide', template: '<div><slot /></div>' },
}));
jest.mock('swiper/modules', () => ({ Autoplay: {} }));
jest.mock('swiper/css', () => {}, { virtual: true });

jest.mock('pinia', () => ({
  storeToRefs: jest.fn((store) => store),
  defineStore: jest.fn(),
}));

jest.mock('../../stores/language', () => ({
  useLanguageStore: jest.fn(() => ({ currentLocale: require('vue').ref('es-co') })),
}));

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      bentoGrid: {
        title1: 'Design and code',
        title2: 'made Simple',
        subtitle: 'Our team of experts is here to help',
        portfolio: { title: 'Portfolio', ctaPrimary: 'Get in Touch', ctaSecondary: 'Go to Portfolio', recentWork: 'RECENT WORK:' },
        recentWork: {
          taptag: { name: 'TapTag', tag1: 'Design', tag2: 'Vue.js', tag3: 'MySQL', tag4: 'Django' },
          andre: { name: 'Andre Architecture', tag1: 'Design', tag2: 'Webflow', tag3: 'React', tag4: 'Branding' },
        },
        apps: { tooltip: 'Click here to see our presentation' },
      },
    }),
  })),
}));

import BentoGrid from '../../components/home/BentoGrid.vue';

function mountBentoGrid() {
  return mount(BentoGrid, {
    global: {
      stubs: {
        VideoModal: true,
      },
    },
  });
}

describe('BentoGrid', () => {
  it('renders the section element', () => {
    const wrapper = mountBentoGrid();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the section title', () => {
    const wrapper = mountBentoGrid();

    expect(wrapper.text()).toContain('Design and code');
    expect(wrapper.text()).toContain('made Simple');
  });

  it('renders the portfolio card title', () => {
    const wrapper = mountBentoGrid();

    expect(wrapper.text()).toContain('Portfolio');
  });

  it('renders the recent work section', () => {
    const wrapper = mountBentoGrid();

    expect(wrapper.text()).toContain('RECENT WORK:');
  });

  it('renders TapTag and Andre Architecture project items', () => {
    const wrapper = mountBentoGrid();

    expect(wrapper.text()).toContain('TapTag');
    expect(wrapper.text()).toContain('Andre Architecture');
  });
});
