import { mount } from '@vue/test-utils';
import ViewModuleCard from '../../components/views/ViewModuleCard.vue';

const section = {
  id: 'admin-panel',
  label: 'Panel administrativo',
  description: 'Vistas internas del panel.',
  views: [
    { label: 'Listado', url: '/panel/blog', group: 'Blog', audience: 'admin', viewType: 'list' },
    { label: 'Crear', url: '/panel/blog/create', group: 'Blog', audience: 'admin', viewType: 'create' },
    { label: 'Emails', url: '/panel/emails', group: 'Emails', audience: 'admin', viewType: 'config' },
  ],
};

function mountCard(props = {}) {
  return mount(ViewModuleCard, { props: { section, ...props } });
}

describe('ViewModuleCard', () => {
  it('renders the module label, view count and sub-module count', () => {
    const wrapper = mountCard();

    expect(wrapper.text()).toContain('Panel administrativo');
    expect(wrapper.text()).toContain('3');
    expect(wrapper.text()).toContain('vistas');
    expect(wrapper.text()).toContain('2 sub-módulos');
  });

  it('renders one distribution bar segment per viewType present', () => {
    const wrapper = mountCard();

    const segments = wrapper.findAll('[aria-hidden="true"] > span');
    expect(segments).toHaveLength(3);
  });

  it('emits select with the section id when clicked', async () => {
    const wrapper = mountCard();

    await wrapper.find(`[data-testid="view-module-card-admin-panel"]`).trigger('click');

    expect(wrapper.emitted('select')).toEqual([['admin-panel']]);
  });
});
