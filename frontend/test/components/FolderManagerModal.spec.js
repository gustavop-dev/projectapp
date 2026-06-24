/**
 * Tests for FolderManagerModal.vue.
 *
 * Covers: rendering, empty state, folder list, create flow,
 * rename flow (start/cancel/commit/Esc), delete flow (ask/confirm/cancel),
 * close, modelValue watcher, handleReorder success and failure.
 */

const mockFolderStore = {
  folders: [],
  isUpdating: false,
  fetchFolders: jest.fn(),
  createFolder: jest.fn(),
  updateFolder: jest.fn(),
  deleteFolder: jest.fn(),
  reorderFolders: jest.fn(),
  // Getters de jerarquía, espejo de los del store real document_folders.js.
  get rootFolders() {
    return mockFolderStore.folders.filter((f) => f.parent == null);
  },
  childrenOf: (id) => mockFolderStore.folders.filter((f) => f.parent === id),
  descendantIdsOf: (id) => {
    const result = new Set();
    const pending = mockFolderStore.folders
      .filter((f) => f.parent === id)
      .map((f) => f.id);
    while (pending.length) {
      const current = pending.pop();
      if (result.has(current)) continue;
      result.add(current);
      mockFolderStore.folders
        .filter((f) => f.parent === current)
        .forEach((f) => pending.push(f.id));
    }
    return result;
  },
};

// Nuxt auto-import — must be set before the component is required
global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

import { mount } from '@vue/test-utils';
import FolderManagerModal from '../../components/panel/documents/FolderManagerModal.vue';
import FolderManagerTree from '../../components/panel/documents/FolderManagerTree.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const DraggableStub = {
  name: 'Draggable',
  props: ['modelValue', 'itemKey', 'handle', 'ghostClass', 'chosenClass', 'dragClass'],
  emits: ['update:modelValue', 'end'],
  template: '<div data-testid="folder-draggable"><slot name="item" v-for="(el, i) in modelValue" :key="i" :element="el" /></div>',
};

const baseFolder = { id: 1, name: 'Design', parent: null, document_count: 3 };
const emptyFolder = { id: 9, name: 'Empty', parent: null, document_count: 0 };

function mountModal(props = {}) {
  return mount(FolderManagerModal, {
    props: { modelValue: true, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        draggable: DraggableStub,
      },
    },
  });
}

describe('FolderManagerModal', () => {
  beforeEach(() => {
    mockFolderStore.folders = [];
    mockFolderStore.isUpdating = false;
    mockFolderStore.fetchFolders.mockReset().mockResolvedValue({ success: true });
    mockFolderStore.createFolder.mockReset().mockResolvedValue({ success: true });
    mockFolderStore.updateFolder.mockReset().mockResolvedValue({ success: true });
    mockFolderStore.deleteFolder.mockReset().mockResolvedValue({ success: true });
    mockFolderStore.reorderFolders.mockReset().mockResolvedValue({ success: true });
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  describe('rendering', () => {
    it('renders the modal heading when modelValue is true', () => {
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Gestionar carpetas');
    });

    it('does not render modal content when modelValue is false', () => {
      const wrapper = mountModal({ modelValue: false });

      expect(wrapper.text()).not.toContain('Gestionar carpetas');
    });

    it('shows the empty state when no folders exist', () => {
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Sin carpetas todavía');
    });

    it('renders the folder name when folders are in the store', () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Design');
    });

    it('shows the document count badge for each folder', () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('3');
    });
  });

  // ── handleCreate ──────────────────────────────────────────────────────────

  describe('handleCreate', () => {
    it('calls createFolder with the trimmed name when the form is submitted', async () => {
      const wrapper = mountModal();
      await wrapper.find('input[placeholder]').setValue('  My Folder  ');
      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(mockFolderStore.createFolder).toHaveBeenCalledWith({ name: 'My Folder', parent: null });
    });

    it('disables the Crear button when the input is empty', () => {
      const wrapper = mountModal();

      expect(wrapper.findAll('button').find((btn) => btn.text() === 'Crear').element.disabled).toBe(true);
    });

    it('clears the input and emits changed after a successful create', async () => {
      const wrapper = mountModal();
      await wrapper.find('input[placeholder]').setValue('New Folder');
      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(wrapper.find('input[placeholder]').element.value).toBe('');
      expect(wrapper.emitted('changed')).toHaveLength(1);
    });

    it('shows an error message when createFolder fails', async () => {
      mockFolderStore.createFolder.mockResolvedValue({
        success: false,
        errors: 'Nombre ya existe.',
      });
      const wrapper = mountModal();
      await wrapper.find('input[placeholder]').setValue('Dup');
      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(wrapper.text()).toContain('Nombre ya existe.');
    });
  });

  // ── Rename flow ───────────────────────────────────────────────────────────

  describe('rename flow', () => {
    it('shows the edit input when the rename button is clicked', async () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Editar carpeta"]').trigger('click');

      expect(wrapper.findAll('input[type="text"]').length).toBe(2);
    });

    it('hides the edit input when Cancelar is clicked during rename', async () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Editar carpeta"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Cancelar').trigger('click');

      expect(wrapper.findAll('input[type="text"]').length).toBe(1);
    });

    it('calls updateFolder with the new name when Guardar is clicked', async () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Editar carpeta"]').trigger('click');
      await wrapper.findAll('input[type="text"]').at(1).setValue('Renamed Folder');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Guardar').trigger('click');
      await flushPromises();

      expect(mockFolderStore.updateFolder).toHaveBeenCalledWith(1, { name: 'Renamed Folder', parent: null });
    });

    it('cancels rename when Esc is pressed in the edit input', async () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Editar carpeta"]').trigger('click');
      await wrapper.findAll('input[type="text"]').at(1).trigger('keyup', { key: 'Escape' });

      expect(wrapper.findAll('input[type="text"]').length).toBe(1);
    });
  });

  // ── Delete flow ───────────────────────────────────────────────────────────

  describe('delete flow', () => {
    it('shows delete confirmation for an empty folder', async () => {
      mockFolderStore.folders = [emptyFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');

      expect(wrapper.text()).toContain('Confirmar eliminación');
    });

    it('calls deleteFolder when Confirmar eliminación is clicked', async () => {
      mockFolderStore.folders = [emptyFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text().includes('Confirmar eliminación')).trigger('click');
      await flushPromises();

      expect(mockFolderStore.deleteFolder).toHaveBeenCalledWith(emptyFolder.id);
    });

    it('hides the delete confirmation when Cancelar is clicked', async () => {
      mockFolderStore.folders = [emptyFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Cancelar').trigger('click');

      expect(wrapper.text()).not.toContain('Confirmar eliminación');
    });

    it('blocks deletion and shows a warning when the folder has documents', async () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');

      expect(wrapper.text()).toContain('No se puede eliminar');
      expect(wrapper.text()).toContain('3 documento(s)');
      expect(wrapper.text()).not.toContain('Confirmar eliminación');
    });

    it('dismisses the warning when Entendido is clicked without calling deleteFolder', async () => {
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Entendido').trigger('click');

      expect(wrapper.text()).not.toContain('No se puede eliminar');
      expect(mockFolderStore.deleteFolder).not.toHaveBeenCalled();
    });
  });

  // ── Close ──────────────────────────────────────────────────────────────────

  describe('close', () => {
    it('emits update:modelValue with false when Cerrar is clicked', async () => {
      const wrapper = mountModal();
      await wrapper.findAll('button').find((btn) => btn.text() === 'Cerrar').trigger('click');

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]);
    });
  });

  // ── modelValue watcher ────────────────────────────────────────────────────

  describe('modelValue watcher', () => {
    it('calls fetchFolders when the modal is opened', async () => {
      const wrapper = mountModal({ modelValue: false });
      await wrapper.setProps({ modelValue: true });
      await flushPromises();

      expect(mockFolderStore.fetchFolders).toHaveBeenCalled();
    });
  });

  // ── initialParent prop ──────────────────────────────────────────────────────

  describe('initialParent prop', () => {
    const parentFolder = { id: 5, name: 'Mis Documentos', parent: null, document_count: 0 };

    function optionByText(wrapper, text) {
      return wrapper.findAll('option').find((opt) => opt.text().trim() === text);
    }

    async function openWith(props) {
      mockFolderStore.folders = [parentFolder];
      const wrapper = mountModal({ modelValue: false, ...props });
      await wrapper.setProps({ modelValue: true });
      await flushPromises();
      return wrapper;
    }

    it('pre-selects the initialParent folder in the "Dentro de:" select when opened', async () => {
      const wrapper = await openWith({ initialParent: 5 });

      expect(optionByText(wrapper, 'Mis Documentos').element.selected).toBe(true);
    });

    it('selects the root option when no initialParent is provided', async () => {
      const wrapper = await openWith({});

      expect(optionByText(wrapper, 'Ninguna (carpeta raíz)').element.selected).toBe(true);
    });

    it('resets the select back to initialParent after a successful create', async () => {
      const wrapper = await openWith({ initialParent: 5 });
      await wrapper.find('input[placeholder]').setValue('Nueva');
      await wrapper.find('form').trigger('submit');
      await flushPromises();

      expect(optionByText(wrapper, 'Mis Documentos').element.selected).toBe(true);
    });
  });

  // ── handleReorder ─────────────────────────────────────────────────────────

  describe('handleReorder', () => {
    it('calls reorderFolders with the folder id order when the tree reorders', async () => {
      mockFolderStore.folders = [
        { id: 1, name: 'A', parent: null, document_count: 0 },
        { id: 2, name: 'B', parent: null, document_count: 0 },
      ];
      const wrapper = mountModal();
      wrapper.findComponent(FolderManagerTree).vm.$emit('reorder', { orderedIds: [1, 2] });
      await flushPromises();

      expect(mockFolderStore.reorderFolders).toHaveBeenCalledWith([1, 2]);
    });

    it('shows an error message when reorderFolders fails', async () => {
      mockFolderStore.folders = [{ id: 1, name: 'A', parent: null, document_count: 0 }];
      mockFolderStore.reorderFolders.mockResolvedValue({ success: false });
      const wrapper = mountModal();
      wrapper.findComponent(FolderManagerTree).vm.$emit('reorder', { orderedIds: [1] });
      await flushPromises();

      expect(wrapper.text()).toContain('Error al reordenar');
    });
  });
});
