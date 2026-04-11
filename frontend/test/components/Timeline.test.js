import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import Timeline from '../../components/BusinessProposal/Timeline.vue';

const samplePhases = [
  {
    title: 'Discovery',
    duration: 'Semana 1-2',
    weeks: '2 semanas',
    description: 'Fase de investigación.',
    tasks: ['Reunión de kickoff', 'Análisis competitivo'],
    milestone: 'Aprobación de estrategia',
  },
  {
    title: 'Desarrollo',
    duration: 'Semana 3-6',
    weeks: '4 semanas',
    description: 'Implementación técnica.',
    tasks: ['Setup del servidor', 'Desarrollo frontend'],
    milestone: '',
  },
];

function mountTimeline(props = {}) {
  return mount(Timeline, {
    props: {
      title: 'Cronograma del Proyecto',
      totalDuration: '6 Semanas',
      phases: samplePhases,
      ...props,
    },
  });
}

describe('Timeline', () => {
  it('renders the section title', () => {
    const wrapper = mountTimeline();

    expect(wrapper.text()).toContain('Cronograma del Proyecto');
  });

  it('renders the total duration', () => {
    const wrapper = mountTimeline({ totalDuration: '8 Semanas' });

    expect(wrapper.text()).toContain('8 Semanas');
  });

  it('renders all phase titles', () => {
    const wrapper = mountTimeline();

    expect(wrapper.text()).toContain('Discovery');
    expect(wrapper.text()).toContain('Desarrollo');
  });

  it('renders task items within each phase', () => {
    const wrapper = mountTimeline();

    expect(wrapper.text()).toContain('Reunión de kickoff');
    expect(wrapper.text()).toContain('Setup del servidor');
  });

  it('renders the milestone badge when phase.milestone is provided', () => {
    const wrapper = mountTimeline();

    expect(wrapper.text()).toContain('Aprobación de estrategia');
  });
});
