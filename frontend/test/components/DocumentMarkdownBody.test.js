import { mount } from '@vue/test-utils';

jest.mock('dompurify', () => ({
  __esModule: true,
  default: { sanitize: jest.fn((html) => html) },
}));

import DocumentMarkdownBody from '../../components/panel/documents/DocumentMarkdownBody.vue';

describe('DocumentMarkdownBody theme', () => {
  it('defaults to the friendly look (no professional modifier)', () => {
    const w = mount(DocumentMarkdownBody, { props: { markdown: 'hola' } });
    expect(w.classes()).toContain('markdown-preview');
    expect(w.classes()).not.toContain('markdown-preview--professional');
  });

  it('adds the professional modifier when theme=professional', () => {
    const w = mount(DocumentMarkdownBody, {
      props: { markdown: 'hola', theme: 'professional' },
    });
    expect(w.classes()).toContain('markdown-preview--professional');
  });

  it('composes theme with the size variant', () => {
    const w = mount(DocumentMarkdownBody, {
      props: { markdown: 'hola', theme: 'professional', variant: 'full' },
    });
    expect(w.classes()).toContain('markdown-preview--professional');
    expect(w.classes()).toContain('markdown-preview--full');
  });
});
