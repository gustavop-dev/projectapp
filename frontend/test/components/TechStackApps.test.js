import { mount } from '@vue/test-utils';

// SVG files not in moduleNameMapper — need virtual mocks
jest.mock('assets/images/icons/figma.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/react-native-1.svg', () => '', { virtual: true });
jest.mock('assets/images/icons/stripe.svg', () => '', { virtual: true });

import TechStackApps from '../../components/landing/TechStackApps.vue';

function mountTechStackApps() {
  return mount(TechStackApps);
}

describe('TechStackApps', () => {
  it('renders the section element', () => {
    const wrapper = mountTechStackApps();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the tech-bubble container', () => {
    const wrapper = mountTechStackApps();

    expect(wrapper.find('.tech-bubble').exists()).toBe(true);
  });

  it('renders 7 tech icon images', () => {
    const wrapper = mountTechStackApps();

    expect(wrapper.findAll('.tech-icon')).toHaveLength(7);
  });

  it('renders Flutter icon', () => {
    const wrapper = mountTechStackApps();

    const flutter = wrapper.findAll('img').find(img => img.attributes('alt') === 'Flutter');
    expect(flutter).toBeTruthy();
  });

  it('renders Android icon', () => {
    const wrapper = mountTechStackApps();

    const android = wrapper.findAll('img').find(img => img.attributes('alt') === 'Android');
    expect(android).toBeTruthy();
  });
});
