import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../stores/services/request_http', () => ({
  create_request: jest.fn(() => Promise.resolve({ data: {} })),
}));

import ValueAddedModules from '../../components/BusinessProposal/ValueAddedModules.vue';
import { create_request } from '../../stores/services/request_http';

const FR_GROUPS = [
  {
    id: 'admin_module',
    icon: '🛠️',
    title: 'Módulo Administrativo',
    description: 'Admin desc',
    items: [
      { icon: '📂', name: 'Gestor de Productos', description: 'CRUD productos' },
      { icon: '🗂️', name: 'Gestor de Categorías', description: 'CRUD categorías' },
    ],
  },
  {
    id: 'analytics_dashboard',
    icon: '📊',
    title: 'Módulo de Analítica',
    description: 'Analytics desc',
    items: [
      { icon: '🔥', name: 'Más visitados', description: 'Top páginas' },
    ],
  },
  { id: 'kpi_dashboard_module', icon: '📊', title: 'Dashboard de KPIs', description: 'KPI desc', items: [] },
  { id: 'manual_module', icon: '📘', title: 'Manual de Usuario Interactivo', description: 'Manual desc', items: [] },
];

const ModalStub = {
  name: 'FunctionalRequirementsModal',
  props: ['visible', 'group'],
  template: '<div data-testid="frm-stub" v-if="visible" :data-group-id="group?.id" :data-items-count="group?.items?.length ?? 0" />',
};

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
  return mount(ValueAddedModules, {
    props: {
      section,
      proposal,
      ...(overrides.props || {}),
    },
    global: {
      stubs: { FunctionalRequirementsModal: ModalStub },
    },
  });
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

  it('does not render the section when module_ids is empty', () => {
    const wrapper = mountSection({
      contentJson: { module_ids: [], justifications: {} },
    });
    expect(wrapper.find('section').exists()).toBe(false);
  });

  it('does not render the section when no module_ids resolve in functional_requirements', () => {
    const wrapper = mountSection({
      contentJson: {
        module_ids: ['foo', 'bar'],
        justifications: { foo: 'x', bar: 'y' },
      },
      proposal: {
        language: 'es',
        sections: [
          { section_type: 'functional_requirements', content_json: { groups: [] } },
        ],
      },
    });
    expect(wrapper.find('section').exists()).toBe(false);
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

  describe('card click → modal', () => {
    function setSearch(search) {
      // history.pushState is supported by jsdom and updates window.location.search
      window.history.pushState({}, '', `/proposal/abc${search}`);
    }
    beforeEach(() => {
      create_request.mockClear();
      setSearch('');
    });
    afterAll(() => {
      setSearch('');
    });

    it('opens the modal with the clicked group (including items from the FR catalog)', async () => {
      const wrapper = mountSection();
      // Modal starts hidden
      expect(wrapper.find('[data-testid="frm-stub"]').exists()).toBe(false);

      await wrapper.find('[data-testid="value-added-card-admin_module"]').trigger('click');

      const modal = wrapper.find('[data-testid="frm-stub"]');
      expect(modal.exists()).toBe(true);
      expect(modal.attributes('data-group-id')).toBe('admin_module');
      expect(modal.attributes('data-items-count')).toBe('2');
    });

    it('opens the modal with an empty items array when the catalog group has no items', async () => {
      const wrapper = mountSection();
      await wrapper.find('[data-testid="value-added-card-kpi_dashboard_module"]').trigger('click');

      const modal = wrapper.find('[data-testid="frm-stub"]');
      expect(modal.exists()).toBe(true);
      expect(modal.attributes('data-group-id')).toBe('kpi_dashboard_module');
      expect(modal.attributes('data-items-count')).toBe('0');
    });

    it('opens the modal via keyboard Enter', async () => {
      const wrapper = mountSection();
      await wrapper.find('[data-testid="value-added-card-admin_module"]').trigger('keydown.enter');
      expect(wrapper.find('[data-testid="frm-stub"]').exists()).toBe(true);
    });

    it('fires tracking when proposalUuid is provided and URL is not preview', async () => {
      const wrapper = mountSection({ props: { proposalUuid: 'abc-123' } });
      await wrapper.find('[data-testid="value-added-card-admin_module"]').trigger('click');

      expect(create_request).toHaveBeenCalledTimes(1);
      expect(create_request).toHaveBeenCalledWith(
        'proposals/abc-123/track-requirement-click/',
        { group_id: 'admin_module', group_title: 'Módulo Administrativo' },
      );
    });

    it('does not fire tracking when preview=1 is set on the URL', async () => {
      setSearch('?preview=1');
      const wrapper = mountSection({ props: { proposalUuid: 'abc-123' } });
      await wrapper.find('[data-testid="value-added-card-admin_module"]').trigger('click');

      expect(create_request).not.toHaveBeenCalled();
    });

    it('does not fire tracking when proposalUuid is empty', async () => {
      const wrapper = mountSection(); // no proposalUuid prop
      await wrapper.find('[data-testid="value-added-card-admin_module"]').trigger('click');
      expect(create_request).not.toHaveBeenCalled();
    });
  });
});
