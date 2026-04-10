import { mount } from '@vue/test-utils';

jest.mock('swiper/vue', () => ({
  Swiper: { name: 'Swiper', template: '<div><slot /></div>' },
  SwiperSlide: { name: 'SwiperSlide', template: '<div><slot /></div>' },
}));
jest.mock('swiper/modules', () => ({ Pagination: {} }));
jest.mock('swiper/css', () => {}, { virtual: true });
jest.mock('swiper/css/pagination', () => {}, { virtual: true });

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
      add: jest.fn().mockReturnThis(),
      play: jest.fn().mockReturnThis(),
      kill: jest.fn().mockReturnThis(),
    })),
    registerPlugin: jest.fn(),
    killTweensOf: jest.fn(),
    context: jest.fn(() => ({ revert: jest.fn() })),
  },
}));

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      contactForm: {
        title: 'Hi there!',
        subtitle: 'tell us what you need',
        submit: 'Submit',
      },
      services: {
        card2: { title: 'Awesome UI Design', description: 'Great design' },
        card3: { title: 'Data-Driven Performance', description: 'Fast results' },
      },
    }),
  })),
}));

jest.mock('pinia', () => ({
  storeToRefs: jest.fn((store) => store),
  defineStore: jest.fn(),
}));

jest.mock('../../stores/language', () => ({
  useLanguageStore: jest.fn(() => ({
    currentLocale: require('vue').ref('es-co'),
  })),
}));

jest.mock('../../stores/contacts', () => ({
  useContactsStore: jest.fn(() => ({
    isSubmitting: require('vue').ref(false),
    submitSuccess: require('vue').ref(false),
    submitError: require('vue').ref(null),
    sendContact: jest.fn(),
  })),
}));

jest.mock('../../composables/useGtagConversions', () => ({
  useGtagConversions: jest.fn(() => ({ trackFormSubmission: jest.fn() })),
}));

global.useRouter = jest.fn(() => ({ push: jest.fn() }));

import ServicesCardsApps from '../../components/landing/ServicesCardsApps.vue';

function mountServicesCardsApps() {
  return mount(ServicesCardsApps, {
    global: {
      stubs: { ClientOnly: { template: '<div><slot /></div>' } },
    },
  });
}

describe('ServicesCardsApps', () => {
  it('renders the form element', () => {
    const wrapper = mountServicesCardsApps();

    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('renders the form title', () => {
    const wrapper = mountServicesCardsApps();

    expect(wrapper.text()).toContain('Hi there!');
  });

  it('renders the submit button', () => {
    const wrapper = mountServicesCardsApps();

    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('renders service card titles', () => {
    const wrapper = mountServicesCardsApps();

    expect(wrapper.text()).toContain('Awesome UI Design');
  });

  it('renders the fullName input field', () => {
    const wrapper = mountServicesCardsApps();

    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
  });
});
