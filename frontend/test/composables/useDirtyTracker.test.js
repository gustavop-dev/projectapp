import { useDirtyTracker } from '~/composables/useDirtyTracker';

describe('useDirtyTracker', () => {
  it('starts clean', () => {
    const t = useDirtyTracker();
    expect(t.hasDirty.value).toBe(false);
    expect(t.isDirty(1)).toBe(false);
  });

  it('tracks per-id dirty flags', () => {
    const t = useDirtyTracker();
    t.setDirty(1, true);
    t.setDirty(2, true);
    expect(t.isDirty(1)).toBe(true);
    expect(t.isDirty(2)).toBe(true);
    expect(t.hasDirty.value).toBe(true);

    t.setDirty(1, false);
    expect(t.isDirty(1)).toBe(false);
    expect(t.hasDirty.value).toBe(true);
  });

  it('clearing removes every flag', () => {
    const t = useDirtyTracker();
    t.setDirty('a', true);
    t.setDirty('b', true);
    t.clear();
    expect(t.hasDirty.value).toBe(false);
    expect(t.dirtyIds.value.size).toBe(0);
  });

  it('is factory-scoped: instances do not share state', () => {
    const a = useDirtyTracker();
    const b = useDirtyTracker();
    a.setDirty(1, true);
    expect(b.hasDirty.value).toBe(false);
  });
});
