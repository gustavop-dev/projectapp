jest.mock('../../stores/document_folders', () => ({ useDocumentFolderStore: jest.fn() }));
jest.mock('../../stores/documents', () => ({ useDocumentStore: jest.fn() }));

/**
 * Tests for MoveFolderModal.vue.
 *
 * Covers: visibility, document title, folder list, moveToFolder flows
 * (null/folder-id), changed emit, error display, close/cancel emits.
 */

const mockDocumentStore = {
  updateDocument: jest.fn(),
};

const mockFolderStore = {
  folders: [],
  tree: [],
};

// Build tree from a flat folder list so existing flat-list tests keep working
// and nested tests can assert depth-indentation.
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

useDocumentStore.mockReturnValue(mockDocumentStore);
useDocumentFolderStore.mockReturnValue(mockFolderStore);

import { useDocumentStore } from '../../stores/documents';
import { useDocumentFolderStore } from '../../stores/document_folders';
import { mount } from '@vue/test-utils';
import MoveFolderModal from '../../components/panel/documents/MoveFolderModal.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const baseDocument = { id: 10, title: 'Especificaciones técnicas', folder_id: null };
const baseFolder = { id: 3, name: 'Propuestas', document_count: 5, parent: null, order: 0 };

function mountModal(props = {}) {
  return mount(MoveFolderModal, {
    props: { modelValue: true, document: baseDocument, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('MoveFolderModal', () => {
  beforeEach(() => {
    setFolders([]);
    mockDocumentStore.updateDocument.mockReset().mockResolvedValue({ success: true });
  });

  // ── Visibility ────────────────────────────────────────────────────────────

  describe('visibility', () => {
    it('does not render modal content when modelValue is false', () => {
      const wrapper = mountModal({ modelValue: false });

      expect(wrapper.text()).not.toContain('Mover documento');
    });

    it('does not render modal content when document prop is null', () => {
      const wrapper = mountModal({ document: null });

      expect(wrapper.text()).not.toContain('Mover documento');
    });

    it('renders the document title in the modal header', () => {
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Especificaciones técnicas');
    });
  });

  // ── Folder options ────────────────────────────────────────────────────────

  describe('folder list', () => {
    it('renders the Sin carpeta option', () => {
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Sin carpeta');
    });

    it('renders all folders from the store', () => {
      setFolders([baseFolder]);
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Propuestas');
    });

    it('shows empty state when there are no folders', () => {
      setFolders([]);
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('No hay carpetas creadas.');
    });
  });

  // ── Move to folder ────────────────────────────────────────────────────────

  describe('moveToFolder', () => {
    it('calls updateDocument with null when Sin carpeta is clicked', async () => {
      const wrapper = mountModal({
        document: { ...baseDocument, folder_id: 5 },
      });
      const sinCarpetaBtn = wrapper.findAll('button').find(b => b.text().includes('Sin carpeta'));
      await sinCarpetaBtn.trigger('click');
      await flushPromises();

      expect(mockDocumentStore.updateDocument).toHaveBeenCalledWith(
        baseDocument.id,
        { folder_id: null }
      );
    });

    it('calls updateDocument with the folder id when a folder button is clicked', async () => {
      setFolders([baseFolder]);
      const wrapper = mountModal({ document: { ...baseDocument, folder_id: null } });
      const folderBtn = wrapper.findAll('button').find(b => b.text().includes('Propuestas'));
      await folderBtn.trigger('click');
      await flushPromises();

      expect(mockDocumentStore.updateDocument).toHaveBeenCalledWith(
        baseDocument.id,
        { folder_id: baseFolder.id }
      );
    });

    it('emits changed after a successful move', async () => {
      const wrapper = mountModal({
        document: { ...baseDocument, folder_id: 5 },
      });
      const sinCarpetaBtn = wrapper.findAll('button').find(b => b.text().includes('Sin carpeta'));
      await sinCarpetaBtn.trigger('click');
      await flushPromises();

      expect(wrapper.emitted('changed')).toBeTruthy();
    });

    it('shows an error message when the move fails', async () => {
      mockDocumentStore.updateDocument.mockResolvedValueOnce({ success: false });
      const wrapper = mountModal({
        document: { ...baseDocument, folder_id: 5 },
      });
      const sinCarpetaBtn = wrapper.findAll('button').find(b => b.text().includes('Sin carpeta'));
      await sinCarpetaBtn.trigger('click');
      await flushPromises();

      expect(wrapper.text()).toContain('No se pudo mover el documento.');
    });

    it('does not call updateDocument when the current folder is already selected', async () => {
      // document.folder_id === null and clicking Sin carpeta (null) → should just close
      const wrapper = mountModal({ document: { ...baseDocument, folder_id: null } });
      const sinCarpetaBtn = wrapper.findAll('button').find(b => b.text().includes('Sin carpeta'));
      await sinCarpetaBtn.trigger('click');
      await flushPromises();

      expect(mockDocumentStore.updateDocument).not.toHaveBeenCalled();
    });
  });

  // ── Tree indentation (added 2026-05-15 nested folders) ───────────────────

  describe('tree indentation', () => {
    it('indents nested folders by depth via padding-left', () => {
      setFolders([
        { id: 1, name: 'Padre', parent: null, order: 0, document_count: 0 },
        { id: 2, name: 'Hijo', parent: 1, order: 0, document_count: 0 },
        { id: 3, name: 'Nieto', parent: 2, order: 0, document_count: 0 },
      ]);
      const wrapper = mountModal();
      const buttons = wrapper.findAll('button').filter((b) =>
        ['Padre', 'Hijo', 'Nieto'].some((n) => b.text().includes(n))
      );
      const styles = buttons.map((b) => b.attributes('style') || '');
      // depth 0 → 12px, depth 1 → 28px, depth 2 → 44px
      expect(styles.some((s) => s.includes('12px'))).toBe(true);
      expect(styles.some((s) => s.includes('28px'))).toBe(true);
      expect(styles.some((s) => s.includes('44px'))).toBe(true);
    });

    it('move to a nested folder PATCHes with the leaf id', async () => {
      setFolders([
        { id: 1, name: 'Clientes', parent: null, order: 0, document_count: 0 },
        { id: 2, name: 'Activos', parent: 1, order: 0, document_count: 0 },
        { id: 3, name: '2026', parent: 2, order: 0, document_count: 0 },
      ]);
      const wrapper = mountModal({ document: { ...baseDocument, folder_id: null } });
      const leafBtn = wrapper.findAll('button').find((b) => b.text().includes('2026'));
      await leafBtn.trigger('click');
      await flushPromises();
      expect(mockDocumentStore.updateDocument).toHaveBeenCalledWith(baseDocument.id, {
        folder_id: 3,
      });
    });
  });

  // ── Close / cancel ────────────────────────────────────────────────────────

  describe('close', () => {
    it('emits update:modelValue false when the cancel button is clicked', async () => {
      const wrapper = mountModal();
      const cancelBtn = wrapper.findAll('button').find(b => b.text() === 'Cancelar');
      await cancelBtn.trigger('click');

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('emits update:modelValue false when the header close button is clicked', async () => {
      const wrapper = mountModal();
      const closeBtn = wrapper.find('button svg path[d*="M6 18L18"]').element.closest('button');
      await closeBtn.dispatchEvent(new Event('click'));
      await wrapper.vm.$nextTick();

      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });
  });
});
