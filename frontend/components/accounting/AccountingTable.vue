<template>
  <div
    class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm"
    :aria-busy="loading ? 'true' : undefined"
  >
    <p class="sr-only" aria-live="polite">
      {{ loading ? 'Cargando registros...' : `${rows.length} registros en la tabla` }}
    </p>
    <!-- The width ceiling lives on the page root (PAGE_MAX_WIDTH), so the table
         always fills its card; on a narrow screen minWidth wins and the card
         scrolls. -->
    <table class="w-full text-sm" :style="{ minWidth: tableMinWidth }">
      <thead>
        <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
          <th v-if="selectable" class="w-10 px-3 py-2">
            <input
              type="checkbox"
              class="align-middle accent-primary"
              aria-label="Seleccionar todas las filas de esta página"
              data-testid="accounting-select-page"
              :checked="allPageSelected"
              :indeterminate.prop="somePageSelected && !allPageSelected"
              @change="togglePage($event.target.checked)"
            >
          </th>
          <th
            v-for="col in resolved"
            :key="col.key"
            :style="{ width: col.width }"
            :class="[col.headerPadClass, col.alignClass, col.nowrapClass, col.hideTableClass]"
            :aria-sort="ariaSort(col)"
          >
            <button
              v-if="col.sortable"
              type="button"
              class="inline-flex items-center gap-1 uppercase tracking-wider rounded hover:text-text-default transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              :class="sortKey === col.key ? 'text-text-default' : ''"
              :data-testid="`accounting-sort-${col.key}`"
              @click="emit('sort', col.key)"
            >
              <span>{{ col.label }}</span>
              <ChevronUpIcon
                v-if="sortKey === col.key && sortDir === 'asc'"
                class="w-3 h-3"
              />
              <ChevronDownIcon
                v-else-if="sortKey === col.key && sortDir === 'desc'"
                class="w-3 h-3"
              />
              <span v-else data-testid="sortable-hint" aria-hidden="true">
                <ChevronUpDownIcon class="w-3 h-3 text-text-subtle" />
              </span>
            </button>
            <template v-else>{{ col.label }}</template>
          </th>
          <th
            v-if="showActions"
            :style="{ width: actionsWidth }"
            :class="[DENSITY.headerCell, 'text-center']"
          >Acciones</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border-muted">
        <template v-if="loading">
          <tr
            v-for="n in skeletonRows"
            :key="`skeleton-${n}`"
            class="bg-surface"
            data-testid="accounting-skeleton-row"
          >
            <td v-if="selectable" :class="DENSITY.cell" />
            <td
              v-for="(col, colIndex) in resolved"
              :key="col.key"
              :class="[col.padClass, col.alignClass, col.hideTableClass]"
            >
              <div
                class="h-3 rounded bg-surface-raised motion-safe:animate-pulse inline-block"
                :class="skeletonWidthClass(n, colIndex)"
              />
            </td>
            <td v-if="showActions" :class="DENSITY.cell" />
          </tr>
        </template>
        <tr v-else-if="rows.length === 0">
          <td :colspan="colspan" class="px-5 py-8 text-center text-sm text-text-subtle">
            <slot name="empty">Sin registros.</slot>
          </td>
        </tr>
        <tr
          v-for="row in loading ? [] : rows"
          :key="row[rowKey]"
          :data-testid="`accounting-row-${row[rowKey]}`"
          class="hover:bg-surface-raised transition-colors h-9"
          :class="[
            rowBgClass(row),
            row[rowKey] === highlightId ? 'accounting-row-flash' : '',
          ]"
        >
          <td v-if="selectable" class="w-10 px-3">
            <input
              type="checkbox"
              class="align-middle accent-primary"
              :aria-label="`Seleccionar fila ${row[rowKey]}`"
              :data-testid="`accounting-select-${row[rowKey]}`"
              :checked="selectedSet.has(row[rowKey])"
              @change="toggleRow(row[rowKey], $event.target.checked)"
            >
          </td>
          <td
            v-for="col in resolved"
            :key="col.key"
            :class="cellClass(col)"
          >
            <!-- The wrapper is what caps the name column: a <td>'s own
                 max-width is ignored under auto layout. -->
            <span :class="col.contentClass">
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                <template v-if="col.format === 'money'">
                  {{ formatMoney(row[col.key], 'COP') }}
                </template>
                <template v-else-if="col.format === 'percent'">
                  {{ formatPercent(row[col.key]) }}
                </template>
                <span
                  v-else-if="col.format === 'badge'"
                  class="text-xs px-2.5 py-1 rounded-full font-medium"
                  :class="badgeClass(col, row[col.key])"
                >
                  {{ row[col.key] }}
                </span>
                <HighlightText
                  v-else-if="highlightQuery"
                  :text="row[col.key] ?? ''"
                  :query="highlightQuery"
                />
                <template v-else>
                  {{ row[col.key] }}
                </template>
              </slot>
            </span>
          </td>
          <td
            v-if="showActions"
            :class="[DENSITY.cell, 'text-center whitespace-nowrap']"
          >
            <slot name="row-actions" :row="row" />
            <button
              type="button"
              aria-label="Editar"
              :data-testid="`accounting-edit-${row[rowKey]}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              @click.stop="emit('edit', row)"
            >
              <PencilSquareIcon class="w-4 h-4" />
            </button>
            <BaseButton variant="danger-ghost" size="sm" icon-only aria-label="Eliminar" :data-testid="`accounting-delete-${row[rowKey]}`" @click.stop="emit('delete', row)">
              <TrashIcon class="w-4 h-4" />
            </BaseButton>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue';
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
import {
  TABLE_DENSITY,
  actionsWidthFor,
  minWidthFor,
  resolveColumns,
} from '~/utils/tableLayout';

const props = defineProps({
  /**
   * Column config: { key, label, format ('money'|'percent'|'date'|'text'|'badge'),
   * align ('left'|'right'|'center'), badgeTones ({ value: tone }),
   * sortable (Boolean), size (see utils/tableLayout SIZE_NAMES),
   * group (String — adjacent columns sharing one draw closer together),
   * hideBelow ('md'|'lg' — collapses the column on narrow screens) }.
   */
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: 'id' },
  showActions: { type: Boolean, default: true },
  /** Search text to highlight inside default text cells. */
  highlightQuery: { type: String, default: '' },
  /** Active sort state (controlled by the page via @sort). */
  sortKey: { type: String, default: '' },
  sortDir: { type: String, default: 'asc' },
  /** When true, renders skeleton placeholder rows instead of data. */
  loading: { type: Boolean, default: false },
  skeletonRows: { type: Number, default: 5 },
  /** Row key of the last created/edited record: flashes that row. */
  highlightId: { type: [String, Number], default: null },
  /**
   * Optional (row) => 'success'|'warning'|null, tinting the row background.
   * The tone REPLACES `bg-surface` rather than stacking on it: two
   * background utilities of equal specificity would be decided by
   * stylesheet order, not by this binding.
   */
  rowTone: { type: Function, default: null },
  /** Opt-in checkbox column; every other tab keeps its current layout. */
  selectable: { type: Boolean, default: false },
  /** Selected row keys (v-model:selected). */
  selected: { type: Array, default: () => [] },
});

const DENSITY = TABLE_DENSITY;

/**
 * Widths come from what each column shows, and the slack is shared out in
 * proportion to that — no single column absorbs it, which is what used to open
 * one wide gap next to the name.
 */
const resolved = computed(() => resolveColumns(props.columns, { hasActions: props.showActions }));

// Same scale as the data columns, so the actions column is one more share of
// the total instead of a hardcoded width that disagreed with minWidthFor().
const actionsWidth = computed(() => actionsWidthFor(resolved.value));

const tableMinWidth = computed(
  () => minWidthFor(resolved.value, { hasActions: props.showActions }),
);

const ROW_TONE_CLASSES = {
  success: 'bg-success-soft',
  warning: 'bg-warning-soft',
};

function rowBgClass(row) {
  return ROW_TONE_CLASSES[props.rowTone?.(row)] || 'bg-surface';
}

const emit = defineEmits(['edit', 'delete', 'sort', 'update:selected']);

// ── Row selection (opt-in via `selectable`) ──

const selectedSet = computed(() => new Set(props.selected));

const pageKeys = computed(() => props.rows.map((row) => row[props.rowKey]));

const allPageSelected = computed(
  () => pageKeys.value.length > 0
    && pageKeys.value.every((key) => selectedSet.value.has(key)),
);

const somePageSelected = computed(
  () => pageKeys.value.some((key) => selectedSet.value.has(key)),
);

function toggleRow(key, checked) {
  const next = new Set(props.selected);
  if (checked) next.add(key);
  else next.delete(key);
  emit('update:selected', [...next]);
}

/** The header checkbox works on the CURRENT page; the page owns any
 *  "select every filtered row" affordance, which knows the full set. */
function togglePage(checked) {
  const next = new Set(props.selected);
  pageKeys.value.forEach((key) => {
    if (checked) next.add(key);
    else next.delete(key);
  });
  emit('update:selected', [...next]);
}

function ariaSort(col) {
  if (!col.sortable) return undefined;
  if (props.sortKey !== col.key) return 'none';
  return props.sortDir === 'desc' ? 'descending' : 'ascending';
}

const TONE_CLASSES = {
  success: 'bg-success-soft text-success-strong',
  warning: 'bg-warning-soft text-warning-strong',
  danger: 'bg-danger-soft text-danger-strong',
  info: 'bg-primary-soft text-text-brand',
  neutral: 'bg-surface-raised text-text-muted',
};

const colspan = computed(
  () => props.columns.length
    + (props.showActions ? 1 : 0)
    + (props.selectable ? 1 : 0),
);

// Deterministic width variety for skeleton cells (no randomness so SSR
// markup and snapshots stay stable).
const SKELETON_WIDTHS = ['w-24', 'w-16', 'w-32', 'w-20'];

function skeletonWidthClass(rowIndex, colIndex) {
  return SKELETON_WIDTHS[(rowIndex + colIndex) % SKELETON_WIDTHS.length];
}

/** `col` here is already resolved, so alignment and padding come precomputed. */
function cellClass(col) {
  const classes = [col.padClass, col.alignClass, col.nowrapClass, col.hideTableClass];
  if (col.format === 'money') classes.push('tabular-nums text-text-muted');
  else if (col.format === 'percent') classes.push('tabular-nums text-text-subtle text-xs');
  else if (col.format === 'date') classes.push('text-text-muted text-xs');
  else classes.push('text-text-default');
  return classes;
}

function badgeClass(col, value) {
  const tone = col.badgeTones?.[value] || 'neutral';
  return TONE_CLASSES[tone] || TONE_CLASSES.neutral;
}
</script>

<style scoped>
/* Feedback flash for the row that was just created or edited. The color
 * holds briefly and then decays; with reduced motion it stays solid until
 * the page clears highlightId (the information is kept, not the motion). */
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
