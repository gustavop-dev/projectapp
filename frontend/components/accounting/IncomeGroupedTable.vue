<template>
  <!--
    Same ARIA grid of divs as RecurringGroupedTable, kept as a sibling on
    purpose: that component owes its div markup (and its mutable group
    mirror) to vuedraggable, which incomes do not need — grafting income
    subtotals and row actions onto it would couple two tables that only
    share the shell. The subgrid CSS is duplicated with it.
  -->
  <div
    class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm"
    role="table"
    :aria-busy="loading ? 'true' : undefined"
    aria-label="Ingresos por cliente"
  >
    <p class="sr-only" aria-live="polite">
      {{ loading ? 'Cargando registros...' : `${rowCount} registros en ${groups.length} clientes` }}
    </p>

    <div class="accounting-grid-scroll" :style="{ ...containerVars, ...gridVars }">
      <!-- Header -->
      <div
        role="row"
        class="accounting-grid-row items-end bg-surface-raised text-xs text-text-muted uppercase tracking-wider leading-tight"
      >
        <!-- Must stay in flow to occupy the selection track; without the cell
             every label would shift one track left. The grouped view never
             paginates, so this covers the whole filtered set. -->
        <span v-if="selectable" role="columnheader" :class="SELECT_PAD">
          <input
            type="checkbox"
            class="align-middle accent-primary"
            aria-label="Seleccionar todos los ingresos filtrados"
            data-testid="accounting-select-all"
            :checked="allSummary.all"
            :indeterminate.prop="allSummary.some && !allSummary.all"
            @change="toggleAll($event.target.checked)"
          >
        </span>
        <span
          v-for="col in resolved"
          :key="col.key"
          role="columnheader"
          :class="[col.headerPadClass, col.alignClass, responsiveGridCellClass(col)]"
        >
          {{ col.label }}
        </span>
        <span v-if="showActions" role="columnheader" :class="[DENSITY.headerCell, 'text-center']">Acciones</span>
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
        <div v-for="group in groups" :key="group.id" role="rowgroup" class="accounting-grid-subgrid">
          <!-- Group header -->
          <!--
            This row IS the group's totals row, but its figures are facts about
            the client they follow, so they sit CONTIGUOUS to the name at the
            start of the band. Spreading them over the row's width was tried and
            rejected: on a wide table the amounts landed so far from the name
            that they read as columns of something else again. Below sm they
            drop together to a second line under the name rather than wrapping
            mid amount.
          -->
          <div
            role="row"
            class="accounting-grid-band accounting-group-header bg-surface-raised border-y border-border-muted px-4 py-2"
            :data-testid="`income-group-${group.id}`"
          >
            <div class="flex items-center gap-2 min-w-0">
              <!-- Sibling of the toggle, never inside it: a checkbox nested in
                   a <button> is invalid, and its click would collapse the
                   group instead of selecting it. -->
              <input
                v-if="selectable"
                type="checkbox"
                class="align-middle accent-primary flex-shrink-0"
                :aria-label="`Seleccionar los ${group.count} ingresos de ${group.name}`"
                :data-testid="`income-group-select-${group.id}`"
                :checked="groupSummary(group.id).all"
                :indeterminate.prop="groupSummary(group.id).some && !groupSummary(group.id).all"
                @change="toggleGroupSelection(group, $event.target.checked)"
              >
              <button
                type="button"
                role="columnheader"
                class="inline-flex items-center gap-2 min-w-0 text-sm font-medium text-text-default rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
                :aria-expanded="!isCollapsed(group.id)"
                :aria-controls="`income-group-body-${group.id}`"
                :data-testid="`income-group-toggle-${group.id}`"
                @click="emit('toggle-group', group.id)"
              >
                <ChevronDownIcon
                  class="w-4 h-4 flex-shrink-0 text-text-subtle transition-transform"
                  :class="isCollapsed(group.id) ? '-rotate-90' : ''"
                />
                <span class="truncate">{{ group.name }}</span>
                <span
                  v-if="group.id === NO_CLIENT_KEY"
                  class="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-warning-soft text-warning-strong whitespace-nowrap"
                >
                  por completar
                </span>
                <span class="text-xs text-text-subtle font-normal">({{ group.count }})</span>
              </button>
              <!-- A collapsed group still counts towards the bulk action, so
                   it has to say how much of it is selected — otherwise the
                   confirmation lists rows the operator cannot see. -->
              <span
                v-if="selectable && isCollapsed(group.id) && groupSummary(group.id).count > 0"
                class="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-primary-soft text-text-brand whitespace-nowrap"
                :data-testid="`income-group-selected-${group.id}`"
              >
                {{ groupSummary(group.id).count }}
                seleccionado{{ groupSummary(group.id).count === 1 ? '' : 's' }}
              </span>
            </div>
            <!--
              Both amounts always render, zero included, so every group states
              the same facts in the same order — the footer row and the totals
              modal already spell out their zeros.

              Each figure is its own block with the label above the value —
              that two-line shape is what made the row legible, and it is also
              what removes the need for separators between the blocks: the gap
              alone tells them apart, so the middots that used to chain them
              into one sentence are gone. The labels borrow the column headers'
              own formula (uppercase, tracked, subtle) because that is what
              makes the row read as totals and not as decoration.
            -->
            <div class="text-xs leading-tight whitespace-nowrap">
              <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
                Facturado
              </span>
              <span
                class="block font-medium tabular-nums text-text-muted"
                :data-testid="`income-group-billed-${group.id}`"
              >{{ money(group.billed) }}</span>
            </div>
            <div class="text-xs leading-tight whitespace-nowrap">
              <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
                Pendiente
              </span>
              <span
                class="block font-medium tabular-nums text-warning-strong"
                :data-testid="`income-group-pending-${group.id}`"
              >{{ money(group.pending) }}</span>
            </div>
            <!-- The label states what the figure actually is: the group's share
                 OF the billed total (weightPct = group billed / Σ billed). "% de
                 lo facturado" also read as "how much of this group is billed",
                 which is a different question and not the one answered here. -->
            <div v-if="group.weightPct != null" class="text-xs leading-tight whitespace-nowrap">
              <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
                Participación en lo facturado
              </span>
              <span
                class="block font-medium tabular-nums text-text-muted"
                :data-testid="`income-group-weight-${group.id}`"
              >{{ formatPercent(group.weightPct) }}</span>
            </div>
          </div>

          <!-- Rows -->
          <div
            v-show="!isCollapsed(group.id)"
            :id="`income-group-body-${group.id}`"
            class="accounting-grid-subgrid divide-y divide-border-muted"
          >
            <div
              v-for="row in group.rows"
              :key="row.id"
              role="row"
              :data-testid="`accounting-row-${row.id}`"
              class="accounting-grid-row items-center min-h-9 bg-surface hover:bg-surface-raised transition-colors text-sm"
              :class="row.id === highlightId ? 'accounting-row-flash' : ''"
            >
              <span v-if="selectable" role="cell" :class="SELECT_PAD">
                <input
                  type="checkbox"
                  class="align-middle accent-primary"
                  :aria-label="`Seleccionar fila ${row.id}`"
                  :data-testid="`accounting-select-${row.id}`"
                  :checked="selectedSet.has(row.id)"
                  @change="toggleRow(row.id, $event.target.checked)"
                >
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
                <div :class="col.contentClass">
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

                  <dl
                    v-if="col.responsive?.primary && groupedColumns.compact.length"
                    class="mt-2 space-y-1 panel-portrait:hidden"
                    data-testid="responsive-group-compact"
                  >
                    <div
                      v-for="detail in groupedColumns.compact"
                      :key="detail.key"
                      class="grid grid-cols-[minmax(5.5rem,auto)_1fr] gap-2 text-left text-xs"
                    >
                      <dt class="font-medium text-text-subtle">{{ detail.label }}</dt>
                      <dd class="min-w-0 text-text-muted">
                        <slot :name="`cell-${detail.key}`" :row="row" :value="row[detail.key]">
                          {{ formatGroupedValue(detail, row[detail.key]) }}
                        </slot>
                      </dd>
                    </div>
                  </dl>

                  <dl
                    v-if="col.responsive?.primary && groupedColumns.portrait.length"
                    class="mt-2 hidden space-y-1 panel-portrait:block panel-landscape:hidden"
                    data-testid="responsive-group-portrait"
                  >
                    <div
                      v-for="detail in groupedColumns.portrait"
                      :key="detail.key"
                      class="grid grid-cols-[minmax(6rem,auto)_1fr] gap-2 text-left text-xs"
                    >
                      <dt class="font-medium text-text-subtle">{{ detail.label }}</dt>
                      <dd class="min-w-0 text-text-muted">
                        <slot :name="`cell-${detail.key}`" :row="row" :value="row[detail.key]">
                          {{ formatGroupedValue(detail, row[detail.key]) }}
                        </slot>
                      </dd>
                    </div>
                  </dl>

                  <dl
                    v-if="col.responsive?.primary && groupedColumns.landscape.length"
                    class="mt-2 hidden space-y-1 panel-landscape:block panel-desktop:hidden"
                    data-testid="responsive-group-landscape"
                  >
                    <div
                      v-for="detail in groupedColumns.landscape"
                      :key="detail.key"
                      class="grid grid-cols-[minmax(6rem,auto)_1fr] gap-2 text-left text-xs"
                    >
                      <dt class="font-medium text-text-subtle">{{ detail.label }}</dt>
                      <dd class="min-w-0 text-text-muted">
                        <slot :name="`cell-${detail.key}`" :row="row" :value="row[detail.key]">
                          {{ formatGroupedValue(detail, row[detail.key]) }}
                        </slot>
                      </dd>
                    </div>
                  </dl>
                </div>
              </span>
              <span v-if="showActions" role="cell" :class="[DENSITY.cell, 'text-center whitespace-nowrap']">
                <slot name="row-actions" :row="row" />
                <template>
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
                </template>
              </span>
            </div>
          </div>
        </div>

        <!-- Grand totals: billed vs collected are separate ledger rows, so
             they read side by side instead of summing into one number.

             Shares the group headers' layout, so the whole table reads the same
             way top to bottom: the label first and the figures grouped right
             after it. Pendiente keeps coming before Cobrado because those first
             two are the columns the groups also carry, and Cobrado — which has
             no group-level counterpart — closes the set. -->
        <div
          role="row"
          class="accounting-grid-band accounting-group-header bg-surface-raised border-t-2 border-border-muted px-4 py-2"
        >
          <span role="cell" class="text-xs uppercase tracking-wider text-text-muted">
            Total del conjunto filtrado
          </span>
          <div role="cell" class="text-xs leading-tight whitespace-nowrap">
            <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
              Facturado
            </span>
            <span
              class="block text-sm font-medium tabular-nums text-text-default"
              data-testid="income-grouped-billed-total"
            >{{ money(totals.billed) }}</span>
          </div>
          <div role="cell" class="text-xs leading-tight whitespace-nowrap">
            <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
              Pendiente
            </span>
            <span
              class="block text-sm font-medium tabular-nums text-warning-strong"
              data-testid="income-grouped-pending-total"
            >{{ money(totals.pending) }}</span>
          </div>
          <div role="cell" class="text-xs leading-tight whitespace-nowrap">
            <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
              Cobrado
            </span>
            <span
              class="block text-sm font-medium tabular-nums text-success-strong"
              data-testid="income-grouped-collected-total"
            >{{ money(totals.collected) }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import {
  ChevronDownIcon,
  PencilSquareIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';
import HighlightText from '~/components/ui/HighlightText.vue';
import { formatMoney } from '~/utils/formatMoney';
import { formatPercent } from '~/utils/percent';
import { NO_CLIENT_KEY, sumClientGroups } from '~/utils/incomeClients';
import { selectionSummary, toggleKeys } from '~/utils/rowSelection';
import {
  SELECT_PAD,
  TABLE_DENSITY,
  minWidthFor,
  resolveColumns,
  trackListFor,
} from '~/utils/tableLayout';

const props = defineProps({
  /** Same column contract as AccountingTable, including the explicit
   * responsive priority for compact, portrait and landscape profiles. */
  columns: { type: Array, required: true },
  /** withClientWeights(groupByClient(rows)) — ordered, subtotaled, "Sin cliente" last. */
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  skeletonRows: { type: Number, default: 5 },
  highlightId: { type: [String, Number], default: null },
  highlightQuery: { type: String, default: '' },
  /** Ids of the collapsed groups. */
  collapsedIds: { type: Array, default: () => [] },
  /** Mirrors AccountingTable: false lets the page own every row action. */
  showActions: { type: Boolean, default: true },
  /** Opt-in checkbox column, same contract as AccountingTable. */
  selectable: { type: Boolean, default: false },
  /** Selected row ids (v-model:selected). */
  selected: { type: Array, default: () => [] },
});

const emit = defineEmits(['edit', 'delete', 'toggle-group', 'update:selected']);

const DENSITY = TABLE_DENSITY;

/** Widths by content, slack shared in proportion — see utils/tableLayout. */
const resolved = computed(() => resolveColumns(props.columns));

const PROFILE_ORDER = ['compact', 'portrait', 'landscape'];
const POLICY_CLASSES = {
  compact: { keep: 'block', group: 'hidden', hide: 'hidden' },
  portrait: { keep: 'panel-portrait:block', group: 'panel-portrait:hidden', hide: 'panel-portrait:hidden' },
  landscape: { keep: 'panel-landscape:block', group: 'panel-landscape:hidden', hide: 'panel-landscape:hidden' },
};

function policyFor(column, profile) {
  if (!column.responsive) return 'keep';
  if (column.responsive[profile]) return column.responsive[profile];
  if (profile === 'portrait') return column.responsive.compact || 'keep';
  return 'keep';
}

function responsiveGridCellClass(column) {
  return [
    ...PROFILE_ORDER.map((profile) => POLICY_CLASSES[profile][policyFor(column, profile)]),
    'panel-desktop:block',
  ];
}

const groupedColumns = computed(() => Object.fromEntries(
  PROFILE_ORDER.map((profile) => [
    profile,
    resolved.value.filter((column) => policyFor(column, profile) === 'group'),
  ]),
));

function visibleColumns(profile) {
  return resolved.value
    .filter((column) => policyFor(column, profile) === 'keep')
    .map((column) => (
      column.responsive?.primary
        ? { ...column, track: 'minmax(0, 1fr)' }
        : column
    ));
}

/**
 * Header and rows must line up, so every row shares one track list. CSS
 * cannot drop a track from grid-template-columns, so each breakpoint gets
 * its own list as a custom property and a media query picks between them.
 */
const gridVars = computed(() => {
  const opts = { hasSelect: props.selectable, hasActions: props.showActions, breakpoint: 'lg' };
  return {
    '--cols-compact': trackListFor(visibleColumns('compact'), opts),
    '--cols-portrait': trackListFor(visibleColumns('portrait'), opts),
    '--cols-landscape': trackListFor(visibleColumns('landscape'), opts),
    '--cols-desktop': trackListFor(resolved.value, opts),
  };
});

const containerVars = computed(() => {
  const opts = { hasSelect: props.selectable, hasActions: props.showActions, breakpoint: 'lg' };
  return {
    '--minw-landscape': minWidthFor(visibleColumns('landscape'), opts),
    '--minw-desktop': minWidthFor(resolved.value, opts),
  };
});

const rowCount = computed(
  () => props.groups.reduce((total, group) => total + group.rows.length, 0),
);

/**
 * Skeleton only when there is nothing to show yet. Every mutation refetches,
 * so binding it to `loading` alone blanked the whole grid — groups, counters
 * and the totals row — and brought it back after a delete. `aria-busy` still
 * announces the fetch.
 */
const showSkeleton = computed(() => props.loading && props.groups.length === 0);

const totals = computed(() => sumClientGroups(props.groups));

function money(value) {
  return formatMoney(Number(value) || 0, 'COP');
}

function isCollapsed(id) {
  return props.collapsedIds.includes(id);
}

// ── Row selection (opt-in via `selectable`) ──
//
// The scope of a group checkbox is its own rows and the scope of the header
// one is every group — collapsed included, because a collapsed group keeps
// counting towards the bulk action. `groups` is built from the FILTERED rows
// and this view never paginates, so "all" here means the filtered set.

const selectedSet = computed(() => new Set(props.selected));

const groupSummaries = computed(() => new Map(
  props.groups.map((group) => [
    group.id,
    selectionSummary(group.rows.map((row) => row.id), selectedSet.value),
  ]),
));

const EMPTY_SUMMARY = { count: 0, all: false, some: false };

function groupSummary(id) {
  return groupSummaries.value.get(id) || EMPTY_SUMMARY;
}

const allKeys = computed(
  () => props.groups.flatMap((group) => group.rows.map((row) => row.id)),
);

const allSummary = computed(() => selectionSummary(allKeys.value, selectedSet.value));

function toggleRow(id, checked) {
  emit('update:selected', toggleKeys(props.selected, [id], checked));
}

function toggleGroupSelection(group, checked) {
  const keys = group.rows.map((row) => row.id);
  emit('update:selected', toggleKeys(props.selected, keys, checked));
}

function toggleAll(checked) {
  emit('update:selected', toggleKeys(props.selected, allKeys.value, checked));
}

/** `col` is already resolved, so alignment, padding and visibility come precomputed. */
function cellClass(col) {
  const classes = [col.padClass, col.alignClass, responsiveGridCellClass(col)];
  // Amounts must never wrap or clip; free text may truncate.
  if (col.format === 'money' || col.align === 'right') {
    classes.push('tabular-nums whitespace-nowrap');
    classes.push(col.format === 'money' ? 'text-text-muted' : 'text-text-default');
  } else {
    classes.push('truncate text-text-default');
  }
  return classes;
}

function formatGroupedValue(col, value) {
  if (col.format === 'money') return formatMoney(value, 'COP');
  if (col.format === 'percent') return formatPercent(value);
  return value ?? '—';
}
</script>

<style scoped>
/* ONE grid for the whole table: the container owns the tracks and every band,
 * group and row is a subgrid of it, so a column is measured once across all
 * the rows — header included — and an outlier only fills its own cell.
 *
 * The variants come in as custom properties because a media query can switch
 * between values but cannot compute a track list from the column config;
 * --cols is the indirection that keeps that switch in one place. */
.accounting-grid-scroll {
  --cols: var(--cols-compact);
  min-width: 100%;
}
@media (min-width: 600px) {
  .accounting-grid-scroll {
    --cols: var(--cols-portrait);
    min-width: 100%;
  }
}
@media (min-width: 1000px) {
  .accounting-grid-scroll {
    --cols: var(--cols-landscape);
    min-width: var(--minw-landscape);
  }
}
@media (min-width: 1280px) {
  .accounting-grid-scroll {
    --cols: var(--cols-desktop);
    min-width: var(--minw-desktop);
  }
}

/* The width ceiling lives on the page root (PAGE_MAX_WIDTH), so the grid fills
 * its card and the fr tracks share the slack; min-width still makes a narrow
 * screen scroll instead of squeezing a column past its content. */
.accounting-grid-scroll {
  display: grid;
  grid-template-columns: var(--cols);
}

/* Rowgroups are transparent for track sizing: without them in the chain the
 * rows stop seeing the container's columns. Rows keep their box (unlike
 * display:contents) because the hover, flash and divider need something to
 * paint on. */
.accounting-grid-subgrid,
.accounting-grid-row {
  display: grid;
  grid-column: 1 / -1;
  /* Fallback first: where subgrid is missing the declaration is dropped and
   * the inherited track list stands — a degraded alignment beats every cell
   * collapsing into a single column. */
  grid-template-columns: var(--cols);
  grid-template-columns: subgrid;
}

/* Bands are not column-structured: they span the grid instead of pushing any
 * single column (client header, totals, loading skeleton). */
.accounting-grid-band {
  grid-column: 1 / -1;
}

/* The group header and the footer are totals rows, but their figures belong to
 * the name they follow: they sit CONTIGUOUS to it at the start of the band, not
 * spread to the far edge. Both ends were tried on the real table — pinned apart
 * and spread over weighted tracks — and both put the amounts far enough from the
 * name to read as columns of some other thing. What carries the reading is the
 * two-line block (label over value), not the distance between blocks.
 *
 * Flex and not grid: a grid track list would have to choose a width for the name
 * up front, and the name is the one value that cannot be sized in advance. Here
 * it is the only flexible item (min-width:0 → it ellipsizes) while every figure
 * block keeps its natural width (flex:none), so a long name gives up space
 * instead of pushing a figure out of the row or breaking one in half.
 *
 * The gap is uniform: with each figure carrying its own label there is nothing
 * left for a separator to disambiguate. */
.accounting-group-header {
  display: flex;
  flex-wrap: wrap;
  /* The name is one line and the figure blocks are two: centring keeps it
   * against the block as a whole instead of stranding it up on the label. */
  align-items: center;
  column-gap: 1.25rem;
  row-gap: 0.25rem;
  /* The band spans every column, so track sizing asks it how wide it wants to
   * be — and a flex row answers with the sum of its children, i.e. the full
   * length of the longest client name. That widened the WHOLE table (measured:
   * a 2518px name grew a 1294px grid to 3057px) and, because the band had
   * grown to fit, `truncate` never engaged. Declaring a zero width makes the
   * contribution zero; min-width then stretches the band back over the tracks
   * the COLUMNS sized. The name ellipsizes only when it actually runs out of
   * room, which is what the flex rules below assume. */
  width: 0;
  min-width: 100%;
}

/* Compact and portrait tablet: identity, the two money figures, then share. */
.accounting-group-header > :first-child {
  min-width: 0;
}

/* Amounts never compress: the name is what yields. */
.accounting-group-header > :not(:first-child) {
  flex: 0 0 auto;
}

@media (max-width: 999px) {
  .accounting-group-header {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.5rem 1rem;
    align-items: start;
  }
  .accounting-group-header > :first-child,
  .accounting-group-header > :last-child:nth-child(4) {
    grid-column: 1 / -1;
  }
}

@media (min-width: 1000px) {
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
