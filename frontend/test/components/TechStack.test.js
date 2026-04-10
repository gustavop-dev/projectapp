import { mount } from '@vue/test-utils';

// vue3-jest strips ~/ from template src attrs → bare paths; SVG not in moduleNameMapper
jest.mock('assets/images/icons/figma.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/webflow.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/astro.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/stripe.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/framer.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/vuejs_logo_icon_169247.svg', () => '', { virtual: true });

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({ messages: {} })),
}));

import TechStack from '../../components/home/TechStack.vue';

function mountTechStack() {
  return mount(TechStack);
}

describe('TechStack', () => {
  it('renders the section element', () => {
    const wrapper = mountTechStack();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the tech-bubble container', () => {
    const wrapper = mountTechStack();

    expect(wrapper.find('.tech-bubble').exists()).toBe(true);
  });

  it('renders 7 tech icon images', () => {
    const wrapper = mountTechStack();

    expect(wrapper.findAll('.tech-icon')).toHaveLength(7);
  });

  it('renders Figma icon with correct alt text', () => {
    const wrapper = mountTechStack();

    const figma = wrapper.findAll('img').find(img => img.attributes('alt') === 'Figma');
    expect(figma).toBeTruthy();
  });

  it('renders Vue.js icon with correct alt text', () => {
    const wrapper = mountTechStack();

    const vue = wrapper.findAll('img').find(img => img.attributes('alt') === 'Vue.js');
    expect(vue).toBeTruthy();
  });
});
