/**
 * Tests for DeleteFolderModal.vue.
 *
 * Covers: the folder name and inventory block, the case-sensitive DELETE gate,
 * the field reset on close, the store call on confirm, and the backend 409
 * surfacing without closing the modal.
 */

const mockFolderStore = {
  deleteFolder: jest.fn(),
  archiveFolder: jest.fn(),
  childrenOf: jest.fn(() => []),
};

// Nuxt auto-import — must be set before the component is required
global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import DeleteFolderModal from '../../components/panel/documents/DeleteFolderModal.vue';
import BaseModal from '../../components/base/BaseModal.vue';

const emptyFolder = { id: 7, name: 'Xpandia Project', document_count: 0, children_count: 0 };
const filledFolder = { id: 8, name: 'Aaron', document_count: 6, children_count: 0 };

function mountModal(props = {}) {
  return mount(DeleteFolderModal, {
    props: {
      modelValue: true,
      folder: emptyFolder,
      ...props,
    },
    global: {
      components: { BaseModal },
      stubs: { Teleport: true, Transition: false },
    },
  });
}

function typeInput(wrapper) {
  return wrapper.find('[data-testid="delete-folder-type-input"]');
}

function confirmButton(wrapper) {
  return wrapper.find('[data-testid="delete-folder-confirm"]');
}

function confirmIsDisabled(wrapper) {
  return confirmButton(wrapper).element.disabled;
}

function archiveButton(wrapper) {
  return wrapper.find('[data-testid="delete-folder-archive"]');
}

describe('DeleteFolderModal', () => {
  beforeEach(() => {
    mockFolderStore.deleteFolder.mockReset().mockResolvedValue({ success: true });
    mockFolderStore.archiveFolder.mockReset().mockResolvedValue({
      success: true, archivedFolders: 0, archivedDocuments: 0,
    });
    mockFolderStore.childrenOf.mockReset().mockReturnValue([]);
  });

  afterEach(() => {
    document.body.style.overflow = '';
  });

  // ── Inventory ─────────────────────────────────────────────────────────────

  describe('inventory', () => {
    it('names the folder and states that an empty folder loses nothing', () => {
      const wrapper = mountModal();

      expect(wrapper.text()).toContain('Xpandia Project');
      expect(wrapper.find('[data-testid="delete-folder-inventory"]').text())
        .toContain('Esta carpeta está vacía');
    });

    it('lists documents and subfolders when the folder still holds content', () => {
      mockFolderStore.childrenOf.mockReturnValue([{ id: 21, name: 'Contratos 2026' }]);
      const wrapper = mountModal({ folder: filledFolder });
      const inventory = wrapper.find('[data-testid="delete-folder-inventory"]');

      expect(inventory.text()).toContain('6 documentos');
      expect(inventory.text()).toContain('Contratos 2026');
      expect(typeInput(wrapper).exists()).toBe(false);
      // El botón destructivo no se renderiza: un botón muerto ES el callejón
      // sin salida que esta rama elimina.
      expect(confirmButton(wrapper).exists()).toBe(false);
    });
  });

  // ── DELETE gate ───────────────────────────────────────────────────────────

  describe('DELETE confirmation gate', () => {
    it('keeps the confirm button disabled until the exact word is typed', async () => {
      const wrapper = mountModal();

      expect(confirmIsDisabled(wrapper)).toBe(true);

      await typeInput(wrapper).setValue('DELETE');

      expect(confirmIsDisabled(wrapper)).toBe(false);
    });

    it.each(['delete', 'Delete', 'DELET', 'DELETE '])(
      'does not enable the confirm button for %p',
      async (value) => {
        const wrapper = mountModal();

        await typeInput(wrapper).setValue(value);

        expect(confirmIsDisabled(wrapper)).toBe(true);
      },
    );

    it('does not call the store when confirm is clicked without the typed word', async () => {
      const wrapper = mountModal();

      await confirmButton(wrapper).trigger('click');

      expect(mockFolderStore.deleteFolder).not.toHaveBeenCalled();
      expect(confirmIsDisabled(wrapper)).toBe(true);
      expect(wrapper.find('[data-testid="delete-folder-inventory"]').text())
        .toContain('Esta carpeta está vacía');
    });

    it('clears the typed word when the modal is closed and reopened', async () => {
      const wrapper = mountModal();
      await typeInput(wrapper).setValue('DELETE');

      await wrapper.setProps({ modelValue: false });
      await wrapper.setProps({ modelValue: true });
      await nextTick();

      expect(typeInput(wrapper).element.value).toBe('');
      expect(confirmIsDisabled(wrapper)).toBe(true);
    });
  });

  // ── Deletion ──────────────────────────────────────────────────────────────

  describe('deletion', () => {
    it('deletes the folder and closes on success', async () => {
      const wrapper = mountModal();
      await typeInput(wrapper).setValue('DELETE');

      await confirmButton(wrapper).trigger('click');
      await nextTick();

      expect(mockFolderStore.deleteFolder).toHaveBeenCalledWith(emptyFolder.id);
      expect(wrapper.emitted('deleted')).toEqual([[emptyFolder]]);
      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('shows the backend conflict detail and stays open when the delete is rejected', async () => {
      mockFolderStore.deleteFolder.mockResolvedValue({
        success: false,
        errors: { detail: 'La carpeta tiene 1 documento(s). Muévelos o elimínalos antes de borrarla.' },
      });
      const wrapper = mountModal();
      await typeInput(wrapper).setValue('DELETE');

      await confirmButton(wrapper).trigger('click');
      await nextTick();

      expect(wrapper.find('[data-testid="delete-folder-error"]').text())
        .toContain('La carpeta tiene 1 documento(s)');
      expect(wrapper.emitted('deleted')).toBeUndefined();
      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });

    it('closes without deleting when Cancelar is clicked', async () => {
      const wrapper = mountModal();
      await typeInput(wrapper).setValue('DELETE');

      const cancelBtn = wrapper.findAll('button').find((b) => b.text() === 'Cancelar');
      await cancelBtn.trigger('click');

      expect(mockFolderStore.deleteFolder).not.toHaveBeenCalled();
      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });
  });

  // ── Archivar como salida ───────────────────────────────────────────────────

  describe('archive escape hatch', () => {
    it('offers archiving before anything is typed, while the gate still blocks delete', () => {
      const wrapper = mountModal();

      // La salida está disponible de entrada...
      expect(archiveButton(wrapper).exists()).toBe(true);
      expect(archiveButton(wrapper).element.disabled).toBe(false);
      // ...mientras el destructivo sigue bloqueado por la palabra.
      expect(confirmIsDisabled(wrapper)).toBe(true);
    });

    it('explains what archiving does before the confirmation field', () => {
      const wrapper = mountModal();
      const html = wrapper.html();

      expect(html).toContain('delete-folder-archive-hint');
      expect(html.indexOf('delete-folder-archive-hint'))
        .toBeLessThan(html.indexOf('delete-folder-type-input'));
    });

    it('archives, emits archived with the cascade counts and closes', async () => {
      mockFolderStore.archiveFolder.mockResolvedValue({
        success: true, archivedFolders: 2, archivedDocuments: 6,
      });
      const wrapper = mountModal({ folder: filledFolder });

      await archiveButton(wrapper).trigger('click');
      await nextTick();
      await nextTick();

      expect(mockFolderStore.archiveFolder).toHaveBeenCalledWith(filledFolder.id);
      expect(wrapper.emitted('archived')[0][0]).toEqual({
        folder: filledFolder, folders: 2, documents: 6,
      });
      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    });

    it('presents archiving as the available action for a folder with content', () => {
      const wrapper = mountModal({ folder: filledFolder });

      expect(wrapper.text()).toContain('Esta carpeta no se puede eliminar');
      expect(archiveButton(wrapper).text()).toContain('Archivar carpeta');
      // Sin botón destructivo muerto: eso era el callejón sin salida.
      expect(confirmButton(wrapper).exists()).toBe(false);
    });

    it('keeps the modal open and shows the error when archiving fails', async () => {
      mockFolderStore.archiveFolder.mockResolvedValue({
        success: false, errors: { detail: 'No se pudo archivar.' },
      });
      const wrapper = mountModal({ folder: filledFolder });

      await archiveButton(wrapper).trigger('click');
      await nextTick();
      await nextTick();

      expect(wrapper.find('[data-testid="delete-folder-error"]').text())
        .toContain('No se pudo archivar.');
      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    });
  });
});
