/**
 * Shared-band form rows.
 *
 * A `BaseFormRow` declares three bands — label / control / error — and every
 * `BaseFormField` inside it becomes a subgrid that inherits them. Each band is
 * then as tall as the tallest cell in the row, so the controls all start at the
 * same height. Without this every field stacks on its own and a label that
 * wraps to two lines pushes down only its own control, leaving the row crooked.
 * Explanatory help belongs to the row and spans every column underneath the
 * group; it is deliberately not a fourth per-field band.
 *
 * The class strings are spelled out per breakpoint instead of being built by
 * interpolation: the JIT scans these files as plain text, so a `${at}:grid-cols-2`
 * would be purged. Same reason `utils/` is listed in the tailwind content globs.
 */

/**
 * Provided by `BaseFormRow`: the breakpoint at which the bands kick
 * in, or `null` when the row is a single column and there is nothing to align.
 */
export const FORM_ROW_ALIGN = Symbol('formRowAlign')

export const ROW_GAP = {
  2: 'gap-2',
  3: 'gap-3',
  4: 'gap-4',
  6: 'gap-6',
}

export const ROW_COLS = {
  sm: { 1: '', 2: 'sm:grid-cols-2', 3: 'sm:grid-cols-3', 4: 'sm:grid-cols-4' },
  md: { 1: '', 2: 'md:grid-cols-2', 3: 'md:grid-cols-3', 4: 'md:grid-cols-4' },
  portrait: {
    1: '',
    2: 'panel-portrait:grid-cols-2',
    3: 'panel-portrait:grid-cols-3',
    4: 'panel-portrait:grid-cols-4',
  },
  landscape: {
    1: '',
    2: 'panel-landscape:grid-cols-2',
    3: 'panel-landscape:grid-cols-3',
    4: 'panel-landscape:grid-cols-4',
  },
}

/** Optional second step, for the filter bars that widen again on large screens. */
export const ROW_COLS_LG = {
  0: '',
  2: 'lg:grid-cols-2',
  3: 'lg:grid-cols-3',
  4: 'lg:grid-cols-4',
  5: 'lg:grid-cols-5',
  6: 'lg:grid-cols-6',
}

/** A field followed by a compact companion action (picker + “Sin proyecto”). */
export const ROW_FIELD_ACTION = {
  sm: 'sm:grid-cols-[minmax(0,1fr)_auto]',
  md: 'md:grid-cols-[minmax(0,1fr)_auto]',
  portrait: 'panel-portrait:grid-cols-[minmax(0,1fr)_auto]',
  landscape: 'panel-landscape:grid-cols-[minmax(0,1fr)_auto]',
}

/**
 * The three bands. Only the track list — the row keeps its normal `gap`, which
 * is what separates one line of fields from the next when a grid holds more
 * fields than it has columns.
 */
export const ROW_BANDS = {
  sm: 'sm:grid-rows-[auto_auto_auto]',
  md: 'md:grid-rows-[auto_auto_auto]',
  portrait: 'panel-portrait:grid-rows-[auto_auto_auto]',
  landscape: 'panel-landscape:grid-rows-[auto_auto_auto]',
}

/**
 * `gap-y-0` here, not on the row: a subgrid inherits its parent's gutters but
 * may override them, so zeroing it on the field keeps the label glued to its
 * control (the 4px comes from `mb-1`) while the row's own row-gap still spaces
 * wrapped lines of fields apart. Verified in Chromium — inheriting instead
 * would push label and control 20px apart.
 *
 * Fallback first, like `.accounting-grid-subgrid` in IncomeGroupedTable: where
 * `subgrid` is missing the declaration is dropped, the field stays a plain grid
 * with implicit rows and renders exactly as it does today — alignment degrades,
 * nothing breaks.
 */
export const FIELD_ALIGNED = {
  sm: 'sm:grid sm:grid-rows-subgrid sm:row-span-3 sm:gap-y-0',
  md: 'md:grid md:grid-rows-subgrid md:row-span-3 md:gap-y-0',
  portrait: 'panel-portrait:grid panel-portrait:grid-rows-subgrid panel-portrait:row-span-3 panel-portrait:gap-y-0',
  landscape: 'panel-landscape:grid panel-landscape:grid-rows-subgrid panel-landscape:row-span-3 panel-landscape:gap-y-0',
}

/**
 * `contents` keeps the wrapper out of the box tree, so a field outside a row
 * renders exactly as it did before the bands existed. Inside a row, and only
 * from the breakpoint up, it becomes a real band cell.
 */
export const FIELD_CELL = {
  sm: 'contents sm:block',
  md: 'contents md:block',
  portrait: 'contents panel-portrait:block',
  landscape: 'contents panel-landscape:block',
}
