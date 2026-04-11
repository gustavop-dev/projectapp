import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));

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
jest.mock('swiper/modules', () => ({ Pagination: {} }));
jest.mock('swiper/css', () => {}, { virtual: true });
jest.mock('swiper/css/pagination', () => {}, { virtual: true });

jest.mock('pinia', () => ({
  storeToRefs: jest.fn((store) => store),
  defineStore: jest.fn(),
}));

jest.mock('../../stores/language', () => ({
  useLanguageStore: jest.fn(() => ({ currentLocale: require('vue').ref('es-co') })),
}));

jest.mock('../../stores/contacts', () => ({
  useContactsStore: jest.fn(() => ({
    isSubmitting: require('vue').ref(false),
    submitSuccess: require('vue').ref(false),
    submitError: require('vue').ref(null),
    sendContact: jest.fn(() => Promise.resolve({ success: false })),
  })),
}));

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      contactForm: {
        title: 'Hi there!',
        subtitle: 'tell us what you need',
        fullName: 'Full name',
        phone: 'Phone number',
        email: 'Your email address',
        message: 'Tell us about your project',
        submit: 'Submit',
        sending: 'Sending...',
      },
      services: {
        card2: { title: 'Awesome UI Design' },
        card3: { title: 'Data-Driven Performance' },
      },
    }),
  })),
}));

jest.mock('../../composables/useGtagConversions', () => ({
  useGtagConversions: jest.fn(() => ({ trackFormSubmission: jest.fn() })),
}));

import ServicesCards from '../../components/home/ServicesCards.vue';

function mountServicesCards() {
  return mount(ServicesCards, {
    global: {
      stubs: {
        ClientOnly: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ServicesCards', () => {
  it('renders the contact form', () => {
    const wrapper = mountServicesCards();

    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('renders the form title', () => {
    const wrapper = mountServicesCards();

    expect(wrapper.text()).toContain('Hi there!');
  });

  it('renders the submit button', () => {
    const wrapper = mountServicesCards();

    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('renders service card titles', () => {
    const wrapper = mountServicesCards();

    expect(wrapper.text()).toContain('Awesome UI Design');
  });

  it('renders the fullname input', () => {
    const wrapper = mountServicesCards();

    const inputs = wrapper.findAll('input');
    expect(inputs.length).toBeGreaterThan(0);
  });
});
