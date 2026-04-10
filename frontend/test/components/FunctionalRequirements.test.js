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
});
