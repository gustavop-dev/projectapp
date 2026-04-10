import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));

jest.mock('gsap', () => {
  const to = jest.fn((target, opts) => { opts?.onComplete?.(); });
  const mock = {
    from: jest.fn(), to, set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to, add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
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
    sendContact: jest.fn(() => Promise.resolve({ success: false })),
  })),
}));

jest.mock('../../composables/useMessages', () => ({
  useGlobalMessages: jest.fn(() => ({
    globalMessages: {
      to_label: 'To',
      to_value: 'team@projectapp.co',
      fullname_label: 'Name',
      fullname_placeholder: 'Full name',
      from_label: 'From',
      email_placeholder: 'your@email.com',
      phone_label: 'Phone',
      phone_placeholder: 'Phone number',
      message_placeholder: 'Your message',
      budget_label: 'Budget',
      send_button: 'Send',
    },
  })),
}));

jest.mock('../../composables/useGtagConversions', () => ({
  useGtagConversions: jest.fn(() => ({ trackFormSubmission: jest.fn() })),
}));

import Email from '../../components/layouts/Email.vue';

function mountEmail(props = {}) {
  return mount(Email, {
    props: { visible: true, ...props },
    attachTo: document.body,
    global: { stubs: { Teleport: true } },
  });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('Email', () => {
  it('renders the form when visible is true', () => {
    const wrapper = mountEmail({ visible: true });

    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('does not render the form when visible is false', () => {
    const wrapper = mountEmail({ visible: false });

    expect(wrapper.find('form').exists()).toBe(false);
  });

  it('renders the fullname input field', () => {
    const wrapper = mountEmail();

    expect(wrapper.find('#fullname-input').exists()).toBe(true);
  });

  it('renders the email input field', () => {
    const wrapper = mountEmail();

    expect(wrapper.find('#email-input').exists()).toBe(true);
  });

  it('renders the send button', () => {
    const wrapper = mountEmail();

    expect(wrapper.find('#form-submit-btn').exists()).toBe(true);
  });

  it('emits update:visible false when a close button is clicked', async () => {
    const wrapper = mountEmail();

    await wrapper.find('button[aria-label="Close contact form"]').trigger('click');

    expect(wrapper.emitted('update:visible')).toBeTruthy();
    expect(wrapper.emitted('update:visible')[0]).toEqual([false]);
  });
});
