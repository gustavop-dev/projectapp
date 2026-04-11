import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import PanelMobileDrawer from '../../components/panel/PanelMobileDrawer.vue';

jest.mock('../../config/panelNav', () => ({
  getPanelNavSections: jest.fn(() => ([
    {
      id: 'main',
      label: 'Principal',
      muted: false,
      items: [
        { href: '/panel', label: 'Inicio', disabled: false },
        { href: '/panel/blog', label: 'Blog', disabled: true },
      ],
    },
    {
      id: 'muted',
      label: 'Archivado',
      muted: true,
      items: [
        { href: '/panel/docs', label: 'Docs', disabled: false },
      ],
    },
  ])),
}));

jest.mock('../../utils/panelNavActive', () => ({
  isPanelNavItemActive: jest.fn((path, item) => path === item.href),
}));

function mountDrawer(props = {}) {
  global.useLocalePath = () => (path) => path;
  global.useRoute = () => ({ path: '/panel' });

  return mount(PanelMobileDrawer, {
    props: {
      isOpen: true,
      ...props,
    },
    global: {
      stubs: {
        Teleport: true,
        Transition: false,
        SidebarItem: {
          props: ['item', 'isCollapsed', 'isActive', 'disabled'],
          template: `
            <div
              class="sidebar-item"
              :data-label="item.label"
              :data-active="String(isActive)"
              :data-disabled="String(disabled)"
            >
              {{ item.label }}
            </div>
          `,
        },
      },
    },
  });
}

describe('PanelMobileDrawer', () => {
  afterEach(() => {
    delete global.useLocalePath;
    delete global.useRoute;
  });

  it('does not render overlay or drawer when closed', () => {
    const wrapper = mountDrawer({ isOpen: false });

    expect(wrapper.html()).not.toContain('Close menu');
    expect(wrapper.find('aside').exists()).toBe(false);
  });

  it('renders sections and passes item state to SidebarItem stubs', () => {
    const wrapper = mountDrawer();
    const items = wrapper.findAll('.sidebar-item');

    expect(wrapper.text()).toContain('Principal');
    expect(wrapper.text()).toContain('Archivado');
    expect(items).toHaveLength(3);
    expect(items[0].attributes('data-active')).toBe('true');
    expect(items[1].attributes('data-disabled')).toBe('true');
  });

  it('emits close when the backdrop is clicked', async () => {
    const wrapper = mountDrawer();

    await wrapper.get('.fixed.inset-0.z-40').trigger('click');

    expect(wrapper.emitted('close')).toEqual([[]]);
  });

  it('emits close when the close button is clicked', async () => {
    const wrapper = mountDrawer();

    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.emitted('close')).toEqual([[]]);
  });

  it('emits close and toggle-theme from the footer action', async () => {
    const wrapper = mountDrawer();

    await wrapper.findAll('button')[2].trigger('click');
    await nextTick();

    expect(wrapper.emitted('close')).toEqual([[]]);
    expect(wrapper.emitted('toggle-theme')).toEqual([[]]);
  });
});
