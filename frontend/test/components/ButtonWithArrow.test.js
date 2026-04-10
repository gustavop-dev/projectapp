import { mount } from '@vue/test-utils';

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to: jest.fn(), add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('@heroicons/vue/20/solid/ArrowRightIcon', () => ({
  __esModule: true,
  default: { name: 'ArrowRightIcon', template: '<svg class="arrow-right-icon" />' },
}), { virtual: true });

jest.mock('../../composables/useMessages', () => ({
  useGlobalMessages: jest.fn(() => ({ globalMessages: { contact_us: 'Contáctanos' } })),
}));

import ButtonWithArrow from '../../components/utils/ButtonWithArrow.vue';

function mountButton() {
  return mount(ButtonWithArrow, { attachTo: document.body });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('ButtonWithArrow', () => {
  it('renders the button element', () => {
    const wrapper = mountButton();

    expect(wrapper.find('button').exists()).toBe(true);
  });

  it('renders the contact_us message text', () => {
    const wrapper = mountButton();

    expect(wrapper.text()).toContain('Contáctanos');
  });

  it('applies the js-hover-button class to the button', () => {
    const wrapper = mountButton();

    expect(wrapper.find('.js-hover-button').exists()).toBe(true);
  });

  it('renders the arrow icon element', () => {
    const wrapper = mountButton();

    expect(wrapper.find('.js-arrow-icon').exists()).toBe(true);
  });
});
