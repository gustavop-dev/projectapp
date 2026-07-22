import { normalizePersistedSelectedIds } from '../../utils/proposalModuleSelectionStorage';

const CATALOG = [
  { id: 'group-5', groupId: 5 },
  { id: 'group-9', groupId: 9 },
  { id: 'module-ai', groupId: null },
];

describe('normalizePersistedSelectedIds', () => {
  it('returns an empty list for non-array input', () => {
    expect(normalizePersistedSelectedIds('group-5', CATALOG)).toEqual([]);
  });

  it('returns an empty list for an empty persisted list', () => {
    expect(normalizePersistedSelectedIds([], CATALOG)).toEqual([]);
  });

  it('keeps ids that already carry the canonical prefix', () => {
    expect(normalizePersistedSelectedIds(['module-ai', 'group-5'], CATALOG))
      .toEqual(['module-ai', 'group-5']);
  });

  it('maps bare group ids to their catalog item id', () => {
    expect(normalizePersistedSelectedIds(['5', 9], CATALOG))
      .toEqual(['group-5', 'group-9']);
  });

  it('keeps unknown bare ids untouched and skips empty entries', () => {
    expect(normalizePersistedSelectedIds(['77', null, ''], CATALOG))
      .toEqual(['77']);
  });

  it('dedups entries that normalize to the same canonical id', () => {
    expect(normalizePersistedSelectedIds(['5', 'group-5'], CATALOG))
      .toEqual(['group-5']);
  });
});
