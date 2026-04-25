import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../stores/services/request_http', () => ({
  create_request: jest.fn(),
}));

import FunctionalRequirements from '../../components/BusinessProposal/FunctionalRequirements.vue';

const sampleData = {
  index: '7',
  title: 'Requerimientos Funcionales',
  intro: 'A continuación se detallan los requerimientos funcionales.',
  groups: [
    { id: 'auth', title: 'Autenticación', description: 'Login y registro', icon: '🔐', items: [{ name: 'Login' }], is_visible: true },
    { id: 'dash', title: 'Dashboard', description: 'Panel principal', icon: '📊', items: [{ name: 'Overview' }], is_visible: true },
  ],
  additionalModules: [],
};

function mountReqs(props = {}) {
  return mount(FunctionalRequirements, {
    props: { data: sampleData, ...props },
    global: { stubs: { FunctionalRequirementsModal: true } },
  });
}

describe('FunctionalRequirements', () => {
  it('renders the section title', () => {
    const wrapper = mountReqs();

    expect(wrapper.text()).toContain('Requerimientos Funcionales');
  });

  it('renders the intro text', () => {
    const wrapper = mountReqs();

    expect(wrapper.text()).toContain('A continuación se detallan los requerimientos funcionales.');
  });

  it('renders overview cards for each group', () => {
    const wrapper = mountReqs();

    expect(wrapper.findAll('.overview-card')).toHaveLength(2);
  });

  it('renders group titles in the overview cards', () => {
    const wrapper = mountReqs();

    expect(wrapper.text()).toContain('Autenticación');
    expect(wrapper.text()).toContain('Dashboard');
  });

  it('shows item count badge for each group', () => {
    const wrapper = mountReqs();

    expect(wrapper.findAll('.badge-count')).toHaveLength(2);
  });

  describe('valueAddedModuleIds filter', () => {
    const dataWithVamModules = {
      index: '9',
      title: 'Todo lo que incluye tu proyecto',
      intro: 'A continuación se detallan los requerimientos funcionales.',
      groups: [
        { id: 'views', title: 'Vistas', description: 'Pantallas', icon: '🖥️', items: [{ name: 'Home' }], is_visible: true },
        { id: 'components', title: 'Componentes', description: 'Reusables', icon: '🧩', items: [{ name: 'Header' }], is_visible: true },
        { id: 'features', title: 'Funcionalidades', description: 'Acciones', icon: '⚙️', items: [{ name: 'Search' }], is_visible: true },
        { id: 'admin_module', title: 'Módulo Administrativo', description: 'Admin', icon: '🛠️', items: [{ name: 'Products' }], is_visible: true },
        { id: 'analytics_dashboard', title: 'Analítica', description: 'Reportes', icon: '📊', items: [{ name: 'Visitas' }], is_visible: true },
        { id: 'kpi_dashboard_module', title: 'KPIs', description: 'Métricas', icon: '📊', items: [{ name: 'KPI' }], is_visible: true },
        { id: 'manual_module', title: 'Manual', description: 'Wiki', icon: '📘', items: [{ name: 'Index' }], is_visible: true },
      ],
      additionalModules: [],
    };

    it('hides groups whose id is in valueAddedModuleIds when the array is non-empty', () => {
      const wrapper = mount(FunctionalRequirements, {
        props: {
          data: dataWithVamModules,
          valueAddedModuleIds: ['admin_module', 'analytics_dashboard', 'kpi_dashboard_module', 'manual_module'],
        },
        global: { stubs: { FunctionalRequirementsModal: true } },
      });
      const titles = wrapper.findAll('.overview-card').map(c => c.text());
      expect(titles.filter(t => ['Vistas', 'Componentes', 'Funcionalidades'].some(k => t.includes(k)))).toHaveLength(3);
      expect(wrapper.text()).not.toContain('Módulo Administrativo');
      expect(wrapper.text()).not.toContain('Analítica');
      expect(wrapper.text()).not.toContain('KPIs');
      expect(wrapper.text()).not.toContain('Manual');
    });

    it('shows all base groups when valueAddedModuleIds is empty (VAM section disabled)', () => {
      const wrapper = mount(FunctionalRequirements, {
        props: {
          data: dataWithVamModules,
          valueAddedModuleIds: [],
        },
        global: { stubs: { FunctionalRequirementsModal: true } },
      });
      expect(wrapper.findAll('.overview-card')).toHaveLength(7);
      expect(wrapper.text()).toContain('Módulo Administrativo');
      expect(wrapper.text()).toContain('Manual');
    });

    it('shows all base groups when valueAddedModuleIds prop is not provided (back-compat)', () => {
      const wrapper = mount(FunctionalRequirements, {
        props: { data: dataWithVamModules },
        global: { stubs: { FunctionalRequirementsModal: true } },
      });
      expect(wrapper.findAll('.overview-card')).toHaveLength(7);
    });
  });
});
