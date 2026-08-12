/**
 * Shared layout rules for the accounting module tables.
 *
 * Why this exists: every table used to size its columns by splitting the
 * available width between them, so a one-character "Día" got as much room as a
 * name. Widths now come from what a column actually shows, the slack is shared
 * out in proportion to that, and the density is one standard instead of
 * per-component guesswork.
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
 * Cap for the name column's content, so one outlier concept cannot widen the
 * whole table. It lives on an inner <span> and not on the cell because auto
 * table layout ignores max-width on a <td>; bounding the content is what bounds
 * the column's max-content contribution. Longer values wrap — nothing is cut.
 */
const NAME_CONTENT_CLASS = 'block max-w-[22rem]';

/**
 * Page ceiling: past 1400px a wider page is not a more readable one. It lives
 * on each accounting page's root — not on the table — so on a wide monitor the
 * whole page (KPIs, filters, table) centres as one column and the slack reads
 * as page margin, never as empty bands inside the table's card.
 */
export const PAGE_MAX_WIDTH = 'max-w-[87.5rem] mx-auto';

/**
 * Width vocabulary.
 *
 * `track` feeds grid-template-columns as `minmax(max-content, <weight>fr)`: the
 * content is the floor, so nothing is ever clipped, and the flexible max shares
 * the leftover width out in proportion to `weight`. `width` is the same intent
 * for the <col>-less table, resolved in resolveColumns() to a percentage of the
 * total weight — auto layout honours that proportion but still grows a column
 * whose content overflows, which is why we do not use table-fixed: a clipped
 * "$1.200.000…" defeats the point of the table.
 *
 * `weight` doubles as `rem`, the floor minWidthFor() sums before the wrapper
 * starts scrolling: a column's share of the slack tracks how much room its
 * content needs, which is why "Día" stays narrow while an amount does not.
 */
const SIZES = {
  name: { rem: 10, nowrap: false, contentClass: NAME_CONTENT_CLASS },
  tiny: { rem: 2.75, nowrap: true },
  badge: { rem: 6, nowrap: true },
  // Wide enough for two 28px icon buttons AND the word "Acciones" at text-xs
  // with tracking — at 4rem the header clipped.
  icons: { rem: 5.25, nowrap: true },
  money: { rem: 7, nowrap: true },
  date: { rem: 6, nowrap: true },
  text: { rem: 5, nowrap: true },
  // Fits "100%" plus the one-character "%" header; tiny (2.75) clips it.
  percent: { rem: 3.5, nowrap: true },
};

for (const spec of Object.values(SIZES)) {
  spec.weight = spec.rem;
  spec.track = `minmax(max-content, ${spec.rem}fr)`;
  spec.contentClass = spec.contentClass || '';
}

/** Grid track for the drag handle column, which is not part of `columns`. */
export const HANDLE_TRACK = '1.75rem';
export const HANDLE_PAD = 'pl-4 pr-1 py-1.5';

/**
 * Grid track for the selection checkbox column — same width as the `w-10` cell
 * the classic table gives it, so the two views line up. Like the handle it is
 * not part of `columns`, and taking the first position it inherits the job of
 * the `first:pl-4` in TABLE_DENSITY: the padding lives here instead.
 */
export const SELECT_TRACK = '2.5rem';
export const SELECT_PAD = 'pl-4 pr-1 py-1.5';

export const SIZE_NAMES = Object.keys(SIZES);

/**
 * Infer a size when the column does not declare one, so the nine consuming
 * pages only annotate what the format cannot already tell us.
 */
function inferSize(col) {
  if (col.size && SIZES[col.size]) return col.size;
  if (col.format === 'money') return 'money';
  if (col.format === 'percent') return 'percent';
  if (col.format === 'date') return 'date';
  if (col.format === 'badge') return 'badge';
  if (col.align === 'center') return 'tiny';
  return 'text';
}

export function alignClass(col) {
  const align = col.align
    || (col.format === 'money' || col.format === 'percent' ? 'right' : 'left');
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
 * Every column is sized by its own content and every column takes a share of
 * the slack, proportional to that content. The previous rule promoted a single
 * column to flexible, which did not remove the dead space — it piled all of it
 * into the gap between the name and its first value.
 *
 * `width` is that share as a percentage of the total weight, the actions column
 * included, so the percentages a table hands out add up to 100.
 */
export function resolveColumns(columns = [], { hasActions = true } = {}) {
  const sizes = columns.map(inferSize);
  const totalWeight = sizes.reduce((total, size) => total + SIZES[size].weight, 0)
    + (hasActions ? SIZES.icons.weight : 0);

  return columns.map((col, index) => {
    const size = sizes[index];
    const spec = SIZES[size];
    return {
      ...col,
      size,
      track: spec.track,
      width: totalWeight ? `${((spec.weight / totalWeight) * 100).toFixed(2)}%` : 'auto',
      minRem: spec.rem,
      contentClass: spec.contentClass,
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
export function trackListFor(
  resolved,
  { breakpoint = 'lg', hasHandle = false, hasSelect = false, hasActions = true } = {},
) {
  const tracks = resolved
    .filter((col) => isVisibleAt(col, breakpoint))
    .map((col) => col.track);
  return [
    ...(hasSelect ? [SELECT_TRACK] : []),
    ...(hasHandle ? [HANDLE_TRACK] : []),
    ...tracks,
    ...(hasActions ? [SIZES.icons.track] : []),
  ].join(' ');
}

/**
 * Share of the table's width for the actions column, on the same scale as the
 * data columns so it neither hogs the slack nor gets starved of it. Kept out of
 * `columns` because no page declares it — both components append it themselves.
 */
export function actionsWidthFor(resolved) {
  const total = resolved.reduce((sum, col) => sum + SIZES[col.size].weight, 0)
    + SIZES.icons.weight;
  return `${((SIZES.icons.weight / total) * 100).toFixed(2)}%`;
}

/**
 * Minimum width before the wrapper starts scrolling horizontally: every column
 * at the floor its content needs. Replaces the hardcoded min-w-[600px] /
 * min-w-[1120px], which were guesses. Below this the proportional share would
 * squeeze a column past its content, so the wrapper scrolls instead.
 */
export function minWidthFor(
  resolved,
  { breakpoint = 'lg', hasHandle = false, hasSelect = false, hasActions = true } = {},
) {
  const columnsRem = resolved
    .filter((col) => isVisibleAt(col, breakpoint))
    .reduce((total, col) => total + col.minRem, 0);
  const extras = (hasHandle ? 1.75 : 0)
    + (hasSelect ? 2.5 : 0)
    + (hasActions ? SIZES.icons.rem : 0);
  // No padding term: cell padding lives inside each track, so the floors above
  // already include it. Adding it again inflated the table past its container
  // and forced a horizontal scroll that clipped the last column.
  return `${(columnsRem + extras).toFixed(2)}rem`;
}
