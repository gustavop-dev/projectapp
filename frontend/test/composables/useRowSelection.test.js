/**
 * Tests for useRowSelection: the selection reconciles against the records that
 * actually exist, so a deleted row cannot go on being counted by a bulk bar.
 *
 * The source is written directly rather than through a store on purpose — the
 * point of hanging the reconciliation off the DATA is that it fires whatever
 * changed the list, including the handlers that never touch the mutation
 * funnel.
 */
import { nextTick, ref } from 'vue';
import { useRowSelection } from '../../composables/useRowSelection';

function rows(...ids) {
  return ids.map((id) => ({ id, concept: `Ingreso ${id}` }));
}

describe('useRowSelection', () => {
  it('drops the deleted id and keeps the rest of the selection', async () => {
    const source = ref(rows(1, 2, 3));
    const { selectedIds } = useRowSelection(source);
    selectedIds.value = [1, 2, 3];

    source.value = rows(1, 3);
    await nextTick();

    expect(selectedIds.value).toEqual([1, 3]);
  });

  it('empties the selection when the last selected record is deleted', async () => {
    const source = ref(rows(1));
    const { selectedIds } = useRowSelection(source);
    selectedIds.value = [1];

    source.value = [];
    await nextTick();

    // This is what lets the bulk bar hide itself with no reload and no
    // Cancelar: its v-if reads the selection length.
    expect(selectedIds.value).toEqual([]);
  });

  it('leaves the selection untouched when a refetch returns the same ids', async () => {
    const source = ref(rows(1, 2));
    const { selectedIds } = useRowSelection(source);
    selectedIds.value = [1, 2];
    const before = selectedIds.value;

    // Every mutation refetches and reassigns the store array: new identity,
    // same ids. Nothing may move.
    source.value = rows(1, 2);
    await nextTick();

    expect(selectedIds.value).toBe(before);
  });

  it('reconciles on a list change that never went through a mutation handler', async () => {
    // Hostings' changeStatus and saveInline call the store directly and then
    // reload, bypassing runMutation. Anything hooked to that funnel would miss
    // them, which is why this composable watches the records instead.
    const source = ref(rows(1, 2));
    const { selectedIds } = useRowSelection(source);
    selectedIds.value = [1, 2];

    source.value = rows(2);
    await nextTick();

    expect(selectedIds.value).toEqual([2]);
  });

  it('exposes the selection as a Set for per-row membership reads', () => {
    const { selectedIds, selectedSet } = useRowSelection(ref(rows(1, 2)));
    selectedIds.value = [2];

    expect(selectedSet.value.has(2)).toBe(true);
    expect(selectedSet.value.has(1)).toBe(false);
  });

  it('clears the whole selection on demand', () => {
    const { selectedIds, clearSelection } = useRowSelection(ref(rows(1, 2)));
    selectedIds.value = [1, 2];

    clearSelection();

    expect(selectedIds.value).toEqual([]);
  });

  it('drops named ids and leaves the rest — the server-said-they-are-gone path', () => {
    const { selectedIds, dropIds } = useRowSelection(ref(rows(1, 2, 3)));
    selectedIds.value = [1, 2, 3];

    dropIds([2]);

    expect(selectedIds.value).toEqual([1, 3]);
  });

  it('accepts a getter as the source', async () => {
    const source = ref(rows(1, 2));
    const { selectedIds } = useRowSelection(() => source.value);
    selectedIds.value = [1, 2];

    source.value = rows(1);
    await nextTick();

    expect(selectedIds.value).toEqual([1]);
  });

  it('honours a custom identity field', async () => {
    const source = ref([{ uuid: 'a' }, { uuid: 'b' }]);
    const { selectedIds } = useRowSelection(source, { key: 'uuid' });
    selectedIds.value = ['a', 'b'];

    source.value = [{ uuid: 'b' }];
    await nextTick();

    expect(selectedIds.value).toEqual(['b']);
  });
});
