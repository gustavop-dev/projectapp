import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useLinkify', () => ({
  linkify: jest.fn((text) => text),
}));

import DesignUX from '../../components/BusinessProposal/DesignUX.vue';

function mountSection(content = {}) {
  return mount(DesignUX, {
    props: { content },
  });
}

describe('DesignUX', () => {
  it('renders the section title', () => {
    const wrapper = mountSection({ title: 'Diseño UX/UI' });

    expect(wrapper.text()).toContain('Diseño UX/UI');
  });

  it('renders paragraphs from content.paragraphs', () => {
    const wrapper = mountSection({
      paragraphs: ['Experiencia de usuario centrada.', 'Interfaces limpias e intuitivas.'],
    });

    expect(wrapper.html()).toContain('Experiencia de usuario centrada.');
  });

  it('renders the objective block when content.objective is provided', () => {
    const wrapper = mountSection({ objective: 'Reducir la fricción del usuario.' });

    expect(wrapper.text()).toContain('Reducir la fricción del usuario.');
  });

  it('hides the objective block when content.objective is absent', () => {
    const wrapper = mountSection({ objective: '' });

    expect(wrapper.text()).not.toContain('Reducir la fricción');
  });

  it('renders focus items from content.focusItems', () => {
    const wrapper = mountSection({
      focusItems: ['Accesibilidad WCAG', 'Mobile-first design'],
    });

    expect(wrapper.text()).toContain('Accesibilidad WCAG');
    expect(wrapper.text()).toContain('Mobile-first design');
  });
});
