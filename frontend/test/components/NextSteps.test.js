import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import NextSteps from '../../components/BusinessProposal/NextSteps.vue';

const defaultSteps = [
  { title: 'Revisión', description: 'Revisa la propuesta' },
  { title: 'Confirmación', description: 'Alinear detalles' },
  { title: 'Inicio', description: 'Comenzamos' },
];

function mountNextSteps(props = {}) {
  return mount(NextSteps, {
    props: {
      title: 'Próximos Pasos',
      steps: defaultSteps,
      primaryCTA: { text: 'WhatsApp', link: 'https://wa.me/123' },
      secondaryCTA: { text: 'Agendar', link: 'https://cal.com' },
      contactMethods: [
        { icon: '📧', title: 'Email', value: 'hola@example.com', link: 'mailto:hola@example.com' },
      ],
      ...props,
    },
  });
}

describe('NextSteps', () => {
  it('renders the section title', () => {
    const wrapper = mountNextSteps();

    expect(wrapper.text()).toContain('Próximos Pasos');
  });

  it('renders all step cards from the steps prop', () => {
    const wrapper = mountNextSteps();

    expect(wrapper.findAll('.step-card')).toHaveLength(3);
  });

  it('renders each step title', () => {
    const wrapper = mountNextSteps();

    expect(wrapper.text()).toContain('Revisión');
    expect(wrapper.text()).toContain('Confirmación');
  });

  it('renders contact method cards', () => {
    const wrapper = mountNextSteps();

    expect(wrapper.findAll('.contact-card')).toHaveLength(1);
    expect(wrapper.text()).toContain('Email');
  });

  it('renders the primary CTA link text', () => {
    const wrapper = mountNextSteps();

    expect(wrapper.text()).toContain('WhatsApp');
  });
});
