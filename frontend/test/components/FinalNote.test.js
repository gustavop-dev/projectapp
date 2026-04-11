import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

import FinalNote from '../../components/BusinessProposal/FinalNote.vue';

function mountNote(props = {}) {
  return mount(FinalNote, { props });
}

describe('FinalNote', () => {
  it('renders the section title', () => {
    const wrapper = mountNote({ title: 'Cierre Final' });

    expect(wrapper.text()).toContain('Cierre Final');
  });

  it('renders the personalNote when provided', () => {
    const wrapper = mountNote({ personalNote: 'Fue un placer trabajar contigo.' });

    expect(wrapper.text()).toContain('Fue un placer trabajar contigo.');
  });

  it('hides the personalNote element when personalNote is empty', () => {
    const wrapper = mountNote({ personalNote: '' });

    expect(wrapper.find('p.italic').exists()).toBe(false);
  });

  it('renders commitment badges', () => {
    const badges = [
      { icon: '🤝', title: 'Compromiso', description: 'Total' },
      { icon: '💯', title: 'Calidad', description: 'Garantizada' },
    ];
    const wrapper = mountNote({ commitmentBadges: badges });

    expect(wrapper.findAll('.badge-card')).toHaveLength(2);
    expect(wrapper.text()).toContain('Compromiso');
  });

  it('renders kickoff plan steps when kickoffPlan is provided', () => {
    const kickoffPlan = [
      { day: 'D1', title: 'Kickoff', description: 'Reunión inicial' },
      { day: 'D2', title: 'Setup', description: 'Configuración del entorno' },
    ];
    const wrapper = mountNote({ kickoffPlan });

    expect(wrapper.text()).toContain('Kickoff');
    expect(wrapper.text()).toContain('Setup');
  });

  it('renders the kickoff section title in English when language is en', () => {
    const kickoffPlan = [{ day: 'D1', title: 'Start', description: 'Begin' }];
    const wrapper = mountNote({ kickoffPlan, language: 'en' });

    expect(wrapper.text()).toContain('Kickoff Plan');
  });
});
