import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import BaseAlert from '../../components/base/BaseAlert.vue';
import BaseBadge from '../../components/base/BaseBadge.vue';
import BaseFormField from '../../components/base/BaseFormField.vue';
import BaseSelect from '../../components/base/BaseSelect.vue';
import LinktreeTemplateEditor from '../../components/panel/linktrees/LinktreeTemplateEditor.vue';
import { useLinktreeTemplatesStore } from '../../stores/linktree-templates';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

const version = (overrides = {}) => ({
  id: 'version-one',
  name: 'Tarjeta principal',
  status: 'valid',
  active: false,
  created_at: '2026-09-23T10:00:00Z',
  preview_url: '/preview/version-one/',
  screenshots: {},
  issues: [],
  ...overrides,
});

const library = (versions = [version()]) => ({
  templates: [],
  versions,
  active_version_id: null,
  can_share: false,
  next_offset: null,
});

const editor = (props = {}) => mount(LinktreeTemplateEditor, {
  props: { treeId: 'tree-bravo', ...props },
  global: {
    components: { BaseAlert, BaseBadge, BaseFormField, BaseSelect },
    stubs: { NuxtLink: { template: '<a><slot /></a>', props: ['to'] } },
  },
});

describe('LinktreeTemplateEditor', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
  });

  it('shows a recoverable library error and retries the failed load', async () => {
    // Falla si una caída transitoria deja al administrador sin manera de recargar la biblioteca.
    get_request
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({ data: library() });

    const wrapper = editor();
    await flushPromises();

    expect(wrapper.get('[data-testid="template-request-error"]').text()).toBe('No se pudo cargar la biblioteca de plantillas.');
    await wrapper.get('button').trigger('click');
    await flushPromises();

    expect(get_request).toHaveBeenCalledTimes(2);
    expect(get_request).toHaveBeenLastCalledWith('linktrees/admin/tree-bravo/templates/?offset=0');
    wrapper.unmount();
  });

  it('disables validation actions for unsaved profiles and shows pending validation', async () => {
    // Falla si se puede validar o publicar una instantánea con cambios de perfil sin guardar.
    get_request.mockResolvedValueOnce({ data: library() });
    const wrapper = editor({ hasUnsavedChanges: true });
    await flushPromises();

    const fileInput = wrapper.get('[data-testid="template-file-input"]');
    const upload = new File(['<html></html>'], 'template.html', { type: 'text/html' });
    Object.defineProperty(fileInput.element, 'files', { configurable: true, value: [upload] });
    await fileInput.trigger('change');

    expect(wrapper.get('[data-testid="template-upload-validate"]').attributes('disabled')).toBe('');
    expect(wrapper.get('[data-testid="template-publish"]').attributes('disabled')).toBe('');
    expect(wrapper.get('[data-testid="template-revalidate"]').attributes('disabled')).toBe('');

    await wrapper.setProps({ hasUnsavedChanges: false });
    useLinktreeTemplatesStore().versions = [version({ status: 'pending' })];
    await flushPromises();

    expect(wrapper.get('[data-testid="template-validating"]').text()).toBe('Comprobando contraste, enlaces y movimiento en 320, 375 y 430 px… Puedes continuar trabajando mientras termina.');
    expect(wrapper.get('[data-testid="template-publish"]').attributes('disabled')).toBe('');
    wrapper.unmount();
  });

  it('renders the sandboxed preview, each validated capture, and the version history', async () => {
    // Falla si el panel deja que la vista previa ejecute código o pierde capturas validadas del historial.
    get_request.mockResolvedValueOnce({ data: library([version({
      screenshots: {
        320: '/captures/320.png',
        375: '/captures/375.png',
        430: '/captures/430.png',
      },
    })]) });
    const wrapper = editor();
    await flushPromises();

    expect(wrapper.get('[data-testid="template-sandbox-preview"]').attributes('sandbox')).toBe('');
    expect(wrapper.get('[data-testid="template-screenshots"]').findAll('img').map((image) => image.attributes('alt'))).toEqual([
      'Captura validada a 320 px',
      'Captura validada a 375 px',
      'Captura validada a 430 px',
    ]);
    expect(wrapper.get('[data-testid="template-version-select"]').element.value).toBe('version-one');
    wrapper.unmount();
  });
});
