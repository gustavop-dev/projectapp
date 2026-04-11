import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import FunctionalRequirementsGroup from '../../components/BusinessProposal/FunctionalRequirementsGroup.vue';

const sampleGroup = {
  id: 'auth',
  icon: '🔐',
  title: 'Autenticación',
  description: 'Módulo de autenticación de usuarios',
  items: [
    { icon: '✅', name: 'Login', description: 'Inicio de sesión seguro' },
    { icon: '✅', name: 'Registro', description: 'Registro de nuevos usuarios' },
  ],
};

function mountGroup(props = {}) {
  return mount(FunctionalRequirementsGroup, {
    props: { group: sampleGroup, subIndex: '7.1', ...props },
  });
}

describe('FunctionalRequirementsGroup', () => {
  it('renders the group title', () => {
    const wrapper = mountGroup();

    expect(wrapper.text()).toContain('Autenticación');
  });

  it('renders the group description', () => {
    const wrapper = mountGroup();

    expect(wrapper.text()).toContain('Módulo de autenticación de usuarios');
  });

  it('renders all requirement items from group.items', () => {
    const wrapper = mountGroup();

    const cards = wrapper.findAll('.requirement-card');
    expect(cards).toHaveLength(2);
  });

  it('renders the subIndex text', () => {
    const wrapper = mountGroup({ subIndex: '3.2' });

    expect(wrapper.text()).toContain('3.2');
  });

  it('renders each item name', () => {
    const wrapper = mountGroup();

    expect(wrapper.text()).toContain('Login');
    expect(wrapper.text()).toContain('Registro');
  });
});
