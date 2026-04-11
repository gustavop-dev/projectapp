import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useLinkify', () => ({
  linkify: jest.fn((text) => text),
}));

import CreativeSupport from '../../components/BusinessProposal/CreativeSupport.vue';

function mountSection(content = {}) {
  return mount(CreativeSupport, {
    props: { content },
  });
}

describe('CreativeSupport', () => {
  it('renders the section title', () => {
    const wrapper = mountSection({ title: 'Soporte Creativo' });

    expect(wrapper.text()).toContain('Soporte Creativo');
  });

  it('renders paragraphs from content.paragraphs', () => {
    const wrapper = mountSection({
      paragraphs: ['Apoyo visual completo.', 'Diseño de marca alineado.'],
    });

    expect(wrapper.html()).toContain('Apoyo visual completo.');
  });

  it('renders the closing paragraph when content.closing is provided', () => {
    const wrapper = mountSection({ closing: 'Tu identidad visual, nuestra prioridad.' });

    expect(wrapper.text()).toContain('Tu identidad visual, nuestra prioridad.');
  });

  it('hides the closing block when content.closing is absent', () => {
    const wrapper = mountSection({ closing: '' });

    expect(wrapper.text()).not.toContain('Tu identidad');
  });

  it('renders include items from content.includes', () => {
    const wrapper = mountSection({
      includes: ['Diseño de logotipo', 'Paleta de colores'],
    });

    expect(wrapper.text()).toContain('Diseño de logotipo');
    expect(wrapper.text()).toContain('Paleta de colores');
  });
});
