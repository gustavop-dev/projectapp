import { mount, flushPromises } from '@vue/test-utils';

jest.mock('axios', () => ({ post: jest.fn() }));
jest.mock('../../stores/services/request_http', () => ({
  getCookie: jest.fn(() => 'test-csrf-token'),
}));

import MarkdownAttachmentModal from '../../components/MarkdownAttachmentModal.vue';

function getAxiosMock() {
  return jest.requireMock('axios').post;
}

function mountModal(props = {}) {
  return mount(MarkdownAttachmentModal, {
    props: { open: true, endpoint: 'proposals/42/proposal-email/markdown-attachment/', ...props },
    global: { stubs: { Teleport: true } },
  });
}

describe('MarkdownAttachmentModal', () => {
  beforeEach(() => {
    getAxiosMock().mockReset();
    URL.createObjectURL = jest.fn(() => 'blob:http://localhost/fake-id');
    URL.revokeObjectURL = jest.fn();
  });

  it('does not render modal content when open is false', () => {
    const wrapper = mount(MarkdownAttachmentModal, {
      props: { open: false, endpoint: 'proposals/42/proposal-email/markdown-attachment/' },
      global: { stubs: { Teleport: true } },
    });

    expect(wrapper.find('h2').exists()).toBe(false);
  });

  it('renders modal content when open is true', () => {
    const wrapper = mountModal();

    expect(wrapper.find('h2').text()).toContain('Adjuntar documento PDF');
  });

  it('preview button is disabled when title is empty', async () => {
    const wrapper = mountModal();
    await wrapper.find('textarea').setValue('# Contenido de prueba');

    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Vista previa'));

    expect(previewBtn.element.disabled).toBe(true);
  });

  it('preview button is disabled when markdown content is empty', async () => {
    const wrapper = mountModal();
    await wrapper.find('input[type="text"]').setValue('Título del documento');

    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Vista previa'));

    expect(previewBtn.element.disabled).toBe(true);
  });

  it('preview button is enabled when both title and markdown are filled', async () => {
    const wrapper = mountModal();
    await wrapper.find('input[type="text"]').setValue('Mi documento');
    await wrapper.find('textarea').setValue('# Encabezado\n\nTexto de contenido.');

    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Vista previa'));

    expect(previewBtn.element.disabled).toBe(false);
  });

  it('all three cover checkboxes are checked by default', () => {
    const wrapper = mountModal();
    const checkboxes = wrapper.findAll('input[type="checkbox"]');

    expect(checkboxes).toHaveLength(3);
    checkboxes.forEach((cb) => {
      expect(cb.element.checked).toBe(true);
    });
  });

  it('emits close when Cancelar button is clicked', async () => {
    const wrapper = mountModal();

    await wrapper.findAll('button').find((b) => b.text() === 'Cancelar').trigger('click');

    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits close when backdrop overlay is clicked', async () => {
    const wrapper = mountModal();

    await wrapper.find('.fixed.inset-0').trigger('click');

    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('renders iframe preview after successful preview generation', async () => {
    const pdfBlob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
    getAxiosMock().mockResolvedValue({ data: pdfBlob });

    const wrapper = mountModal();
    await wrapper.find('input[type="text"]').setValue('Informe técnico');
    await wrapper.find('textarea').setValue('# Contenido\n\nPárrafo.');

    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Vista previa'));
    await previewBtn.trigger('click');
    await flushPromises();

    expect(wrapper.find('iframe').exists()).toBe(true);
  });

  it('emits attach with a File and closes when Adjuntar clicked after preview', async () => {
    const pdfBlob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
    getAxiosMock().mockResolvedValue({ data: pdfBlob });

    global.fetch = jest.fn().mockResolvedValue({ blob: () => Promise.resolve(pdfBlob) });

    const wrapper = mountModal();
    await wrapper.find('input[type="text"]').setValue('Mi reporte');
    await wrapper.find('textarea').setValue('# Encabezado\n\nContenido.');

    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Vista previa'));
    await previewBtn.trigger('click');
    await flushPromises();

    const attachBtn = wrapper.findAll('button').find((b) => b.text().includes('Adjuntar'));
    await attachBtn.trigger('click');
    await flushPromises();

    expect(wrapper.emitted('attach')).toBeTruthy();
    expect(wrapper.emitted('attach')[0][0]).toBeInstanceOf(File);
    expect(wrapper.emitted('attach')[0][0].name).toBe('mi-reporte.pdf');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('resets title and markdown when modal is closed', async () => {
    const wrapper = mountModal();
    await wrapper.find('input[type="text"]').setValue('Borrador');
    await wrapper.find('textarea').setValue('# Borrador');

    await wrapper.setProps({ open: false });
    await flushPromises();
    await wrapper.setProps({ open: true });

    expect(wrapper.find('input[type="text"]').element.value).toBe('');
    expect(wrapper.find('textarea').element.value).toBe('');
  });
});
