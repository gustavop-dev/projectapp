import { mount } from '@vue/test-utils';

jest.mock('gsap', () => ({
  __esModule: true,
  default: {
    from: jest.fn(),
    to: jest.fn(),
    set: jest.fn(),
    fromTo: jest.fn(),
    timeline: jest.fn(() => ({
      to: jest.fn().mockReturnThis(),
      from: jest.fn().mockReturnThis(),
      fromTo: jest.fn().mockReturnThis(),
    })),
    registerPlugin: jest.fn(),
    killTweensOf: jest.fn(),
  },
}));

jest.mock('../../animations', () => ({
  waveEmoji: jest.fn(),
}));

jest.mock('pinia', () => ({
  storeToRefs: jest.fn((store) => store),
  defineStore: jest.fn(),
}));

jest.mock('../../stores/language', () => ({
  useLanguageStore: jest.fn(() => ({
    messages: require('vue').ref({
      contact: {
        title: 'Need a professional website?',
        subtitle: 'We develop custom websites.',
        form: {
          fullName: 'Full name',
          phone: 'Phone number',
          email: 'Your email',
          project: 'Tell us about your project',
          budget: 'Estimated budget',
          submit: 'Send message',
        },
        budgetOptions: ['500-5K', '5-10K', '10-20K'],
      },
    }),
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

import ContactPage from '../../components/pages/ContactPage.vue';

function mountContactPage() {
  return mount(ContactPage);
}

describe('ContactPage', () => {
  it('renders the main element', () => {
    const wrapper = mountContactPage();

    expect(wrapper.find('main').exists()).toBe(true);
  });

  it('renders the page title', () => {
    const wrapper = mountContactPage();

    expect(wrapper.text()).toContain('Need a professional website?');
  });

  it('renders the contact form', () => {
    const wrapper = mountContactPage();

    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('renders the submit button', () => {
    const wrapper = mountContactPage();

    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('renders budget option buttons', () => {
    const wrapper = mountContactPage();

    expect(wrapper.text()).toContain('500-5K');
  });
});
