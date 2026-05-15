jest.mock('../../stores/document_folders', () => ({ useDocumentFolderStore: jest.fn() }));
jest.mock('../../composables/useFolderExpansion', () => ({ useFolderExpansion: jest.fn() }));

/**
 * Tests for FolderSidebar.vue (nested-tree version, 2026-05-15).
 *
 * Covers:
 *  - Static entries (Todos, Sin carpeta) and counts
 *  - Renders FolderTreeNode per root from folderStore.tree
 *  - Auto-expands ancestors of activeId on mount
 *  - Manage emits
 *  - folder-drop on "Sin carpeta" emits null
 *  - Root-level drag @change triggers moveFolder (reparent to root) or reorderFolders
 */

const folderA = { id: 1, name: 'Propuestas', document_count: 5, parent: null, order: 0 };
const folderB = { id: 2, name: 'Contratos', document_count: 2, parent: null, order: 1 };

const TREE = [
  { folder: folderA, children: [] },
  { folder: folderB, children: [] },
];

const mockFolderStore = {
  folders: [folderA, folderB],
  tree: TREE,
  moveFolder: jest.fn(),
  reorderFolders: jest.fn(),
  ancestorsOf: jest.fn(() => []),
  fetchFolders: jest.fn(),
};
useDocumentFolderStore.mockReturnValue(mockFolderStore);

const mockExpansion = {
  expandPath: jest.fn(),
};
useFolderExpansion.mockReturnValue(mockExpansion);

import { useDocumentFolderStore } from '../../stores/document_folders';
import { useFolderExpansion } from '../../composables/useFolderExpansion';
import { mount } from '@vue/test-utils';
import FolderSidebar from '../../components/panel/documents/FolderSidebar.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

// Stub the recursive FolderTreeNode so we can assert sidebar behavior
// without rendering the recursive tree under test.
const FolderTreeNodeStub = {
  name: 'FolderTreeNode',
  props: ['node', 'level', 'activeId', 'isDragging'],
  emits: ['select', 'folder-drop'],
  template: `
    <li :data-testid="'tree-node-' + node.folder.id">
      <button @click="$emit('select', node.folder.id)">{{ node.folder.name }}</button>
    </li>
  `,
};

const DraggableStub = {
  name: 'draggable',
  props: ['modelValue', 'itemKey', 'handle', 'ghostClass', 'group', 'disabled', 'tag'],
  emits: ['change'],
  template: `
    <div data-testid="root-draggable">
      <slot name="item" v-for="el in modelValue" :key="el.id" :element="el" />
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
      stubs: { draggable: DraggableStub, FolderTreeNode: FolderTreeNodeStub },
    },
  });
}

beforeEach(() => {
  mockFolderStore.tree = TREE;
  mockFolderStore.folders = [folderA, folderB];
  mockFolderStore.moveFolder.mockReset().mockResolvedValue({ success: true });
  mockFolderStore.reorderFolders.mockReset().mockResolvedValue({ success: true });
  mockFolderStore.ancestorsOf.mockReset().mockReturnValue([]);
  mockFolderStore.fetchFolders.mockReset();
  mockExpansion.expandPath.mockReset();
});

describe('FolderSidebar — static entries', () => {
  it('renders the Todos entry with the total count', () => {
    const wrapper = mountSidebar({ totalCount: 42 });
    expect(wrapper.text()).toContain('Todos');
    expect(wrapper.text()).toContain('42');
  });

  it('renders the Sin carpeta entry', () => {
    expect(mountSidebar().text()).toContain('Sin carpeta');
  });
});

describe('FolderSidebar — tree rendering', () => {
  it('renders a FolderTreeNode for each root folder in the store tree', () => {
    const wrapper = mountSidebar();
    expect(wrapper.find('[data-testid="tree-node-1"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="tree-node-2"]').exists()).toBe(true);
  });

  it('forwards select events bubbling from tree nodes', async () => {
    const wrapper = mountSidebar();
    await wrapper.find('[data-testid="tree-node-1"] button').trigger('click');
    expect(wrapper.emitted('select')).toEqual([[1]]);
  });
});

describe('FolderSidebar — select emits for static entries', () => {
  it('emits select(all) when Todos is clicked', async () => {
    const wrapper = mountSidebar();
    const todosBtn = wrapper.findAll('button').find((b) => b.text().includes('Todos'));
    await todosBtn.trigger('click');
    expect(wrapper.emitted('select')).toEqual([['all']]);
  });

  it('emits select(none) when Sin carpeta is clicked', async () => {
    const wrapper = mountSidebar();
    const noneBtn = wrapper.findAll('button').find((b) => b.text().includes('Sin carpeta'));
    await noneBtn.trigger('click');
    expect(wrapper.emitted('select')).toEqual([['none']]);
  });
});

describe('FolderSidebar — manage emits', () => {
  it('emits manage when the Gestionar link is clicked', async () => {
    const wrapper = mountSidebar();
    const btn = wrapper.findAll('button').find((b) => b.text() === 'Gestionar');
    await btn.trigger('click');
    expect(wrapper.emitted('manage')).toBeTruthy();
  });

  it('emits manage when the Nueva carpeta button is clicked', async () => {
    const wrapper = mountSidebar();
    const btn = wrapper.findAll('button').find((b) => b.text().includes('Nueva carpeta'));
    await btn.trigger('click');
    expect(wrapper.emitted('manage')).toBeTruthy();
  });
});

describe('FolderSidebar — active styling', () => {
  it('applies active class to Todos when activeId=all', () => {
    const wrapper = mountSidebar({ activeId: 'all' });
    const btn = wrapper.findAll('button').find((b) => b.text().includes('Todos'));
    expect(btn.classes()).toContain('bg-primary-soft');
  });
});

describe('FolderSidebar — auto-expand ancestors', () => {
  it('calls expandPath with ancestor ids when activeId is a folder id', () => {
    mockFolderStore.ancestorsOf.mockReturnValue([{ id: 1 }, { id: 5 }]);
    mountSidebar({ activeId: 9 });
    expect(mockExpansion.expandPath).toHaveBeenCalledWith([1, 5]);
  });

  it('does not call expandPath for string activeId like "all"', () => {
    mountSidebar({ activeId: 'all' });
    // expandPath may be called with [] but never with non-empty for a non-number activeId
    const calls = mockExpansion.expandPath.mock.calls;
    for (const [arg] of calls) {
      expect(arg).toEqual([]);
    }
  });
});

describe('FolderSidebar — document drop on Sin carpeta', () => {
  it('emits folder-drop(null) when a document is dropped while isDragging', async () => {
    const wrapper = mountSidebar({ isDragging: true });
    const noneBtn = wrapper.findAll('button').find((b) => b.text().includes('Sin carpeta'));
    await noneBtn.trigger('dragover');
    await noneBtn.trigger('drop');
    expect(wrapper.emitted('folder-drop')).toEqual([[null]]);
  });

  it('does not emit folder-drop when not currently dragging', async () => {
    const wrapper = mountSidebar({ isDragging: false });
    const noneBtn = wrapper.findAll('button').find((b) => b.text().includes('Sin carpeta'));
    await noneBtn.trigger('drop');
    expect(wrapper.emitted('folder-drop')).toBeFalsy();
  });
});

describe('FolderSidebar — root-level drag reparent / reorder', () => {
  it('calls moveFolder when an item is added at the root scope', async () => {
    const wrapper = mountSidebar();
    const draggable = wrapper.findComponent(DraggableStub);
    draggable.vm.$emit('change', { added: { element: { id: 99 }, newIndex: 0 } });
    await flushPromises();
    expect(mockFolderStore.moveFolder).toHaveBeenCalledWith(99, {
      parent_id: null,
      position: 0,
    });
  });

  it('calls reorderFolders scoped to parent_id=null when siblings are reordered at root', async () => {
    const wrapper = mountSidebar();
    const draggable = wrapper.findComponent(DraggableStub);
    draggable.vm.$emit('change', { moved: { oldIndex: 0, newIndex: 1 } });
    await flushPromises();
    expect(mockFolderStore.reorderFolders).toHaveBeenCalledWith({
      parent_id: null,
      ids: [2, 1],  // reordered
    });
  });
});
