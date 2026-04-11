import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('../../composables/useLinkify', () => ({
  linkify: jest.fn((text) => text),
}));

import ConversionStrategy from '../../components/BusinessProposal/ConversionStrategy.vue';

function mountSection(content = {}) {
  return mount(ConversionStrategy, {
    props: { content },
  });
}

describe('ConversionStrategy', () => {
  it('renders the section title', () => {
    const wrapper = mountSection({ title: 'Estrategia de Conversión' });

    expect(wrapper.text()).toContain('Estrategia de Conversión');
  });

  it('renders the intro text', () => {
    const wrapper = mountSection({ intro: 'Nuestro enfoque maximiza conversiones.' });

    expect(wrapper.html()).toContain('Nuestro enfoque maximiza conversiones.');
  });

  it('renders step cards from content.steps', () => {
    const wrapper = mountSection({
      steps: [
        { title: 'Paso 1', bullets: ['Bullet A', 'Bullet B'] },
        { title: 'Paso 2', bullets: ['Bullet C'] },
      ],
    });

    expect(wrapper.text()).toContain('Paso 1');
    expect(wrapper.text()).toContain('Paso 2');
    expect(wrapper.text()).toContain('Bullet A');
  });

  it('renders the result block when content.result is provided', () => {
    const wrapper = mountSection({ result: 'Incremento del 30% en leads.' });

    expect(wrapper.text()).toContain('Incremento del 30% en leads.');
  });

  it('hides the result block when content.result is absent', () => {
    const wrapper = mountSection({ result: '' });

    expect(wrapper.text()).not.toContain('Incremento');
  });
});
