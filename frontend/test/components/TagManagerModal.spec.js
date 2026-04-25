/**
 * Tests for TagManagerModal.vue.
 *
 * Covers: visibility, fetchTags on open, tag list render, create/rename/delete
 * flows, error display, close emit.
 */

const mockTagStore = {
  tags: [],
  isUpdating: false,
  fetchTags: jest.fn(),
  createTag: jest.fn(),
  updateTag: jest.fn(),
  deleteTag: jest.fn(),
};

// Nuxt auto-import — must be set before the component is required
global.useDocumentTagStore = jest.fn(() => mockTagStore);

import { mount } from '@vue/test-utils';
import TagManagerModal from '../../components/panel/documents/TagManagerModal.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const baseTag = { id: 1, name: 'Diseño', color: 'blue' };

function mountModal(props = {}) {
  return mount(TagManagerModal, {
    props: { modelValue: true, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('TagManagerModal', () => {
  beforeEach(() => {
    mockTagStore.tags = [];
    mockTagStore.isUpdating = false;
    mockTagStore.fetchTags.mockReset().mockResolvedValue({ success: true });
    mockTagStore.createTag.mockReset().mockResolvedValue({ success: true });
    mockTagStore.updateTag.mockReset().mockResolvedValue({ success: true });
    mockTagStore.deleteTag.mockReset().mockResolvedValue({ success: true });
    window.confirm = jest.fn(() => true);
  });

  // ── Visibility ────────────────────────────────────────────────────────────

  describe('visibility', () => {
    it('renders modal content when modelValue is true', () => {
      const wrapper = mountModal({ modelValue: true });

      expect(wrapper.text()).toContain('Gestionar etiquetas');
    });

    it('does not render modal content when modelValue is false', () => {
      const wrapper = mountModal({ modelValue: false });

      expect(wrapper.text()).not.toContain('Gestionar etiquetas');
    });
  });

  // ── Fetch on open ─────────────────────────────────────────────────────────

  describe('data loading', () => {
    it('calls fetchTags when modelValue transitions to true', async () => {
      const wrapper = mountModal({ modelValue: false });
      await wrapper.setProps({ modelValue: true });
      await flushPromises();

      expect(mockTagStore.fetchTags).toHaveBeenCalled();
    });

    it('shows empty state when no tags exist', () => {
      mockTagStore.tags = [];
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('No hay etiquetas todavía');
    });

    it('renders the existing tag list', () => {
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Diseño');
    });
  });

  // ── Create ────────────────────────────────────────────────────────────────

  describe('create tag', () => {
    it('calls createTag when the form is submitted with a name', async () => {
      const wrapper = mountModal();
      await wrapper.find('input[type="text"]').setValue('Nueva etiqueta');
      await wrapper.find('form').trigger('submit.prevent');
      await flushPromises();

      expect(mockTagStore.createTag).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Nueva etiqueta' })
      );
    });

    it('does not call createTag when the name input is empty', async () => {
      const wrapper = mountModal();
      await wrapper.find('input[type="text"]').setValue('');
      await wrapper.find('form').trigger('submit.prevent');

      expect(mockTagStore.createTag).not.toHaveBeenCalled();
    });

    it('emits changed after a tag is successfully created', async () => {
      const wrapper = mountModal();
      await wrapper.find('input[type="text"]').setValue('Nueva etiqueta');
      await wrapper.find('form').trigger('submit.prevent');
      await flushPromises();

      expect(wrapper.emitted('changed')).toBeTruthy();
    });

    it('shows a formatted error when createTag fails', async () => {
      mockTagStore.createTag.mockResolvedValueOnce({
        success: false,
        errors: { name: ['Ya existe una etiqueta con ese nombre.'] },
      });
      const wrapper = mountModal();
      await wrapper.find('input[type="text"]').setValue('Duplicada');
      await wrapper.find('form').trigger('submit.prevent');
      await flushPromises();

      expect(wrapper.text()).toContain('Ya existe una etiqueta con ese nombre.');
    });
  });

  // ── Rename ────────────────────────────────────────────────────────────────

  describe('rename tag', () => {
    it('enters rename mode when the Editar button is clicked', async () => {
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();
      const editBtn = wrapper.findAll('button').find(b => b.text() === 'Editar');
      await editBtn.trigger('click');

      const input = wrapper.find('li input[type="text"]');
      expect(input.exists()).toBe(true);
      expect(input.element.value).toBe('Diseño');
    });

    it('calls updateTag when the Guardar button is clicked', async () => {
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();
      const editBtn = wrapper.findAll('button').find(b => b.text() === 'Editar');
      await editBtn.trigger('click');

      await wrapper.find('li input[type="text"]').setValue('Diseño v2');
      const saveBtn = wrapper.findAll('button').find(b => b.text() === 'Guardar');
      await saveBtn.trigger('click');
      await flushPromises();

      expect(mockTagStore.updateTag).toHaveBeenCalledWith(
        baseTag.id,
        expect.objectContaining({ name: 'Diseño v2' })
      );
    });

    it('emits changed after a tag is successfully renamed', async () => {
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();
      const editBtn = wrapper.findAll('button').find(b => b.text() === 'Editar');
      await editBtn.trigger('click');

      await wrapper.find('li input[type="text"]').setValue('Diseño v2');
      const saveBtn = wrapper.findAll('button').find(b => b.text() === 'Guardar');
      await saveBtn.trigger('click');
      await flushPromises();

      expect(wrapper.emitted('changed')).toBeTruthy();
    });
  });

  // ── Delete ────────────────────────────────────────────────────────────────

  describe('delete tag', () => {
    it('calls deleteTag when window.confirm is accepted', async () => {
      window.confirm = jest.fn(() => true);
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();
      const deleteBtn = wrapper.findAll('button').find(b => b.text() === 'Eliminar');
      await deleteBtn.trigger('click');
      await flushPromises();

      expect(mockTagStore.deleteTag).toHaveBeenCalledWith(baseTag.id);
    });

    it('does not call deleteTag when window.confirm is cancelled', async () => {
      window.confirm = jest.fn(() => false);
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();
      const deleteBtn = wrapper.findAll('button').find(b => b.text() === 'Eliminar');
      await deleteBtn.trigger('click');

      expect(mockTagStore.deleteTag).not.toHaveBeenCalled();
    });

    it('emits changed after a tag is successfully deleted', async () => {
      window.confirm = jest.fn(() => true);
      mockTagStore.tags = [baseTag];
      const wrapper = mountModal();
      const deleteBtn = wrapper.findAll('button').find(b => b.text() === 'Eliminar');
      await deleteBtn.trigger('click');
      await flushPromises();

      expect(wrapper.emitted('changed')).toBeTruthy();
    });
  });

  // ── Close ─────────────────────────────────────────────────────────────────

  describe('close', () => {
    it('emits update:modelValue false when the close button is clicked', async () => {
      const wrapper = mountModal();
      await wrapper.findAll('button').find(b => b.text() === 'Cerrar').trigger('click');

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });
  });
});
