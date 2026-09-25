import { flushPromises, mount } from '@vue/test-utils';
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue';

async function mountExportMarkdown(markdown) {
  const wrapper = mount(DocumentMarkdownBody, {
    props: { markdown, standardMarkdown: true },
  });
  await flushPromises();
  return wrapper;
}

describe('DocumentMarkdownBody standard Markdown export', () => {
  it('renders a table cell with escaped Markdown punctuation', async () => {
    // Falla si la vista previa de Office divide un pipe escapado o interpreta asteriscos literales.
    const wrapper = await mountExportMarkdown([
      '| Campo | Valor |',
      '| --- | --- |',
      '| Nota | \\*literal\\* y A\\|B |',
    ].join('\n'));

    expect(wrapper.findAll('table')).toHaveLength(1);
    expect(wrapper.findAll('td')).toHaveLength(2);
    expect(wrapper.findAll('td')[1].text()).toBe('*literal* y A|B');
  });

  it('sanitizes malicious inline HTML in exported Markdown', async () => {
    // Falla si contenido adjunto no confiable conserva HTML ejecutable en la vista previa.
    const wrapper = await mountExportMarkdown('Antes <span onclick="alert(1)">contenido visible</span> después');

    expect(wrapper.text()).toContain('contenido visible');
    expect(wrapper.html()).not.toContain('onclick');
  });
});
