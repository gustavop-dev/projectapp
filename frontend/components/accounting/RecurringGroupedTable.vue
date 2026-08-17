<template>
  <!--
    An ARIA grid of divs rather than a <table>: sortablejs cannot reliably drag
    a <tr>, because the clone it drags is detached from the table and collapses
    to zero width. Roles keep the semantics a table would have given us.
  -->
  <div
    class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm"
    role="table"
    :aria-busy="loading ? 'true' : undefined"
    aria-label="Pagos recurrentes por categoría"
  >
    <p class="sr-only" aria-live="polite">
      {{ loading ? 'Cargando registros...' : `${rowCount} registros en ${groups.length} categorías` }}
    </p>

    <div class="accounting-grid-scroll" :style="{ ...containerVars, ...gridVars }">
      <!-- Header -->
      <div
        role="row"
        class="accounting-grid-row items-end bg-surface-raised text-xs text-text-muted uppercase tracking-wider leading-tight"
      >
        <!-- Must stay in flow to occupy the handle track; sr-only (absolute) on
             the grid item itself shifts every label one track left. -->
        <span v-if="dragEnabled" role="columnheader" :class="HANDLE_PAD"><span class="sr-only">Orden</span></span>
        <span
          v-for="col in resolved"
          :key="col.key"
          role="columnheader"
          :class="[col.headerPadClass, col.alignClass, col.hideGridClass]"
          :aria-sort="headerAriaSort(col)"
        >
          <button
            v-if="col.key === sortColumnKey && sortColumnKey"
            type="button"
            class="inline-flex items-center gap-1 uppercase tracking-wider rounded hover:text-text-default transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
            :class="weightSort ? 'text-text-default' : ''"
            data-testid="recurring-grouped-sort-weight"
            title="Ordenar por peso (vista temporal, no cambia el orden manual)"
            @click="emit('toggle-weight-sort')"
          >
            <span>{{ col.label }}</span>
            <ChevronUpIcon v-if="weightSort === 'asc'" class="w-3 h-3" />
            <ChevronDownIcon v-else-if="weightSort === 'desc'" class="w-3 h-3" />
            <span v-else aria-hidden="true">
              <ChevronUpDownIcon class="w-3 h-3 text-text-subtle" />
            </span>
          </button>
          <template v-else>{{ col.label }}</template>
        </span>
        <span role="columnheader" :class="[DENSITY.headerCell, 'text-center']">Acciones</span>
      </div>

      <!-- Skeleton -->
      <div v-if="showSkeleton" class="accounting-grid-band divide-y divide-border-muted">
        <div
          v-for="n in skeletonRows"
          :key="`skeleton-${n}`"
          class="px-4 py-1.5 min-h-9 flex items-center bg-surface"
          data-testid="accounting-skeleton-row"
        >
          <div class="h-3 w-32 rounded bg-surface-raised motion-safe:animate-pulse" />
        </div>
      </div>

      <template v-else>
        <div v-for="group in localGroups" :key="group.id" role="rowgroup" class="accounting-grid-subgrid">
          <!-- Group header -->
          <!-- Totals row with the figures grouped next to the name; see
               IncomeGroupedTable for why they are not spread across the row. -->
          <div
            role="row"
            class="accounting-grid-band accounting-group-header bg-surface-raised border-y border-border-muted px-4 py-2"
            :data-testid="`recurring-group-${group.id}`"
          >
            <!-- min-w-0 down the chain is what lets a long category name
                 ellipsize instead of pushing the figures out of the row. -->
            <button
              type="button"
              role="columnheader"
              class="inline-flex items-center gap-2 min-w-0 text-sm font-medium text-text-default rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              :aria-expanded="!isCollapsed(group.id)"
              :aria-controls="`recurring-group-body-${group.id}`"
              :data-testid="`recurring-group-toggle-${group.id}`"
              @click="emit('toggle-group', group.id)"
            >
              <ChevronDownIcon
                class="w-4 h-4 flex-shrink-0 text-text-subtle transition-transform"
                :class="isCollapsed(group.id) ? '-rotate-90' : ''"
              />
              <span class="truncate">{{ group.name }}</span>
              <span class="text-xs text-text-subtle font-normal">({{ group.rows.length }})</span>
            </button>
            <div class="text-xs leading-tight whitespace-nowrap">
              <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
                Mensual
              </span>
              <span
                class="block font-medium tabular-nums text-text-muted"
                :data-testid="`recurring-group-total-${group.id}`"
              >{{ formatMonthlyCop(group.monthlyCopTotal) }}</span>
            </div>
            <div
              v-if="group.groupWeightPct != null"
              class="text-xs leading-tight whitespace-nowrap"
            >
              <!-- The share OF the active payments, not how much of this group
                   is active — same wording fix as the incomes header. -->
              <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
                Participación en pagos activos
              </span>
              <span
                class="block font-medium tabular-nums text-text-muted"
                :data-testid="`recurring-group-weight-${group.id}`"
              >{{ formatPercent(group.groupWeightPct) }}</span>
            </div>
          </div>

          <!-- Rows -->
          <draggable
            v-show="!isCollapsed(group.id)"
            :id="`recurring-group-body-${group.id}`"
            v-model="group.rows"
            tag="div"
            class="accounting-grid-subgrid divide-y divide-border-muted"
            item-key="id"
            handle=".recurring-drag-handle"
            ghost-class="opacity-30"
            :group="{ name: 'recurring' }"
            :disabled="!dragEnabled"
            @end="onDragEnd"
          >
            <template #item="{ element: row }">
              <div
                role="row"
                :data-testid="`accounting-row-${row.id}`"
                class="accounting-grid-row items-center min-h-9 bg-surface hover:bg-surface-raised transition-colors text-sm"
                :class="row.id === highlightId ? 'accounting-row-flash' : ''"
              >
                <span v-if="dragEnabled" role="cell" :class="HANDLE_PAD">
                  <span
                    class="recurring-drag-handle cursor-grab select-none text-text-subtle"
                    :data-testid="`recurring-drag-handle-${row.id}`"
                    title="Arrastra para reordenar"
                  >⠿</span>
                </span>
                <span
                  v-for="col in resolved"
                  :key="col.key"
                  role="cell"
                  class="min-w-0"
                  :class="cellClass(col)"
                >
                  <!-- Caps the name column's content so one long value cannot
                       widen its track past the rest of the table. -->
                  <span :class="col.contentClass">
                    <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                      <template v-if="col.format === 'money'">
                        {{ formatMoney(row[col.key], 'COP') }}
                      </template>
                      <HighlightText
                        v-else-if="highlightQuery"
                        :text="row[col.key] ?? ''"
                        :query="highlightQuery"
                      />
                      <template v-else>{{ row[col.key] }}</template>
                    </slot>
                  </span>
                </span>
                <span role="cell" :class="[DENSITY.cell, 'text-center whitespace-nowrap']">
                  <button
                    type="button"
                    aria-label="Editar"
                    :data-testid="`accounting-edit-${row.id}`"
                    class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
                    @click.stop="emit('edit', row)"
                  >
                    <PencilSquareIcon class="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    aria-label="Eliminar"
                    :data-testid="`accounting-delete-${row.id}`"
                    class="p-1.5 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
                    @click.stop="emit('delete', row)"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </span>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Grand total: same layout as the group headers, so the whole table
             reads the same way — label first, figure grouped right after it. -->
        <div
          role="row"
          class="accounting-grid-band accounting-group-header bg-surface-raised border-t-2 border-border-muted px-4 py-2"
        >
          <span role="cell" class="text-xs uppercase tracking-wider text-text-muted">
            Total mensual (COP)
          </span>
          <div role="cell" class="text-xs leading-tight whitespace-nowrap">
            <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
              Mensual
            </span>
            <span
              class="block text-sm font-medium tabular-nums text-text-default"
              data-testid="recurring-monthly-grand-total"
            >{{ formatMonthlyCop(grandTotal) }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import {
  ChevronDownIcon,
  ChevronUpDownIcon,
  ChevronUpIcon,
  PencilSquareIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';
import HighlightText from '~/components/ui/HighlightText.vue';
import { formatMoney } from '~/utils/formatMoney';
import { formatPercent } from '~/utils/percent';
import { formatMonthlyCop, UNCATEGORIZED_KEY } from '~/utils/recurring';
import {
  HANDLE_PAD,
  TABLE_DENSITY,
  minWidthFor,
  resolveColumns,
  trackListFor,
} from '~/utils/tableLayout';

const props = defineProps({
  /** Same column config shape as AccountingTable ({ key, label, format, align, size, group, hideBelow }). */
  columns: { type: Array, required: true },
  /** [{ id, name, rows, monthlyCopTotal }] — already ordered and subtotaled. */
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  skeletonRows: { type: Number, default: 5 },
  highlightId: { type: [String, Number], default: null },
  highlightQuery: { type: String, default: '' },
  /** Drag handles only render when reordering is meaningful (no active filter). */
  dragEnabled: { type: Boolean, default: false },
  /** Ids of the collapsed groups. */
  collapsedIds: { type: Array, default: () => [] },
  /**
   * Column whose header toggles the temporary weight sort (emits
   * 'toggle-weight-sort'); empty disables the affordance. Kept as a prop so
   * the component stays agnostic of which field means "weight".
   */
  sortColumnKey: { type: String, default: '' },
  /** Current weight-sort state, controlled by the page: '' | 'asc' | 'desc'. */
  weightSort: { type: String, default: '' },
});

const emit = defineEmits(['edit', 'delete', 'reorder', 'toggle-group', 'toggle-weight-sort']);

function headerAriaSort(col) {
  if (col.key !== props.sortColumnKey) return undefined;
  if (!props.weightSort) return 'none';
  return props.weightSort === 'desc' ? 'descending' : 'ascending';
}

/**
 * Mutable mirror of `groups`: vuedraggable has to own the arrays it reorders.
 * Rebuilt whenever the page pushes new groups, which is also how a failed
 * reorder snaps the row back — the store restores the old order, the prop
 * changes, and the mirror follows.
 */
const localGroups = ref([]);

watch(
  () => props.groups,
  (groups) => {
    localGroups.value = groups.map((group) => ({ ...group, rows: [...group.rows] }));
  },
  { immediate: true, deep: true },
);

const DENSITY = TABLE_DENSITY;

/** Widths by content, slack shared in proportion — see utils/tableLayout. */
const resolved = computed(() => resolveColumns(props.columns));

/**
 * Header, rows and the drag handle must line up, so every row shares one track
 * list. CSS cannot drop a track from grid-template-columns, so each breakpoint
 * gets its own list as a custom property and a media query picks between them.
 * Doing it in CSS rather than a JS breakpoint watcher keeps SSR and the client
 * rendering the same markup.
 */
const gridVars = computed(() => {
  const opts = { hasHandle: props.dragEnabled, hasActions: true };
  return {
    '--cols-base': trackListFor(resolved.value, { ...opts, breakpoint: 'base' }),
    '--cols-md': trackListFor(resolved.value, { ...opts, breakpoint: 'md' }),
    '--cols-lg': trackListFor(resolved.value, { ...opts, breakpoint: 'lg' }),
  };
});

const containerVars = computed(() => {
  const opts = { hasHandle: props.dragEnabled, hasActions: true };
  return {
    '--minw-base': minWidthFor(resolved.value, { ...opts, breakpoint: 'base' }),
    '--minw-md': minWidthFor(resolved.value, { ...opts, breakpoint: 'md' }),
    '--minw-lg': minWidthFor(resolved.value, { ...opts, breakpoint: 'lg' }),
  };
});

const rowCount = computed(
  () => props.groups.reduce((total, group) => total + group.rows.length, 0),
);

/**
 * Skeleton only when there is nothing to show yet, like the other accounting
 * tables: a refetch over rows already on screen updates them in place instead
 * of blanking the grid. `aria-busy` still announces the fetch.
 */
const showSkeleton = computed(() => props.loading && props.groups.length === 0);

const grandTotal = computed(
  () => props.groups.reduce((total, group) => total + (group.monthlyCopTotal || 0), 0),
);

function isCollapsed(id) {
  return props.collapsedIds.includes(id);
}

/** `col` is already resolved, so alignment, padding and visibility come precomputed. */
function cellClass(col) {
  const classes = [col.padClass, col.alignClass, col.hideGridClass];
  // Amounts must never wrap or clip; free text may truncate.
  if (col.format === 'money' || col.align === 'right') {
    classes.push('tabular-nums whitespace-nowrap');
    classes.push(col.format === 'money' ? 'text-text-muted' : 'text-text-default');
  } else {
    classes.push('truncate text-text-default');
  }
  return classes;
}

/**
 * Emit the whole board once, after the drag settles.
 *
 * `end` fires a single time per drag, and by then vuedraggable has already
 * mutated both the source and the target list — so a cross-group move is just
 * another state to read off `localGroups`, with no double emit to dedupe.
 */
function onDragEnd() {
  const items = localGroups.value.flatMap((group) =>
    group.rows.map((row, index) => ({
      id: row.id,
      // The uncategorized bucket is a UI-only group; it maps back to null.
      category: group.id === UNCATEGORIZED_KEY ? null : group.id,
      order: index,
    })),
  );
  emit('reorder', items);
}
</script>

<style scoped>
/* ONE grid for the whole table. Every row used to carry its own
 * grid-template-columns, which sizes each row against its OWN cells: the single
 * row paying by "Efectivo" resolved a wider track than the rows paying by "T.C"
 * and drifted out of column. Now the container owns the tracks and every band,
 * group and row is a subgrid of it, so a column is measured once across all the
 * rows — header included — and an outlier only fills its own cell.
 *
 * The variants come in as custom properties because a media query can switch
 * between values but cannot compute a track list from the column config; --cols
 * is the indirection that keeps that switch in one place. */
.accounting-grid-scroll {
  --cols: var(--cols-base);
  min-width: var(--minw-base);
}
@media (min-width: 768px) {
  .accounting-grid-scroll {
    --cols: var(--cols-md);
    min-width: var(--minw-md);
  }
}
@media (min-width: 1024px) {
  .accounting-grid-scroll {
    --cols: var(--cols-lg);
    min-width: var(--minw-lg);
  }
}

/* The width ceiling lives on the page root (PAGE_MAX_WIDTH), so the grid fills
 * its card and the fr tracks share the slack; min-width still makes a narrow
 * screen scroll instead of squeezing a column past its content. */
.accounting-grid-scroll {
  display: grid;
  grid-template-columns: var(--cols);
}

/* Rowgroups and the draggable list are transparent for track sizing: without
 * them in the chain the rows stop seeing the container's columns. Rows keep
 * their box (unlike display:contents) because sortablejs drags them by their
 * rect, and the hover, flash and divider all need something to paint on. */
.accounting-grid-subgrid,
.accounting-grid-row {
  display: grid;
  grid-column: 1 / -1;
  /* Fallback first: where subgrid is missing the declaration is dropped and the
   * inherited track list stands, which is the previous behaviour — a degraded
   * alignment beats every cell collapsing into a single column. */
  grid-template-columns: var(--cols);
  grid-template-columns: subgrid;
}

/* Bands are not column-structured: they span the grid instead of pushing any
 * single column (category header, monthly total, loading skeleton). */
.accounting-grid-band {
  grid-column: 1 / -1;
}

/* Group header and footer as totals rows — duplicated with IncomeGroupedTable
 * for the same reason the grid CSS above already is (see its file header), and
 * that file carries the argument for grouping the figures next to the name
 * instead of spreading them across the row. */
.accounting-group-header {
  display: flex;
  flex-wrap: wrap;
  /* Name is one line, figure blocks are two: centre it against the block. */
  align-items: center;
  column-gap: 1.25rem;
  row-gap: 0.25rem;
  /* Zero width so the band contributes nothing to the columns' track sizing,
   * min-width to stretch it back over them: otherwise the longest category
   * name widens the whole table and `truncate` never engages. See
   * IncomeGroupedTable for the measurements. */
  width: 0;
  min-width: 100%;
}

/* Below sm the name owns its line and the figures ride together on the next. */
.accounting-group-header > :first-child {
  flex: 0 1 100%;
  min-width: 0;
}

/* Amounts never compress: the name is what yields. */
.accounting-group-header > :not(:first-child) {
  flex: 0 0 auto;
}

@media (min-width: 640px) {
  /* One line from sm up: wrapping would push the figures down instead of
   * making the name yield to them — see IncomeGroupedTable. */
  .accounting-group-header {
    flex-wrap: nowrap;
  }
  .accounting-group-header > :first-child {
    flex: 0 1 auto;
  }
}

/* Same feedback flash as AccountingTable for the row just created or edited. */
@keyframes accounting-row-flash {
  0%,
  55% {
    background-color: var(--color-primary-soft);
  }
  100% {
    background-color: transparent;
  }
}
.accounting-row-flash {
  animation: accounting-row-flash 2.5s ease-out;
}
@media (prefers-reduced-motion: reduce) {
  .accounting-row-flash {
    animation: none;
    background-color: var(--color-primary-soft);
  }
}
</style>
