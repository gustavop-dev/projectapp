import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));
global.useLocalePath = jest.fn(() => (path) => path);

jest.mock('gsap', () => {
  const tl = {};
  tl.from = jest.fn(() => tl);
  tl.to = jest.fn(() => tl);
  tl.fromTo = jest.fn(() => tl);
  tl.add = jest.fn(() => tl);
  tl.play = jest.fn(() => tl);
  tl.kill = jest.fn(() => tl);
  tl.set = jest.fn(() => tl);
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => tl),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { __esModule: true, default: mock, gsap: mock, ...mock };
});

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
      contact_section: {
        title: 'Need a professional website?',
        subtitle: 'Tell us your idea.',
        form: {
          fullName: 'Full name',
          phone: 'Phone number',
          email: 'Your email',
          project: 'Tell us about your web project',
          budget: 'Estimated budget',
          submit: 'Send message',
          sending: 'Sending...',
        },
      },
    }),
  })),
}));

jest.mock('../../composables/useGtagConversions', () => ({
  useGtagConversions: jest.fn(() => ({ trackFormSubmission: jest.fn() })),
}));

import ContactSection from '../../components/home/ContactSection.vue';

function mountContactSection() {
  return mount(ContactSection);
}

describe('ContactSection (home)', () => {
  it('renders the section element', () => {
    const wrapper = mountContactSection();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the title text', () => {
    const wrapper = mountContactSection();

    expect(wrapper.text()).toContain('Need a professional website?');
  });

  it('renders the form', () => {
    const wrapper = mountContactSection();

    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('renders the submit button', () => {
    const wrapper = mountContactSection();

    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it('renders budget option buttons', () => {
    const wrapper = mountContactSection();

    const budgetButtons = wrapper.findAll('button[type="button"]');
    expect(budgetButtons.length).toBeGreaterThan(0);
  });
});
