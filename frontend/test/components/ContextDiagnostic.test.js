import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useLinkify', () => ({
  linkify: jest.fn((text) => text),
}));

import ContextDiagnostic from '../../components/BusinessProposal/ContextDiagnostic.vue';

function mountSection(content = {}) {
  return mount(ContextDiagnostic, {
    props: { content },
  });
}

describe('ContextDiagnostic', () => {
  it('renders the section title', () => {
    const wrapper = mountSection({ title: 'Diagnóstico Inicial' });

    expect(wrapper.text()).toContain('Diagnóstico Inicial');
  });

  it('renders paragraphs from content.paragraphs', () => {
    const wrapper = mountSection({
      paragraphs: ['Primer párrafo de contexto.', 'Segundo párrafo.'],
    });

    expect(wrapper.html()).toContain('Primer párrafo de contexto.');
  });

  it('renders the opportunity block when content.opportunity is provided', () => {
    const wrapper = mountSection({ opportunity: 'Gran oportunidad de mercado.' });

    expect(wrapper.text()).toContain('Gran oportunidad de mercado.');
  });

  it('hides the opportunity block when content.opportunity is absent', () => {
    const wrapper = mountSection({ opportunity: '' });

    expect(wrapper.text()).not.toContain('Gran oportunidad');
  });

  it('renders issue items when content.issues is provided', () => {
    const wrapper = mountSection({
      issues: ['Problema de rendimiento', 'Falta de escalabilidad'],
    });

    expect(wrapper.text()).toContain('Problema de rendimiento');
    expect(wrapper.text()).toContain('Falta de escalabilidad');
  });
});
