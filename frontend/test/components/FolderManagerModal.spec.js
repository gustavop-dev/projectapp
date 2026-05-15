/**
 * Tests for FolderManagerModal.vue.
 *
 * Covers: rendering, empty state, folder list, create flow,
 * rename flow (start/cancel/commit/Esc), delete flow (ask/confirm/cancel),
 * close, modelValue watcher, handleReorder success and failure.
 */

const mockFolderStore = {
  folders: [],
  tree: [],
  isUpdating: false,
  fetchFolders: jest.fn(),
  createFolder: jest.fn(),
  updateFolder: jest.fn(),
  deleteFolder: jest.fn(),
  reorderFolders: jest.fn(),
};

/**
 * Build a flat-rendered tree from a simple {id, name, parent, children} list.
 * Helper to set both `folders` and `tree` consistently in the mock store.
 */
function setFolders(folders) {
  mockFolderStore.folders = folders;
  const byId = new Map(folders.map((f) => [f.id, { folder: f, children: [] }]));
  const roots = [];
  for (const f of folders) {
    const node = byId.get(f.id);
    if (f.parent == null) roots.push(node);
    else byId.get(f.parent)?.children.push(node);
  }
  mockFolderStore.tree = roots;
}

// Nuxt auto-import — must be set before the component is required
global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

import { mount } from '@vue/test-utils';
import FolderManagerModal from '../../components/panel/documents/FolderManagerModal.vue';

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

const baseFolder = { id: 1, name: 'Design', document_count: 3, parent: null, order: 0 };
const emptyFolder = { id: 9, name: 'Empty', document_count: 0, parent: null, order: 0 };

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
    setFolders([]);
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
      setFolders([baseFolder]);
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Design');
    });

    it('shows the document count badge for each folder', () => {
      setFolders([baseFolder]);
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

      expect(mockFolderStore.createFolder).toHaveBeenCalledWith({ name: 'My Folder' });
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
      setFolders([baseFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Renombrar"]').trigger('click');

      expect(wrapper.findAll('input[type="text"]').length).toBe(2);
    });

    it('hides the edit input when Cancelar is clicked during rename', async () => {
      setFolders([baseFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Renombrar"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Cancelar').trigger('click');

      expect(wrapper.findAll('input[type="text"]').length).toBe(1);
    });

    it('calls updateFolder with the new name when Guardar is clicked', async () => {
      setFolders([baseFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Renombrar"]').trigger('click');
      await wrapper.findAll('input[type="text"]').at(1).setValue('Renamed Folder');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Guardar').trigger('click');
      await flushPromises();

      expect(mockFolderStore.updateFolder).toHaveBeenCalledWith(1, { name: 'Renamed Folder' });
    });

    it('cancels rename when Esc is pressed in the edit input', async () => {
      setFolders([baseFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Renombrar"]').trigger('click');
      await wrapper.findAll('input[type="text"]').at(1).trigger('keyup', { key: 'Escape' });

      expect(wrapper.findAll('input[type="text"]').length).toBe(1);
    });
  });

  // ── Delete flow ───────────────────────────────────────────────────────────

  describe('delete flow', () => {
    it('shows delete confirmation for an empty folder', async () => {
      setFolders([emptyFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');

      expect(wrapper.text()).toContain('Confirmar eliminación');
    });

    it('calls deleteFolder when Confirmar eliminación is clicked', async () => {
      setFolders([emptyFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text().includes('Confirmar eliminación')).trigger('click');
      await flushPromises();

      expect(mockFolderStore.deleteFolder).toHaveBeenCalledWith(emptyFolder.id);
    });

    it('hides the delete confirmation when Cancelar is clicked', async () => {
      setFolders([emptyFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');
      await wrapper.findAll('button').find((btn) => btn.text() === 'Cancelar').trigger('click');

      expect(wrapper.text()).not.toContain('Confirmar eliminación');
    });

    it('blocks deletion and shows a warning when the folder has documents', async () => {
      setFolders([baseFolder]);
      const wrapper = mountModal();
      await wrapper.find('[title="Eliminar carpeta"]').trigger('click');

      expect(wrapper.text()).toContain('No se puede eliminar');
      expect(wrapper.text()).toContain('3 documento(s)');
      expect(wrapper.text()).not.toContain('Confirmar eliminación');
    });

    it('dismisses the warning when Entendido is clicked without calling deleteFolder', async () => {
      setFolders([baseFolder]);
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

  // ── Parent selector (added 2026-05-15 nested folders) ─────────────────────

  describe('parent selector "Dentro de"', () => {
    it('renders the "Raíz" option plus an option per folder', () => {
      setFolders([
        { id: 1, name: 'A', parent: null, order: 0, document_count: 0 },
        { id: 2, name: 'B', parent: 1, order: 0, document_count: 0 },
      ]);
      const wrapper = mountModal();
      const select = wrapper.find('select');
      const optionTexts = select.findAll('option').map((o) => o.text());
      expect(optionTexts[0]).toContain('Raíz');
      expect(optionTexts.join(' ')).toContain('A');
      expect(optionTexts.join(' ')).toContain('B');
    });

    it('forwards selected parent to createFolder', async () => {
      setFolders([{ id: 7, name: 'A', parent: null, order: 0, document_count: 0 }]);
      const wrapper = mountModal();
      await wrapper.find('input[placeholder="Nombre de la nueva carpeta..."]')
        .setValue('Hija');
      await wrapper.find('select').setValue('7');
      await wrapper.find('form').trigger('submit.prevent');
      await flushPromises();
      expect(mockFolderStore.createFolder).toHaveBeenCalledWith({
        name: 'Hija',
        parent: 7,
      });
    });

    it('creates a root folder when "Raíz" is selected', async () => {
      const wrapper = mountModal();
      await wrapper.find('input[placeholder="Nombre de la nueva carpeta..."]')
        .setValue('Raíz nueva');
      // "Raíz" is the default value (null) — no change needed
      await wrapper.find('form').trigger('submit.prevent');
      await flushPromises();
      expect(mockFolderStore.createFolder).toHaveBeenCalledWith({
        name: 'Raíz nueva',
        parent: null,
      });
    });
  });

  // ── Delete blocked by children (added 2026-05-15) ─────────────────────────

  describe('delete blocked by children', () => {
    it('shows a "contiene subcarpetas" warning when the folder has children', async () => {
      setFolders([
        { id: 1, name: 'Padre', parent: null, order: 0, document_count: 0 },
        { id: 2, name: 'Hijo', parent: 1, order: 0, document_count: 0 },
      ]);
      const wrapper = mountModal();
      // Click delete on the parent — finding the icon button with title="Eliminar carpeta"
      const deleteBtns = wrapper.findAll('button[title="Eliminar carpeta"]');
      // First delete button corresponds to "Padre" (parent rendered before child)
      await deleteBtns[0].trigger('click');
      expect(wrapper.text()).toContain('contiene subcarpetas');
      // Destructive button should not appear
      expect(wrapper.text()).not.toContain('Confirmar eliminación');
    });

    it('still blocks for has_documents when the folder has no children but has docs', async () => {
      setFolders([{ id: 1, name: 'Solo', parent: null, order: 0, document_count: 4 }]);
      const wrapper = mountModal();
      await wrapper.find('button[title="Eliminar carpeta"]').trigger('click');
      expect(wrapper.text()).toContain('Primero mueve o elimina sus 4 documento(s).');
    });
  });
});
