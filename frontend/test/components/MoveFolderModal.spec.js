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
};

// Nuxt auto-imports — must be set before the component is required
global.useDocumentStore = jest.fn(() => mockDocumentStore);
global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

import { mount } from '@vue/test-utils';
import MoveFolderModal from '../../components/panel/documents/MoveFolderModal.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const baseDocument = { id: 10, title: 'Especificaciones técnicas', folder_id: null };
const baseFolder = { id: 3, name: 'Propuestas', document_count: 5 };

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
    mockFolderStore.folders = [];
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
      mockFolderStore.folders = [baseFolder];
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Propuestas');
    });

    it('shows empty state when there are no folders', () => {
      mockFolderStore.folders = [];
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
      mockFolderStore.folders = [baseFolder];
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
