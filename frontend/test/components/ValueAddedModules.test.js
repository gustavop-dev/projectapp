import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import ValueAddedModules from '../../components/BusinessProposal/ValueAddedModules.vue';

const FR_GROUPS = [
  { id: 'admin_module', icon: '🛠️', title: 'Módulo Administrativo', description: 'Admin desc' },
  { id: 'analytics_dashboard', icon: '📊', title: 'Módulo de Analítica', description: 'Analytics desc' },
  { id: 'kpi_dashboard_module', icon: '📊', title: 'Dashboard de KPIs', description: 'KPI desc' },
  { id: 'manual_module', icon: '📘', title: 'Manual de Usuario Interactivo', description: 'Manual desc' },
];

function mountSection(overrides = {}) {
  const section = {
    section_type: 'value_added_modules',
    content_json: {
      index: '9',
      title: 'Lo que sumamos',
      intro: 'Todo gratis para ti.',
      module_ids: ['admin_module', 'analytics_dashboard', 'kpi_dashboard_module', 'manual_module'],
      justifications: {
        admin_module: 'Para no depender del developer.',
        analytics_dashboard: 'Para entender a tu audiencia.',
        kpi_dashboard_module: 'Para decisiones basadas en datos.',
        manual_module: 'Para que el equipo entienda el sistema.',
      },
      footer_note: 'Total adicional: $0.',
      ...overrides.contentJson,
    },
  };
  const proposal = {
    language: 'es',
    sections: [
      { section_type: 'functional_requirements', content_json: { groups: FR_GROUPS } },
    ],
    ...overrides.proposal,
  };
  return mount(ValueAddedModules, { props: { section, proposal } });
}

describe('ValueAddedModules', () => {
  it('renders one card per module_id when all ids resolve in functional_requirements', () => {
    const wrapper = mountSection();
    const cards = wrapper.findAll('[data-testid^="value-added-card-"]');
    expect(cards).toHaveLength(4);
  });

  it('skips cards whose module_id is not present in functional_requirements', () => {
    const wrapper = mountSection({
      contentJson: {
        module_ids: ['admin_module', 'unknown_module'],
        justifications: { admin_module: 'a', unknown_module: 'b' },
      },
    });
    const cards = wrapper.findAll('[data-testid^="value-added-card-"]');
    expect(cards).toHaveLength(1);
    expect(wrapper.html()).toContain('Módulo Administrativo');
    expect(wrapper.html()).not.toContain('unknown_module');
  });

  it('renders the justification text for each module', () => {
    const wrapper = mountSection();
    expect(wrapper.text()).toContain('Para no depender del developer.');
    expect(wrapper.text()).toContain('Para que el equipo entienda el sistema.');
  });

  it('renders the footer note when provided', () => {
    const wrapper = mountSection();
    expect(wrapper.text()).toContain('Total adicional: $0.');
  });

  it('renders Spanish i18n labels when proposal.language is "es"', () => {
    const wrapper = mountSection();
    expect(wrapper.text()).toContain('Sin costo adicional');
    expect(wrapper.text()).toContain('Gratis');
  });

  it('renders English i18n labels when proposal.language is "en"', () => {
    const wrapper = mountSection({
      contentJson: { title: '' },
      proposal: {
        language: 'en',
        sections: [
          { section_type: 'functional_requirements', content_json: { groups: FR_GROUPS } },
        ],
      },
    });
    expect(wrapper.text()).toContain('No extra cost');
    expect(wrapper.text()).toContain('Free');
    expect(wrapper.text()).toContain('Included at no extra cost');
  });
});
