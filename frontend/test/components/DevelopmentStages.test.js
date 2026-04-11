import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import DevelopmentStages from '../../components/BusinessProposal/DevelopmentStages.vue';

const sampleStages = [
  { icon: '✉️', title: 'Propuesta Comercial', description: 'Etapa actual.', current: true },
  { icon: '🧾', title: 'Borrador de Contrato', description: 'Términos y condiciones.', current: false },
  { icon: '🚀', title: 'Lanzamiento', description: 'Despliegue final.', current: false },
];

function mountStages(props = {}) {
  return mount(DevelopmentStages, {
    props: {
      title: 'Etapas de Desarrollo',
      stages: sampleStages,
      currentLabel: 'Actual',
      ...props,
    },
  });
}

describe('DevelopmentStages', () => {
  it('renders the section title', () => {
    const wrapper = mountStages();

    expect(wrapper.text()).toContain('Etapas de Desarrollo');
  });

  it('renders all stage cards', () => {
    const wrapper = mountStages();

    expect(wrapper.text()).toContain('Propuesta Comercial');
    expect(wrapper.text()).toContain('Borrador de Contrato');
    expect(wrapper.text()).toContain('Lanzamiento');
  });

  it('renders the current label badge on the active stage', () => {
    const wrapper = mountStages({ currentLabel: 'En curso' });

    expect(wrapper.text()).toContain('En curso');
  });

  it('renders the intro text', () => {
    const wrapper = mountStages({ intro: 'Proceso claro y estructurado.' });

    expect(wrapper.text()).toContain('Proceso claro y estructurado.');
  });

  it('renders the section index', () => {
    const wrapper = mountStages({ index: '06' });

    expect(wrapper.text()).toContain('06');
  });
});
