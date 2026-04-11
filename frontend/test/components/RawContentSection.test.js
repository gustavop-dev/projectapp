import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSectionAnimations', () => ({
  useSectionAnimations: jest.fn(),
}));

jest.mock('marked', () => ({
  marked: { parse: jest.fn((text) => `<p>${text}</p>`) },
}));

jest.mock('dompurify', () => ({
  __esModule: true,
  default: { sanitize: jest.fn((html) => html) },
}));

import RawContentSection from '../../components/BusinessProposal/RawContentSection.vue';

function mountSection(props = {}) {
  return mount(RawContentSection, {
    props: { title: '', index: '', rawText: '', ...props },
  });
}

describe('RawContentSection', () => {
  it('renders the section title', () => {
    const wrapper = mountSection({ title: 'Arquitectura técnica' });

    expect(wrapper.text()).toContain('Arquitectura técnica');
  });

  it('renders the index when provided', () => {
    const wrapper = mountSection({ title: 'Tech', index: '5' });

    expect(wrapper.find('[data-testid="raw-content-index"]').text()).toBe('5');
  });

  it('does not render the index element when index is empty', () => {
    const wrapper = mountSection({ title: 'Tech', index: '' });

    expect(wrapper.find('[data-testid="raw-content-index"]').exists()).toBe(false);
  });

  it('renders converted markdown content in the card', () => {
    const wrapper = mountSection({ rawText: 'Hola mundo' });

    expect(wrapper.find('[data-testid="raw-content-card"]').html()).toContain('Hola mundo');
  });
});
