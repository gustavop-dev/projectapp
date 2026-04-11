import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);
global.useRoute = jest.fn(() => ({ path: '/' }));

import PanelSidebar from '../../components/panel/PanelSidebar.vue';

jest.mock('../../config/panelNav', () => ({
  getPanelNavSections: jest.fn(() => [
    {
      id: 'main',
      label: 'Principal',
      items: [{ href: '/panel', label: 'Dashboard', icon: 'dashboard' }],
    },
  ]),
}));

jest.mock('../../utils/panelNavActive', () => ({
  isPanelNavItemActive: jest.fn(() => false),
}));

function mountSidebar(props = {}) {
  return mount(PanelSidebar, {
    props: { isCollapsed: false, isDark: false, ...props },
    global: {
      stubs: {
        SidebarItem: true,
        NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' },
      },
    },
  });
}

describe('PanelSidebar', () => {
  it('renders the section label when not collapsed', () => {
    const wrapper = mountSidebar({ isCollapsed: false });

    expect(wrapper.text()).toContain('Principal');
  });

  it('renders the full logo text when not collapsed', () => {
    const wrapper = mountSidebar({ isCollapsed: false });

    expect(wrapper.text()).toContain('ProjectApp.');
  });

  it('hides the section label when collapsed', () => {
    const wrapper = mountSidebar({ isCollapsed: true });

    expect(wrapper.text()).not.toContain('Principal');
  });

  it('renders the collapsed logo abbreviation when isCollapsed is true', () => {
    const wrapper = mountSidebar({ isCollapsed: true });

    expect(wrapper.text()).toContain('PA');
  });

  it('emits toggle-theme when the theme button is clicked', async () => {
    const wrapper = mountSidebar();

    await wrapper.findAll('button')[1].trigger('click');

    expect(wrapper.emitted('toggle-theme')).toHaveLength(1);
  });
});
