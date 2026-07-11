/**
 * Tests for useTableSort.
 *
 * Covers: the toggle cycle with default and per-column first directions,
 * sortAccessors resolving a display column to its sort field, and the
 * untouched order when no sort is active.
 */
import { computed } from 'vue';
import { useTableSort } from '../../composables/useTableSort';

const ROWS = [
  { id: 1, period_label: 'Enero 2026', period_date: '2026-01-01', total: '300' },
  { id: 2, period_label: 'Marzo 2026', period_date: '2026-03-01', total: '100' },
  { id: 3, period_label: 'Febrero 2026', period_date: '2026-02-01', total: '200' },
];

function makeSort(options = {}) {
  return useTableSort(computed(() => ROWS), options);
}

describe('useTableSort', () => {
  it('returns the original order when no sort is active', () => {
    const sort = makeSort();

    expect(sort.sortedRecords.value.map((r) => r.id)).toEqual([1, 2, 3]);
  });

  it('cycles asc → desc → off by default', () => {
    const sort = makeSort();

    sort.toggleSort('total');
    expect(sort.sortDir.value).toBe('asc');
    expect(sort.sortedRecords.value.map((r) => r.id)).toEqual([2, 3, 1]);

    sort.toggleSort('total');
    expect(sort.sortDir.value).toBe('desc');
    expect(sort.sortedRecords.value.map((r) => r.id)).toEqual([1, 3, 2]);

    sort.toggleSort('total');
    expect(sort.sortKey.value).toBe('');
    expect(sort.sortedRecords.value.map((r) => r.id)).toEqual([1, 2, 3]);
  });

  it('starts descending for columns with a desc sortDefault', () => {
    const sort = makeSort({ sortDefaults: { total: 'desc' } });

    sort.toggleSort('total');
    expect(sort.sortDir.value).toBe('desc');
    expect(sort.sortedRecords.value.map((r) => r.id)).toEqual([1, 3, 2]);

    sort.toggleSort('total');
    expect(sort.sortDir.value).toBe('asc');

    sort.toggleSort('total');
    expect(sort.sortKey.value).toBe('');
  });

  it('sorts by the accessor field instead of the display column', () => {
    const sort = makeSort({
      sortAccessors: { period_label: 'period_date' },
      sortDefaults: { period_label: 'desc' },
    });

    sort.toggleSort('period_label');

    // Newest month first — by ISO date, not by the localized label text.
    expect(sort.sortedRecords.value.map((r) => r.period_label)).toEqual([
      'Marzo 2026',
      'Febrero 2026',
      'Enero 2026',
    ]);
  });
});
