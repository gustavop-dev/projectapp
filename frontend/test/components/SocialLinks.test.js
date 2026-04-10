import { mount } from '@vue/test-utils';

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to: jest.fn(), add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('@heroicons/vue/20/solid/ArrowUpRightIcon', () => ({
  __esModule: true,
  default: { name: 'ArrowUpRightIcon', template: '<svg />' },
}), { virtual: true });

import SocialLinks from '../../components/utils/SocialLinks.vue';

function mountSocialLinks() {
  return mount(SocialLinks, { attachTo: document.body });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('SocialLinks', () => {
  it('renders 3 social link anchors', () => {
    const wrapper = mountSocialLinks();

    expect(wrapper.findAll('a.js-social-link')).toHaveLength(3);
  });

  it('renders Instagram link', () => {
    const wrapper = mountSocialLinks();

    expect(wrapper.text()).toContain('Instagram');
  });

  it('renders Facebook link', () => {
    const wrapper = mountSocialLinks();

    expect(wrapper.text()).toContain('Facebook');
  });

  it('renders WhatsApp link', () => {
    const wrapper = mountSocialLinks();

    expect(wrapper.text()).toContain('WhatsApp');
  });

  it('all links open in a new tab', () => {
    const wrapper = mountSocialLinks();

    const links = wrapper.findAll('a.js-social-link');
    links.forEach((link) => {
      expect(link.attributes('target')).toBe('_blank');
    });
  });
});
