jest.mock('~/stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

import { flushPromises, mount } from '@vue/test-utils';
import { get_request } from '~/stores/services/request_http';
import { usePanelNotify } from '~/composables/usePanelNotify';
import ProposalDocumentCopyButton from '~/components/BusinessProposal/admin/ProposalDocumentCopyButton.vue';

const MARKDOWN = '# Contrato de desarrollo\n\nEl alcance incluye la fase de descubrimiento.';
const endpoint = 'proposals/42/contract/markdown/';
const wrappers = [];
let originalClipboard;

function mountCopyButton(props = {}) {
  const wrapper = mount(ProposalDocumentCopyButton, {
    props: {
      endpoint,
      title: 'Contrato de desarrollo',
      ...props,
    },
  });
  wrappers.push(wrapper);
  return wrapper;
}

describe('ProposalDocumentCopyButton', () => {
  beforeEach(() => {
    originalClipboard = navigator.clipboard;
    get_request.mockReset();
    usePanelNotify().clearAll();
  });

  afterEach(() => {
    wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: originalClipboard,
    });
    usePanelNotify().clearAll();
  });

  it('confirms copying returned Markdown after the clipboard resolves', async () => {
    // Falla si el control confirma antes de que el navegador acepte el contenido del contrato.
    let resolveClipboard;
    const writeText = jest.fn(() => new Promise((resolve) => { resolveClipboard = resolve; }));
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    get_request.mockResolvedValue({ data: { markdown: MARKDOWN } });
    const wrapper = mountCopyButton();

    await wrapper.get('button').trigger('click');
    await flushPromises();

    expect(get_request).toHaveBeenCalledTimes(1);
    expect(get_request).toHaveBeenCalledWith(endpoint, expect.objectContaining({ signal: expect.any(AbortSignal) }));
    expect(writeText).toHaveBeenCalledWith(MARKDOWN);
    expect(wrapper.get('button').attributes('aria-label')).toBe('Copiando…');

    resolveClipboard();
    await flushPromises();

    expect(wrapper.get('button').attributes('data-displayed-action')).toBe('complete');
    expect(wrapper.get('[role="status"]').text()).toBe('Copiado');
  });

  test.each([
    {
      scenario: 'the API returns blank Markdown',
      configureRequest: () => get_request.mockResolvedValue({ data: { markdown: '   ' } }),
      clipboard: jest.fn().mockResolvedValue(undefined),
      notification: 'El documento no contiene texto para copiar.',
      writes: 0,
    },
    {
      scenario: 'the document API returns an error',
      configureRequest: () => get_request.mockRejectedValue({
        response: { data: { error: 'El documento ya no está disponible.' } },
      }),
      clipboard: jest.fn().mockResolvedValue(undefined),
      notification: 'El documento ya no está disponible.',
      writes: 0,
    },
    {
      scenario: 'the network connection fails',
      configureRequest: () => get_request.mockRejectedValue(new Error('Network Error')),
      clipboard: jest.fn().mockResolvedValue(undefined),
      notification: 'No se pudo obtener el documento. Vuelve a intentarlo.',
      writes: 0,
    },
    {
      scenario: 'clipboard permission is rejected',
      configureRequest: () => get_request.mockResolvedValue({ data: { markdown: MARKDOWN } }),
      clipboard: jest.fn().mockRejectedValue(new Error('Permission denied')),
      notification: 'No se pudo copiar. Revisa el permiso del portapapeles y vuelve a intentarlo.',
      writes: 1,
    },
  ])('keeps the control reusable when $scenario', async ({ configureRequest, clipboard, notification, writes }) => {
    // Falla si un error de exportación deja el botón bloqueado o muestra un éxito falso.
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: clipboard },
    });
    configureRequest();
    const wrapper = mountCopyButton();

    await wrapper.get('button').trigger('click');
    await flushPromises();

    expect(clipboard).toHaveBeenCalledTimes(writes);
    expect(wrapper.get('button').element.disabled).toBe(false);
    expect(usePanelNotify().notifications.value.at(-1).title).toBe(notification);
  });
});
