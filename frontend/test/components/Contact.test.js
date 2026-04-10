import { mount } from '@vue/test-utils';

global.useRouter = jest.fn(() => ({ push: jest.fn() }));
global.useLocalePath = jest.fn(() => (path) => path);

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to: jest.fn(), add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
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

jest.mock('../../composables/useMessages', () => ({
  useGlobalMessages: jest.fn(() => ({
    globalMessages: {
      heading: 'Let\'s Work Together',
      mail_us_title: 'Mail Us',
      mail_us_description: 'Send us an email',
      email_address: 'team@projectapp.co',
      direct_contact_title: 'Chat',
      direct_contact_description: 'WhatsApp chat',
      chat: 'WhatsApp',
    },
  })),
}));

import Contact from '../../components/layouts/Contact.vue';

function mountContact() {
  return mount(Contact, {
    global: {
      stubs: { Email: true },
    },
  });
}

describe('Contact', () => {
  it('renders the section element', () => {
    const wrapper = mountContact();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the mail us title', () => {
    const wrapper = mountContact();

    expect(wrapper.text()).toContain('Mail Us');
  });

  it('renders the email address link', () => {
    const wrapper = mountContact();

    expect(wrapper.text()).toContain('team@projectapp.co');
  });

  it('renders the WhatsApp chat link', () => {
    const wrapper = mountContact();

    expect(wrapper.text()).toContain('WhatsApp');
  });

  it('renders two contact article cards', () => {
    const wrapper = mountContact();

    expect(wrapper.findAll('article')).toHaveLength(2);
  });
});
