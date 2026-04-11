import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useLinkify', () => ({
  linkify: jest.fn((text) => text),
}));

import ExecutiveSummary from '../../components/BusinessProposal/ExecutiveSummary.vue';

function mountSummary(content = {}) {
  return mount(ExecutiveSummary, { props: { content } });
}

describe('ExecutiveSummary', () => {
  it('renders the section title', () => {
    const wrapper = mountSummary({ title: 'Resumen Ejecutivo' });

    expect(wrapper.text()).toContain('Resumen Ejecutivo');
  });

  it('renders paragraphs from content.paragraphs', () => {
    const wrapper = mountSummary({
      paragraphs: ['Primera descripción del proyecto.', 'Segunda descripción.'],
    });

    expect(wrapper.html()).toContain('Primera descripción del proyecto.');
  });

  it('renders the highlights aside when content.highlights has items', () => {
    const wrapper = mountSummary({
      highlights: ['Característica clave 1', 'Característica clave 2'],
      highlightsTitle: 'Incluye',
    });

    expect(wrapper.text()).toContain('Incluye');
    expect(wrapper.text()).toContain('Característica clave 1');
  });

  it('hides the highlights aside when content.highlights is empty', () => {
    const wrapper = mountSummary({ highlights: [] });

    expect(wrapper.find('aside').exists()).toBe(false);
  });

  it('renders the section index', () => {
    const wrapper = mountSummary({ index: '01' });

    expect(wrapper.text()).toContain('01');
  });
});
