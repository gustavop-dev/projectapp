import { flushPromises, mount } from '@vue/test-utils';

import PdfPreviewPane from '../../components/base/PdfPreviewPane.vue';

function mountPane(props = {}) {
  return mount(PdfPreviewPane, {
    props: {
      src: '/api/documents/1/pdf/?inline=1',
      testIdPrefix: 'document-pdf',
      ...props,
    },
  });
}

describe('PdfPreviewPane', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders the PDF after a successful probe', async () => {
    global.fetch.mockResolvedValue({ ok: true });

    const wrapper = mountPane();
    await flushPromises();

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/documents/1/pdf/?inline=1',
      { credentials: 'same-origin' },
    );
    expect(wrapper.get('[data-testid="document-pdf-frame"]').attributes('src'))
      .toBe('/api/documents/1/pdf/?inline=1');
  });

  it('explains an unavailable PDF', async () => {
    global.fetch.mockResolvedValue({ ok: false });

    const wrapper = mountPane({ errorMessage: 'Todavía no existe un PDF.' });
    await flushPromises();

    expect(wrapper.get('[data-testid="document-pdf-error"]').text())
      .toContain('Todavía no existe un PDF.');
  });

  it('reports a failed PDF request', async () => {
    global.fetch.mockRejectedValue(new Error('offline'));

    const wrapper = mountPane();
    await flushPromises();

    expect(wrapper.get('[data-testid="document-pdf-error"]').exists()).toBe(true);
  });

  it('ignores a stale probe after the source changes', async () => {
    let resolveFirst;
    global.fetch
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
      .mockResolvedValueOnce({ ok: false });
    const wrapper = mountPane();

    await wrapper.setProps({ src: '/api/documents/2/pdf/?inline=1' });
    await flushPromises();
    resolveFirst({ ok: true });
    await flushPromises();

    expect(wrapper.get('[data-testid="document-pdf-error"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="document-pdf-frame"]').exists()).toBe(false);
  });
});
