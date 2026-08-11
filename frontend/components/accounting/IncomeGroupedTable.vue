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
        <span
          v-for="col in resolved"
          :key="col.key"
          role="columnheader"
          :class="[col.headerPadClass, col.alignClass, col.hideGridClass]"
        >
          {{ col.label }}
        </span>
        <span role="columnheader" :class="[DENSITY.headerCell, 'text-center']">Acciones</span>
      </div>

      <!-- Skeleton -->
      <div v-if="loading" class="accounting-grid-band divide-y divide-border-muted">
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
          <div
            role="row"
            class="accounting-grid-band flex items-center justify-between gap-3 bg-surface-raised border-y border-border-muted px-4 py-2"
            :data-testid="`income-group-${group.id}`"
          >
            <button
              type="button"
              role="columnheader"
              class="inline-flex items-center gap-2 text-sm font-medium text-text-default rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              :aria-expanded="!isCollapsed(group.id)"
              :aria-controls="`income-group-body-${group.id}`"
              :data-testid="`income-group-toggle-${group.id}`"
              @click="emit('toggle-group', group.id)"
            >
              <ChevronDownIcon
                class="w-4 h-4 text-text-subtle transition-transform"
                :class="isCollapsed(group.id) ? '-rotate-90' : ''"
              />
              <span class="truncate">{{ group.name }}</span>
              <span
                v-if="group.id === NO_CLIENT_KEY"
                class="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-warning-soft text-warning-strong"
              >
                por completar
              </span>
              <span class="text-xs text-text-subtle font-normal">({{ group.count }})</span>
            </button>
            <span class="text-sm tabular-nums text-text-muted whitespace-nowrap">
              <span class="text-xs text-text-subtle">Facturado </span>
              <span :data-testid="`income-group-billed-${group.id}`">
                {{ money(group.billed) }}
              </span>
              <template v-if="group.pending > 0">
                <span class="text-xs text-text-subtle"> · Pendiente </span>
                <span class="text-warning-strong" :data-testid="`income-group-pending-${group.id}`">
                  {{ money(group.pending) }}
                </span>
              </template>
              <span
                v-if="group.weightPct != null"
                class="text-xs text-text-subtle tabular-nums"
                :data-testid="`income-group-weight-${group.id}`"
                title="Peso del cliente sobre el total facturado del conjunto filtrado"
              >
                · {{ formatPercent(group.weightPct) }}
              </span>
            </span>
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
                <slot name="row-actions" :row="row" />
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
          </div>
        </div>

        <!-- Grand totals: billed vs collected are separate ledger rows, so
             they read side by side instead of summing into one number. -->
        <div
          role="row"
          class="accounting-grid-band flex flex-wrap items-center justify-between gap-3 bg-surface-raised border-t-2 border-border-muted px-4 py-2"
        >
          <span role="cell" class="text-xs uppercase tracking-wider text-text-muted">
            Total del conjunto filtrado
          </span>
          <span role="cell" class="text-sm tabular-nums whitespace-nowrap">
            <span class="text-xs text-text-subtle">Facturado </span>
            <span class="font-medium text-text-default" data-testid="income-grouped-billed-total">
              {{ money(totals.billed) }}
            </span>
            <span class="text-xs text-text-subtle"> · Cobrado </span>
            <span class="font-medium text-success-strong" data-testid="income-grouped-collected-total">
              {{ money(totals.collected) }}
            </span>
            <span class="text-xs text-text-subtle"> · Pendiente </span>
            <span class="font-medium text-warning-strong" data-testid="income-grouped-pending-total">
              {{ money(totals.pending) }}
            </span>
          </span>
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
import {
  TABLE_DENSITY,
  minWidthFor,
  resolveColumns,
  trackListFor,
} from '~/utils/tableLayout';

const props = defineProps({
  /** Same column config shape as AccountingTable ({ key, label, format, align, size, group, hideBelow }). */
  columns: { type: Array, required: true },
  /** withClientWeights(groupByClient(rows)) — ordered, subtotaled, "Sin cliente" last. */
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  skeletonRows: { type: Number, default: 5 },
  highlightId: { type: [String, Number], default: null },
  highlightQuery: { type: String, default: '' },
  /** Ids of the collapsed groups. */
  collapsedIds: { type: Array, default: () => [] },
});

const emit = defineEmits(['edit', 'delete', 'toggle-group']);

const DENSITY = TABLE_DENSITY;

/** Widths by content, slack shared in proportion — see utils/tableLayout. */
const resolved = computed(() => resolveColumns(props.columns));

/**
 * Header and rows must line up, so every row shares one track list. CSS
 * cannot drop a track from grid-template-columns, so each breakpoint gets
 * its own list as a custom property and a media query picks between them.
 */
const gridVars = computed(() => {
  const opts = { hasHandle: false, hasActions: true };
  return {
    '--cols-base': trackListFor(resolved.value, { ...opts, breakpoint: 'base' }),
    '--cols-md': trackListFor(resolved.value, { ...opts, breakpoint: 'md' }),
    '--cols-lg': trackListFor(resolved.value, { ...opts, breakpoint: 'lg' }),
  };
});

const containerVars = computed(() => {
  const opts = { hasHandle: false, hasActions: true };
  return {
    '--minw-base': minWidthFor(resolved.value, { ...opts, breakpoint: 'base' }),
    '--minw-md': minWidthFor(resolved.value, { ...opts, breakpoint: 'md' }),
    '--minw-lg': minWidthFor(resolved.value, { ...opts, breakpoint: 'lg' }),
  };
});

const rowCount = computed(
  () => props.groups.reduce((total, group) => total + group.rows.length, 0),
);

const totals = computed(() => sumClientGroups(props.groups));

function money(value) {
  return formatMoney(Number(value) || 0, 'COP');
}

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
