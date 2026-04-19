import { mount, flushPromises } from '@vue/test-utils';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

import ProposalDiagnosticTemplatesSection from '../../components/BusinessProposal/admin/ProposalDiagnosticTemplatesSection.vue';

const TEMPLATES_LIST = [
  { slug: 'diagnostico-aplicacion', title: 'Diagnóstico de Aplicación', filename: 'diagnostico_aplicacion_es.md', size_bytes: 4096, updated_at: '2026-04-01T10:00:00Z' },
  { slug: 'diagnostico-tecnico', title: 'Diagnóstico Técnico', filename: 'diagnostico_tecnico_es.md', size_bytes: 5120, updated_at: '2026-04-01T10:00:00Z' },
  { slug: 'anexo', title: 'Anexo — Dimensionamiento', filename: 'anexo_es.md', size_bytes: 3072, updated_at: '2026-04-01T10:00:00Z' },
];

function getMock() {
  return jest.requireMock('../../stores/services/request_http').get_request;
}

function mountSection() {
  return mount(ProposalDiagnosticTemplatesSection);
}

describe('ProposalDiagnosticTemplatesSection', () => {
  beforeEach(() => {
    getMock().mockReset();
  });

  it('shows loading indicator while templates are being fetched', () => {
    getMock().mockReturnValue(new Promise(() => {}));

    const wrapper = mountSection();

    expect(wrapper.text()).toContain('Cargando plantillas');
  });

  it('renders 3 list items after successful API response', async () => {
    getMock().mockResolvedValue({ data: TEMPLATES_LIST });

    const wrapper = mountSection();
    await flushPromises();

    expect(wrapper.findAll('li')).toHaveLength(3);
  });

  it('renders each template title', async () => {
    getMock().mockResolvedValue({ data: TEMPLATES_LIST });

    const wrapper = mountSection();
    await flushPromises();

    expect(wrapper.text()).toContain('Diagnóstico de Aplicación');
    expect(wrapper.text()).toContain('Diagnóstico Técnico');
    expect(wrapper.text()).toContain('Anexo — Dimensionamiento');
  });

  it('shows error message when API call fails', async () => {
    getMock().mockRejectedValue(new Error('Network error'));

    const wrapper = mountSection();
    await flushPromises();

    expect(wrapper.text()).toContain('No se pudieron cargar las plantillas');
  });

  it('calls clipboard with markdown content when copy button clicked', async () => {
    const markdown = '# Diagnóstico de Aplicación\n\nContenido.';
    getMock()
      .mockResolvedValueOnce({ data: TEMPLATES_LIST })
      .mockResolvedValueOnce({ data: { content_markdown: markdown } });

    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });

    const wrapper = mountSection();
    await flushPromises();

    const copyBtn = wrapper.findAll('button').find((b) => b.text() === 'Copiar contenido');
    await copyBtn.trigger('click');
    await flushPromises();

    expect(writeText).toHaveBeenCalledWith(markdown);
  });

  it('shows "¡Copiado!" feedback after copying', async () => {
    jest.useFakeTimers();
    const markdown = '# Contenido';
    getMock()
      .mockResolvedValueOnce({ data: TEMPLATES_LIST })
      .mockResolvedValueOnce({ data: { content_markdown: markdown } });

    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
      configurable: true,
    });

    const wrapper = mountSection();
    await flushPromises();

    const copyBtn = wrapper.findAll('button').find((b) => b.text() === 'Copiar contenido');
    await copyBtn.trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('¡Copiado!');

    jest.useRealTimers();
  });

  it('does not refetch content on second copy of the same template', async () => {
    const markdown = '# Contenido cacheado';
    getMock()
      .mockResolvedValueOnce({ data: TEMPLATES_LIST })
      .mockResolvedValueOnce({ data: { content_markdown: markdown } });

    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
      configurable: true,
    });

    const wrapper = mountSection();
    await flushPromises();

    const copyBtn = wrapper.findAll('button').find((b) => b.text() === 'Copiar contenido');
    await copyBtn.trigger('click');
    await flushPromises();
    await copyBtn.trigger('click');
    await flushPromises();

    // list fetch + one detail fetch (cached on second copy)
    expect(getMock()).toHaveBeenCalledTimes(2);
  });

  it('expands preview block when Vista previa clicked', async () => {
    const markdown = '# Vista previa del contenido';
    getMock()
      .mockResolvedValueOnce({ data: TEMPLATES_LIST })
      .mockResolvedValueOnce({ data: { content_markdown: markdown } });

    const wrapper = mountSection();
    await flushPromises();

    expect(wrapper.find('pre').exists()).toBe(false);

    const previewBtn = wrapper.findAll('button').find((b) => b.text() === 'Vista previa');
    await previewBtn.trigger('click');
    await flushPromises();

    expect(wrapper.find('pre').exists()).toBe(true);
    expect(wrapper.find('pre').text()).toContain('Vista previa del contenido');
  });

  it('collapses preview block when Ocultar clicked', async () => {
    const markdown = '# Contenido';
    getMock()
      .mockResolvedValueOnce({ data: TEMPLATES_LIST })
      .mockResolvedValueOnce({ data: { content_markdown: markdown } });

    const wrapper = mountSection();
    await flushPromises();

    const previewBtn = wrapper.findAll('button').find((b) => b.text() === 'Vista previa');
    await previewBtn.trigger('click');
    await flushPromises();

    const hideBtn = wrapper.findAll('button').find((b) => b.text() === 'Ocultar');
    await hideBtn.trigger('click');

    expect(wrapper.find('pre').exists()).toBe(false);
  });
});
