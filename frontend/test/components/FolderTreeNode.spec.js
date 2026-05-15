jest.mock('../../stores/document_folders', () => ({ useDocumentFolderStore: jest.fn() }));
jest.mock('../../composables/useFolderExpansion', () => ({ useFolderExpansion: jest.fn() }));

/**
 * Tests for FolderTreeNode.vue.
 *
 * Recursive tree node — covers chevron toggle, indentation, drop zone, drag handle,
 * recursive children rendering, and event emissions for select / folder-drop.
 */

const mockFolderStore = {
  moveFolder: jest.fn(),
  reorderFolders: jest.fn(),
};
useDocumentFolderStore.mockReturnValue(mockFolderStore);

const mockExpansion = {
  isExpanded: jest.fn(() => false),
  toggle: jest.fn(),
};
useFolderExpansion.mockReturnValue(mockExpansion);

import { useDocumentFolderStore } from '../../stores/document_folders';
import { useFolderExpansion } from '../../composables/useFolderExpansion';
import { mount } from '@vue/test-utils';
import FolderTreeNode from '../../components/panel/documents/FolderTreeNode.vue';

const DraggableStub = {
  name: 'draggable',
  props: ['modelValue', 'itemKey', 'handle', 'ghostClass', 'group', 'disabled', 'tag'],
  emits: ['change'],
  template: `
    <ul data-testid="folder-children-draggable">
      <slot name="item" v-for="el in modelValue" :key="el.id" :element="el" />
    </ul>
  `,
};

const LEAF_NODE = { folder: { id: 10, name: 'Hoja', document_count: 3 }, children: [] };

const PARENT_NODE = {
  folder: { id: 1, name: 'Padre', document_count: 5 },
  children: [
    { folder: { id: 2, name: 'Hijo A', document_count: 2 }, children: [] },
    { folder: { id: 3, name: 'Hijo B', document_count: 0 }, children: [] },
  ],
};

function mountNode(props = {}) {
  return mount(FolderTreeNode, {
    props: {
      node: LEAF_NODE,
      level: 0,
      activeId: 'all',
      isDragging: false,
      ...props,
    },
    global: {
      stubs: { draggable: DraggableStub },
    },
  });
}

beforeEach(() => {
  mockExpansion.isExpanded.mockReset().mockReturnValue(false);
  mockExpansion.toggle.mockReset();
  mockFolderStore.moveFolder.mockReset().mockResolvedValue({ success: true });
  mockFolderStore.reorderFolders.mockReset().mockResolvedValue({ success: true });
});

describe('FolderTreeNode — leaf rendering', () => {
  it('renders the folder name and document_count', () => {
    const wrapper = mountNode();
    expect(wrapper.text()).toContain('Hoja');
    expect(wrapper.text()).toContain('3');
  });

  it('does not show a chevron when there are no children', () => {
    const wrapper = mountNode();
    const chevronBtn = wrapper.find('button[title="Expandir"], button[title="Colapsar"]');
    expect(chevronBtn.exists()).toBe(false);
  });

  it('emits select(folder.id) when label button is clicked', async () => {
    const wrapper = mountNode();
    await wrapper.findAll('button').filter((b) => b.text().includes('Hoja'))[0].trigger('click');
    expect(wrapper.emitted('select')).toBeTruthy();
    expect(wrapper.emitted('select')[0]).toEqual([10]);
  });

  it('applies padding-left scaled by level', () => {
    const wrapper = mountNode({ level: 2 });
    const row = wrapper.find('div.flex.items-center.rounded-lg');
    expect(row.attributes('style')).toContain('padding-left: 24px');
  });
});

describe('FolderTreeNode — chevron + expand', () => {
  it('renders a chevron when the node has children', () => {
    const wrapper = mountNode({ node: PARENT_NODE });
    const chevron = wrapper.find('button[title="Expandir"]');
    expect(chevron.exists()).toBe(true);
  });

  it('chevron click calls toggle(folder.id) on the composable', async () => {
    const wrapper = mountNode({ node: PARENT_NODE });
    await wrapper.find('button[title="Expandir"]').trigger('click');
    expect(mockExpansion.toggle).toHaveBeenCalledWith(1);
  });

  it('does not render the children draggable while collapsed', () => {
    mockExpansion.isExpanded.mockReturnValue(false);
    const wrapper = mountNode({ node: PARENT_NODE });
    expect(wrapper.find('[data-testid="folder-children-draggable"]').exists()).toBe(false);
  });

  it('renders children inside the draggable when expanded', () => {
    mockExpansion.isExpanded.mockReturnValue(true);
    const wrapper = mountNode({ node: PARENT_NODE });
    expect(wrapper.find('[data-testid="folder-children-draggable"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Hijo A');
    expect(wrapper.text()).toContain('Hijo B');
  });
});

describe('FolderTreeNode — drag and drop', () => {
  it('emits folder-drop(folder.id) when a document is dropped while isDragging', async () => {
    const wrapper = mountNode({ isDragging: true });
    const row = wrapper.find('div.flex.items-center.rounded-lg');
    await row.trigger('dragover');
    await row.trigger('drop');
    expect(wrapper.emitted('folder-drop')).toBeTruthy();
    expect(wrapper.emitted('folder-drop')[0]).toEqual([10]);
  });

  it('does not emit folder-drop when not currently dragging a document', async () => {
    const wrapper = mountNode({ isDragging: false });
    const row = wrapper.find('div.flex.items-center.rounded-lg');
    await row.trigger('drop');
    expect(wrapper.emitted('folder-drop')).toBeFalsy();
  });

  it('children @change with `added` triggers moveFolder reparenting', async () => {
    mockExpansion.isExpanded.mockReturnValue(true);
    const wrapper = mountNode({ node: PARENT_NODE });
    const draggable = wrapper.findComponent(DraggableStub);
    draggable.vm.$emit('change', {
      added: { element: { id: 99 }, newIndex: 0 },
    });
    await wrapper.vm.$nextTick();
    expect(mockFolderStore.moveFolder).toHaveBeenCalledWith(99, {
      parent_id: 1,
      position: 0,
    });
  });

  it('children @change with `moved` triggers reorderFolders scoped by parent', async () => {
    mockExpansion.isExpanded.mockReturnValue(true);
    const wrapper = mountNode({ node: PARENT_NODE });
    const draggable = wrapper.findComponent(DraggableStub);
    draggable.vm.$emit('change', {
      moved: { oldIndex: 0, newIndex: 1 },
    });
    await wrapper.vm.$nextTick();
    expect(mockFolderStore.reorderFolders).toHaveBeenCalledWith({
      parent_id: 1,
      ids: [3, 2],  // children reordered
    });
  });

  it('children @change with `removed` is ignored (handled by receiving list)', async () => {
    mockExpansion.isExpanded.mockReturnValue(true);
    const wrapper = mountNode({ node: PARENT_NODE });
    const draggable = wrapper.findComponent(DraggableStub);
    draggable.vm.$emit('change', { removed: { element: { id: 2 } } });
    await wrapper.vm.$nextTick();
    expect(mockFolderStore.moveFolder).not.toHaveBeenCalled();
    expect(mockFolderStore.reorderFolders).not.toHaveBeenCalled();
  });
});
