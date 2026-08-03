/**
 * Shared layout rules for the accounting module tables.
 *
 * Why this exists: every table used to size its columns by splitting the
 * available width between them, so a one-character "Día" got as much room as a
 * name. Widths now come from what a column actually shows, a single column
 * absorbs the slack, and the density is one standard instead of per-component
 * guesswork.
 *
 * Consumed by AccountingTable.vue (a real <table>) and RecurringGroupedTable.vue
 * (an ARIA grid of divs), which is why every size carries BOTH a grid track and
 * a table width — the two layout engines need different units for the same
 * intent.
 *
 * NOTE: the Tailwind classes below only survive the JIT purge because
 * tailwind.config.js scans ./utils/**. Keep them as plain literals; a class
 * assembled from string concatenation is invisible to the scanner.
 */

/** Row height standard for the module: 2.25rem = 36px. */
export const ROW_MIN_HEIGHT = 'min-h-9';

export const TABLE_DENSITY = {
  /**
   * Header and body share one horizontal rhythm so a column's label always sits
   * over its values. The edge overrides keep the content clear of the card
   * border without paying that padding between every pair of columns.
   */
  headerCell: 'px-2.5 py-2 first:pl-4 last:pr-4',
  cell: 'px-2.5 py-1.5 first:pl-4 last:pr-4',
  row: ROW_MIN_HEIGHT,
  /** Action icons drive the row height, so they shrink with it. */
  actionButton: 'p-1.5',
  actionIcon: 'w-4 h-4',
};

/**
 * Width vocabulary. `track` feeds grid-template-columns; `width` feeds the
 * <col>-less table (auto layout honours a width hint but still grows a column
 * whose content overflows, which is why we do not use table-fixed: a clipped
 * "$1.200.000…" defeats the point of the table).
 */
const SIZES = {
  flex: { track: 'minmax(7rem, 1fr)', width: '100%', rem: 7, nowrap: false },
  tiny: { track: '2.75rem', width: '2.75rem', rem: 2.75, nowrap: true },
  badge: { track: 'minmax(6rem, max-content)', width: '6rem', rem: 6, nowrap: true },
  // Wide enough for two 28px icon buttons AND the word "Acciones" at text-xs
  // with tracking — at 4rem the header clipped.
  icons: { track: '5.25rem', width: '5.25rem', rem: 5.25, nowrap: true },
  // `max-content` above the floor so a long "$789.600 COP" widens its own track
  // instead of spilling into the neighbour; the flex column gives up the room.
  money: { track: 'minmax(7rem, max-content)', width: '7rem', rem: 7, nowrap: true },
  date: { track: 'minmax(6rem, max-content)', width: '6rem', rem: 6, nowrap: true },
  text: { track: 'minmax(5rem, max-content)', width: 'auto', rem: 5, nowrap: true },
};

/** Grid track for the drag handle column, which is not part of `columns`. */
export const HANDLE_TRACK = '1.75rem';
export const HANDLE_PAD = 'pl-4 pr-1 py-1.5';

export const SIZE_NAMES = Object.keys(SIZES);

/**
 * Infer a size when the column does not declare one, so the nine consuming
 * pages only annotate what the format cannot already tell us.
 */
function inferSize(col) {
  if (col.size && SIZES[col.size]) return col.size;
  if (col.format === 'money') return 'money';
  if (col.format === 'date') return 'date';
  if (col.format === 'badge') return 'badge';
  if (col.align === 'center') return 'tiny';
  return 'text';
}

export function alignClass(col) {
  const align = col.align || (col.format === 'money' ? 'right' : 'left');
  if (align === 'right') return 'text-right';
  if (align === 'center') return 'text-center';
  return 'text-left';
}

/**
 * Responsive class maps. Two variants because a <td> that is un-hidden must go
 * back to `display: table-cell`, while a grid item must go back to `block`.
 */
const HIDE_TABLE = {
  md: 'hidden md:table-cell',
  lg: 'hidden lg:table-cell',
};

const HIDE_GRID = {
  md: 'hidden md:block',
  lg: 'hidden lg:block',
};

export function hideClass(col, mode = 'table') {
  if (!col.hideBelow) return '';
  const map = mode === 'grid' ? HIDE_GRID : HIDE_TABLE;
  return map[col.hideBelow] || '';
}

/** Breakpoints a column can survive to, widest-first. */
export const BREAKPOINTS = ['base', 'md', 'lg'];

const VISIBLE_AT = {
  base: (col) => !col.hideBelow,
  md: (col) => col.hideBelow !== 'lg',
  lg: () => true,
};

export function isVisibleAt(col, breakpoint) {
  return (VISIBLE_AT[breakpoint] || VISIBLE_AT.lg)(col);
}

/**
 * Padding for a column given its position inside a `group`.
 *
 * Money columns are variants of one number; spacing them like unrelated columns
 * breaks that reading. Members sit close together and the group as a whole is
 * bracketed by a wider gap, which is also what stops a right-aligned amount
 * header from colliding with the left-aligned label that follows it.
 */
function padClassFor(col, prevCol, nextCol, base) {
  if (!col.group) return base;
  const vertical = base === TABLE_DENSITY.headerCell ? 'py-2' : 'py-1.5';
  const first = !prevCol || prevCol.group !== col.group;
  const last = !nextCol || nextCol.group !== col.group;
  if (first && last) return base;
  if (first) return `pl-6 pr-1.5 ${vertical}`;
  if (last) return `pl-2 pr-6 ${vertical}`;
  return `pl-2 pr-1.5 ${vertical}`;
}

/**
 * Resolve a page's column config into everything both table components need.
 *
 * Guarantees exactly one flexible column: without that, either every column
 * stretches (the bug this fixes) or none does and the table floats in a sea of
 * whitespace on a wide screen.
 */
export function resolveColumns(columns = []) {
  const sizes = columns.map(inferSize);

  let flexIndex = columns.findIndex((col) => col.size === 'flex');
  if (flexIndex === -1) flexIndex = sizes.findIndex((size) => size === 'text');
  if (flexIndex === -1) flexIndex = 0;
  if (sizes.length) sizes[flexIndex] = 'flex';

  return columns.map((col, index) => {
    const size = sizes[index];
    const spec = SIZES[size];
    return {
      ...col,
      size,
      track: spec.track,
      width: spec.width,
      minRem: spec.rem,
      alignClass: alignClass(col),
      nowrapClass: spec.nowrap ? 'whitespace-nowrap' : '',
      headerPadClass: padClassFor(
        col,
        columns[index - 1],
        columns[index + 1],
        TABLE_DENSITY.headerCell,
      ),
      padClass: padClassFor(col, columns[index - 1], columns[index + 1], TABLE_DENSITY.cell),
      hideTableClass: hideClass(col, 'table'),
      hideGridClass: hideClass(col, 'grid'),
    };
  });
}

/**
 * Grid track list at a given breakpoint. Columns hidden at that width are
 * dropped entirely — CSS cannot remove a track, so each breakpoint gets its own
 * template and the component picks between them with a media query.
 */
export function trackListFor(resolved, { breakpoint = 'lg', hasHandle = false, hasActions = true } = {}) {
  const tracks = resolved
    .filter((col) => isVisibleAt(col, breakpoint))
    .map((col) => col.track);
  return [
    ...(hasHandle ? [HANDLE_TRACK] : []),
    ...tracks,
    ...(hasActions ? [SIZES.icons.track] : []),
  ].join(' ');
}

/**
 * Minimum width before the wrapper starts scrolling horizontally: the fixed
 * columns at their real size plus a usable floor for the flexible one. Replaces
 * the hardcoded min-w-[600px] / min-w-[1120px], which were guesses.
 */
export function minWidthFor(resolved, { breakpoint = 'lg', hasHandle = false, hasActions = true } = {}) {
  const columnsRem = resolved
    .filter((col) => isVisibleAt(col, breakpoint))
    .reduce((total, col) => total + col.minRem, 0);
  const extras = (hasHandle ? 1.75 : 0) + (hasActions ? SIZES.icons.rem : 0);
  // No padding term: cell padding lives inside each track, so the floors above
  // already include it. Adding it again inflated the table past its container
  // and forced a horizontal scroll that clipped the last column.
  return `${(columnsRem + extras).toFixed(2)}rem`;
}
