import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import ProcessMethodology from '../../components/BusinessProposal/ProcessMethodology.vue';

const sampleSteps = [
  { icon: '🔍', title: 'Discovery', description: 'Investigación inicial', clientAction: 'Briefing' },
  { icon: '🎨', title: 'Diseño', description: 'Prototipos en Figma', clientAction: '' },
  { icon: '💻', title: 'Desarrollo', description: 'Implementación', clientAction: '' },
];

function mountProcess(props = {}) {
  return mount(ProcessMethodology, {
    props: {
      title: 'Proceso y Metodología',
      intro: 'Nuestro proceso garantiza calidad.',
      steps: sampleSteps,
      activeStep: 0,
      ...props,
    },
  });
}

describe('ProcessMethodology', () => {
  it('renders the section title', () => {
    const wrapper = mountProcess();

    expect(wrapper.text()).toContain('Proceso y Metodología');
  });

  it('renders the intro text', () => {
    const wrapper = mountProcess();

    expect(wrapper.text()).toContain('Nuestro proceso garantiza calidad.');
  });

  it('renders all step titles from the steps prop', () => {
    const wrapper = mountProcess();

    expect(wrapper.text()).toContain('Discovery');
    expect(wrapper.text()).toContain('Diseño');
    expect(wrapper.text()).toContain('Desarrollo');
  });

  it('renders the section index', () => {
    const wrapper = mountProcess({ index: '05' });

    expect(wrapper.text()).toContain('05');
  });
});
