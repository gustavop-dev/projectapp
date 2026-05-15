/**
 * Tests for FolderPathChip.vue.
 *
 * Renders a breadcrumb chip "Root › Mid › Leaf" for a given folderId by
 * looking up the folder + ancestors from useDocumentFolderStore.
 */

const mockFolderStore = {
  getById: jest.fn(),
  ancestorsOf: jest.fn(),
};

global.useDocumentFolderStore = jest.fn(() => mockFolderStore);

import { mount } from '@vue/test-utils';
import FolderPathChip from '../../components/panel/documents/FolderPathChip.vue';

beforeEach(() => {
  mockFolderStore.getById.mockReset();
  mockFolderStore.ancestorsOf.mockReset();
});

describe('FolderPathChip', () => {
  it('renders nothing when folderId is null', () => {
    const wrapper = mount(FolderPathChip, { props: { folderId: null } });
    expect(wrapper.text()).toBe('');
    expect(wrapper.find('span').exists()).toBe(false);
  });

  it('renders nothing when the folder is not found in the store', () => {
    mockFolderStore.getById.mockReturnValue(null);
    const wrapper = mount(FolderPathChip, { props: { folderId: 99 } });
    expect(wrapper.text()).toBe('');
  });

  it('renders just the folder name when it is a root folder', () => {
    mockFolderStore.getById.mockReturnValue({ id: 1, name: 'Clientes' });
    mockFolderStore.ancestorsOf.mockReturnValue([]);
    const wrapper = mount(FolderPathChip, { props: { folderId: 1 } });
    expect(wrapper.text()).toContain('Clientes');
    expect(wrapper.text()).not.toContain('›');
  });

  it('renders ancestor → folder path with › separator', () => {
    mockFolderStore.getById.mockReturnValue({ id: 3, name: '2026' });
    mockFolderStore.ancestorsOf.mockReturnValue([
      { id: 1, name: 'Clientes' },
      { id: 2, name: 'Activos' },
    ]);
    const wrapper = mount(FolderPathChip, { props: { folderId: 3 } });
    expect(wrapper.text()).toContain('Clientes › Activos › 2026');
  });

  it('sets the full path as title for accessibility tooltip', () => {
    mockFolderStore.getById.mockReturnValue({ id: 2, name: 'Activos' });
    mockFolderStore.ancestorsOf.mockReturnValue([{ id: 1, name: 'Clientes' }]);
    const wrapper = mount(FolderPathChip, { props: { folderId: 2 } });
    expect(wrapper.find('span[title]').attributes('title')).toBe('Clientes › Activos');
  });

  it('applies truncate utility class so long paths do not overflow', () => {
    mockFolderStore.getById.mockReturnValue({ id: 4, name: 'Leaf' });
    mockFolderStore.ancestorsOf.mockReturnValue([
      { id: 1, name: 'A very long ancestor name that exceeds the chip width' },
      { id: 2, name: 'Another long one' },
      { id: 3, name: 'And another' },
    ]);
    const wrapper = mount(FolderPathChip, { props: { folderId: 4 } });
    const chip = wrapper.find('span.truncate');
    expect(chip.exists()).toBe(true);
    const outer = wrapper.find('span.max-w-\\[14rem\\]');
    expect(outer.exists()).toBe(true);
  });
});
