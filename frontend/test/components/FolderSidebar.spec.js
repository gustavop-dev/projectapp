/**
 * Tests for FolderSidebar.vue.
 *
 * Covers: Todos/Sin-carpeta entries, folder list, select emits,
 * manage emits, active styling, reorderFolders on drag-end,
 * folder-drop emit on document drop, row alignment, the archived-content
 * badge, and the two row actions: archivar (siempre disponible, es la salida
 * de una carpeta con contenido) y eliminar (deshabilitado en cuanto la carpeta
 * contiene algo, archivado incluido, igual que el 409 del backend).
 */

const archivedContentCount = (f) => (f?.archived_document_count || 0)
  + (f?.archived_children_count || 0);

const mockFolderStore = {
  reorderFolders: jest.fn(),
  fetchFolders: jest.fn(),
  // Espejo de los getters reales: el ícono de eliminar depende de ellos.
  archivedContentCount,
  totalContentCount: (f) => (f?.active_document_count ?? f?.document_count ?? 0)
    + (f?.active_children_count ?? f?.children_count ?? 0)
    + archivedContentCount(f),
};

// Nuxt auto-import — must be set before the component is required
global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

import { mount } from '@vue/test-utils';
import FolderSidebar from '../../components/panel/documents/FolderSidebar.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

const folderA = { id: 1, name: 'Propuestas', document_count: 5, children_count: 0 };
const folderB = { id: 2, name: 'Contratos', document_count: 2, children_count: 0 };
const emptyFolder = { id: 3, name: 'Xpandia Project', document_count: 0, children_count: 0 };
const parentFolder = { id: 4, name: 'Clientes', document_count: 0, children_count: 2 };
// Estado mixto: activa por fuera, con archivados dentro — lo que deja una
// restauración por cadena.
const mixedFolder = {
  id: 5,
  name: 'temp',
  document_count: 0,
  children_count: 0,
  active_document_count: 0,
  active_children_count: 0,
  archived_document_count: 2,
  archived_children_count: 0,
};

// Stub that renders all items from v-model and can emit @end
const DraggableStub = {
  name: 'draggable',
  props: ['modelValue', 'itemKey', 'handle', 'ghostClass', 'chosenClass', 'disabled', 'tag'],
  emits: ['update:modelValue', 'start', 'end'],
  template: `
    <div data-testid="folder-draggable">
      <slot name="item" v-for="(el, i) in modelValue" :key="i" :element="el" />
    </div>
  `,
};

// BaseTooltip is a Nuxt auto-import; the stub keeps the trigger (and the body,
// which the real component only reveals on hover) reachable from the spec.
const BaseTooltipStub = {
  name: 'BaseTooltip',
  props: ['position', 'width', 'minWidth'],
  template: `
    <div data-testid="tooltip">
      <slot name="trigger" />
      <span data-testid="tooltip-body"><slot /></span>
    </div>
  `,
};

function mountSidebar(props = {}) {
  return mount(FolderSidebar, {
    props: {
      folders: [],
      activeId: 'all',
      totalCount: 0,
      isDragging: false,
      ...props,
    },
    global: {
      stubs: { draggable: DraggableStub },
      components: { BaseTooltip: BaseTooltipStub },
    },
  });
}

function folderNameButton(wrapper, name) {
  return wrapper.findAll('button').find((b) => b.text().includes(name));
}

describe('FolderSidebar', () => {
  beforeEach(() => {
    mockFolderStore.reorderFolders.mockReset().mockResolvedValue({ success: true });
    mockFolderStore.fetchFolders.mockReset().mockResolvedValue({ success: true });
  });

  // ── Static entries ────────────────────────────────────────────────────────

  describe('static entries', () => {
    it('renders the Todos entry with the total count', () => {
      const wrapper = mountSidebar({ totalCount: 42 });

      expect(wrapper.text()).toContain('Todos');
      expect(wrapper.text()).toContain('42');
    });

    it('renders the Sin carpeta entry', () => {
      const wrapper = mountSidebar();

      expect(wrapper.text()).toContain('Sin carpeta');
    });
  });

  // ── Folder list ───────────────────────────────────────────────────────────

  describe('folder list', () => {
    it('renders all folders from the folders prop', () => {
      const wrapper = mountSidebar({ folders: [folderA, folderB] });

      expect(wrapper.text()).toContain('Propuestas');
      expect(wrapper.text()).toContain('Contratos');
    });
  });

  // ── Select emits ──────────────────────────────────────────────────────────

  describe('select emits', () => {
    it('emits select with all when the Todos button is clicked', async () => {
      const wrapper = mountSidebar();
      const todosBtn = wrapper.findAll('button').find(b => b.text().includes('Todos'));
      await todosBtn.trigger('click');

      expect(wrapper.emitted('select')).toEqual([['all']]);
    });

    it('emits select with none when the Sin carpeta button is clicked', async () => {
      const wrapper = mountSidebar();
      const sinCarpetaBtn = wrapper.findAll('button').find(b => b.text().includes('Sin carpeta'));
      await sinCarpetaBtn.trigger('click');

      expect(wrapper.emitted('select')).toEqual([['none']]);
    });

    it('emits select with the folder id when a folder button is clicked', async () => {
      const wrapper = mountSidebar({ folders: [folderA] });
      const folderBtn = wrapper.findAll('button').find(b => b.text().includes('Propuestas'));
      await folderBtn.trigger('click');

      expect(wrapper.emitted('select')).toEqual([[folderA.id]]);
    });
  });

  // ── Manage emits ──────────────────────────────────────────────────────────

  describe('manage emits', () => {
    it('emits manage when the Gestionar link is clicked', async () => {
      const wrapper = mountSidebar();
      const gestionarBtn = wrapper.findAll('button').find(b => b.text() === 'Gestionar');
      await gestionarBtn.trigger('click');

      expect(wrapper.emitted('manage')).toBeTruthy();
    });

    it('emits manage when the Nueva carpeta button is clicked', async () => {
      const wrapper = mountSidebar();
      const nuevaBtn = wrapper.findAll('button').find(b => b.text().includes('Nueva carpeta'));
      await nuevaBtn.trigger('click');

      expect(wrapper.emitted('manage')).toBeTruthy();
    });
  });

  // ── Active styling ────────────────────────────────────────────────────────

  describe('active styling', () => {
    it('applies active class to the Todos entry when activeId is all', () => {
      const wrapper = mountSidebar({ activeId: 'all' });
      const todosBtn = wrapper.findAll('button').find(b => b.text().includes('Todos'));

      expect(todosBtn.classes()).toContain('bg-primary-soft');
    });

    it('applies active class to a folder entry matching activeId', () => {
      const wrapper = mountSidebar({ folders: [folderA], activeId: folderA.id });
      const folderDiv = wrapper.find(`[data-testid="folder-draggable"]`);

      expect(folderDiv.text()).toContain('Propuestas');
      // The inner button wrapper should have the active class
      const folderBtn = wrapper.findAll('button').find(b => b.text().includes('Propuestas'));
      expect(folderBtn.classes()).not.toContain('bg-emerald-50'); // button itself, parent div has class
    });
  });

  // ── Row alignment ─────────────────────────────────────────────────────────

  describe('row alignment', () => {
    it('starts folder names on the same horizontal axis as the Todos entry', () => {
      const wrapper = mountSidebar({ folders: [folderA] });
      const todosBtn = folderNameButton(wrapper, 'Todos');
      const folderBtn = folderNameButton(wrapper, 'Propuestas');

      expect(todosBtn.classes()).toContain('px-3');
      expect(folderBtn.classes()).toContain('px-3');
    });

    it('truncates a long folder name instead of wrapping or pushing the counter', () => {
      const longName = 'Documentación comercial de clientes corporativos 2026';
      const wrapper = mountSidebar({
        folders: [{ id: 9, name: longName, document_count: 3, children_count: 0 }],
      });
      const nameSpan = folderNameButton(wrapper, longName).find('span');

      expect(nameSpan.classes()).toContain('truncate');
    });
  });

  // ── Row actions ───────────────────────────────────────────────────────────

  describe('delete affordance', () => {
    it('emits delete with the folder when an empty folder’s delete icon is clicked', async () => {
      const wrapper = mountSidebar({ folders: [emptyFolder] });

      await wrapper.find('[data-testid="folder-delete"]').trigger('click');

      expect(wrapper.emitted('delete')).toEqual([[emptyFolder]]);
    });

    it('disables delete for a folder that still holds documents', async () => {
      const wrapper = mountSidebar({ folders: [folderA] });

      const button = wrapper.find('[data-testid="folder-delete"]');
      expect(button.element.disabled).toBe(true);
      await button.trigger('click');
      expect(wrapper.emitted('delete')).toBeUndefined();
    });

    it('disables delete for a folder that only holds subfolders', () => {
      const wrapper = mountSidebar({ folders: [parentFolder] });

      expect(wrapper.find('[data-testid="folder-delete"]').element.disabled).toBe(true);
    });

    it('disables delete when the only content left is archived', () => {
      // El 409 del backend cuenta lo archivado, así que el ícono también.
      const wrapper = mountSidebar({ folders: [mixedFolder] });

      expect(wrapper.find('[data-testid="folder-delete"]').element.disabled).toBe(true);
    });

    it('explains in the tooltip why a filled folder cannot be deleted', () => {
      const wrapper = mountSidebar({ folders: [folderA] });

      expect(wrapper.text()).toContain('No se puede eliminar');
      expect(wrapper.text()).toContain('Archívala en su lugar');
    });

    it('names the action in the tooltip when the folder can be deleted', () => {
      const wrapper = mountSidebar({ folders: [emptyFolder] });

      expect(wrapper.text()).toContain('Eliminar carpeta');
    });
  });

  describe('archive affordance', () => {
    it('emits archive with the folder when the archive icon is clicked', async () => {
      const wrapper = mountSidebar({ folders: [folderA] });

      await wrapper.find('[data-testid="folder-archive"]').trigger('click');

      expect(wrapper.emitted('archive')).toEqual([[folderA]]);
    });

    it('stays enabled for a filled folder — it is the way out', () => {
      const wrapper = mountSidebar({ folders: [folderA] });

      expect(wrapper.find('[data-testid="folder-archive"]').element.disabled).toBe(false);
      expect(wrapper.text()).toContain('Archivar carpeta');
    });
  });

  describe('archived content indicator', () => {
    it('shows the badge on a folder that still holds archived items', () => {
      const wrapper = mountSidebar({ folders: [mixedFolder] });

      expect(wrapper.find('[data-testid="folder-archived-badge"]').text()).toContain('2');
    });

    it('hides the badge when nothing is archived inside', () => {
      const wrapper = mountSidebar({ folders: [folderA] });

      expect(wrapper.find('[data-testid="folder-archived-badge"]').exists()).toBe(false);
    });

    it('emits view-archived so the row can be opened in its archived scope', async () => {
      const wrapper = mountSidebar({ folders: [mixedFolder] });

      await wrapper.find('[data-testid="folder-archived-badge"]').trigger('click');

      expect(wrapper.emitted('view-archived')).toEqual([[mixedFolder]]);
    });
  });

  describe('Archivados entry', () => {
    it('highlights only at the top of the archive, not inside a subfolder', () => {
      const atRoot = mountSidebar({ archiveScope: 'archived', activeId: 'root' });
      const inside = mountSidebar({ archiveScope: 'archived', activeId: 9 });

      const entryOf = (w) => w.find('[data-testid="folder-archived-entry"]').classes().join(' ');
      expect(entryOf(atRoot)).toContain('text-text-brand');
      expect(entryOf(inside)).not.toContain('text-text-brand');
    });
  });

  // ── Folder drag reorder ───────────────────────────────────────────────────

  describe('folder reorder', () => {
    it('calls reorderFolders when draggable emits end with a changed order', async () => {
      const wrapper = mountSidebar({ folders: [folderA, folderB] });

      // Simulate drag-end by directly manipulating localFolders and triggering handleFolderReorder
      wrapper.vm.localFolders = [folderB, folderA];
      await wrapper.findComponent({ name: 'draggable' }).vm.$emit('end');
      await flushPromises();

      expect(mockFolderStore.reorderFolders).toHaveBeenCalledWith([folderB.id, folderA.id]);
    });

    it('does not call reorderFolders when the order is unchanged after drag-end', async () => {
      const wrapper = mountSidebar({ folders: [folderA, folderB] });

      await wrapper.findComponent({ name: 'draggable' }).vm.$emit('end');
      await flushPromises();

      expect(mockFolderStore.reorderFolders).not.toHaveBeenCalled();
    });
  });

  // ── Document drop ─────────────────────────────────────────────────────────

  describe('document drop on folder', () => {
    it('emits folder-drop with null when a document is dropped on Sin carpeta', async () => {
      const wrapper = mountSidebar({ isDragging: true });
      const sinCarpetaBtn = wrapper.findAll('button').find(b => b.text().includes('Sin carpeta'));
      await sinCarpetaBtn.trigger('drop');

      expect(wrapper.emitted('folder-drop')).toEqual([[null]]);
    });
  });
});
