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

jest.mock('pinia', () => ({
  storeToRefs: jest.fn((store) => store),
  defineStore: jest.fn(),
}));

jest.mock('../../stores/language', () => ({
  useLanguageStore: jest.fn(() => ({
    messages: require('vue').ref({
      contactSuccess: {
        title: '¡Gracias!',
        message: 'Nos pondremos en contacto contigo.',
        button: 'Ver portafolio',
      },
    }),
    currentLocale: require('vue').ref('es-co'),
  })),
}));

import ContactSuccess from '../../components/pages/ContactSuccess.vue';

function mountContactSuccess() {
  return mount(ContactSuccess);
}

describe('ContactSuccess', () => {
  it('renders the main element', () => {
    const wrapper = mountContactSuccess();

    expect(wrapper.find('main').exists()).toBe(true);
  });

  it('renders the success title', () => {
    const wrapper = mountContactSuccess();

    expect(wrapper.text()).toContain('¡Gracias!');
  });

  it('renders the success message', () => {
    const wrapper = mountContactSuccess();

    expect(wrapper.text()).toContain('Nos pondremos en contacto contigo.');
  });

  it('renders the portfolio link button', () => {
    const wrapper = mountContactSuccess();

    expect(wrapper.find('a').exists()).toBe(true);
    expect(wrapper.text()).toContain('Ver portafolio');
  });
});
