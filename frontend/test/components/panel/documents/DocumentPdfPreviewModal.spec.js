import { mount, flushPromises } from '@vue/test-utils';
import DocumentPdfPreviewModal from '~/components/panel/documents/DocumentPdfPreviewModal.vue';

const SAVED_COVERS = {
  include_portada: true,
  include_subportada: false,
  include_contraportada: true,
};

function mountModal(props = {}) {
  return mount(DocumentPdfPreviewModal, {
    props: {
      modelValue: true,
      documentId: 42,
      title: 'Alcance Fase 2',
      templateStyle: 'friendly',
      version: '2026-08-18T10:00:00Z',
      coverOptions: SAVED_COVERS,
      ...props,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size', 'fullHeight'],
          emits: ['update:modelValue'],
          template: '<div><slot /></div>',
        },
        BaseButton: {
          props: ['variant', 'iconOnly', 'size'],
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });
}

describe('DocumentPdfPreviewModal', () => {
  beforeEach(() => {
    global.fetch = jest.fn(() => Promise.resolve({ ok: true }));
  });

  it('shows the generated PDF inline, con el estilo y el sello de la versión', async () => {
    const wrapper = mountModal();
    await flushPromises();

    const src = wrapper.find('[data-testid="doc-pdf-preview-frame"]').attributes('src');
    expect(src).toContain('/api/documents/42/pdf/');
    expect(src).toContain('inline=1');
    expect(src).toContain('template=friendly');
    // Sin el sello, tras guardar el navegador devolvería el PDF cacheado.
    expect(src).toContain('v=2026-08-18T10%3A00%3A00Z');
  });

  it('describes the pages of the SAVED document, not the ones on screen', async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.find('[data-testid="doc-pdf-preview-pages"]').text())
      .toBe('El PDF incluye: portada · contenido · contraportada');
  });

  it('says it could not render instead of showing an empty viewer', async () => {
    global.fetch = jest.fn(() => Promise.resolve({ ok: false }));
    const wrapper = mountModal();
    await flushPromises();

    expect(wrapper.find('[data-testid="doc-pdf-preview-frame"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="doc-pdf-preview-error"]').text())
      .toContain('No pudimos mostrar el PDF');
  });

  it('re-generates on each opening: entre una y otra pudo cambiar lo guardado', async () => {
    const wrapper = mountModal({ modelValue: false });
    await flushPromises();
    expect(global.fetch).not.toHaveBeenCalled();

    await wrapper.setProps({ modelValue: true });
    await flushPromises();
    expect(global.fetch).toHaveBeenCalledTimes(1);

    await wrapper.setProps({ modelValue: false });
    await wrapper.setProps({ modelValue: true });
    await flushPromises();
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });
});
