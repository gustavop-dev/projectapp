<template>
  <div
    class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm"
    :aria-busy="loading ? 'true' : undefined"
  >
    <p class="sr-only" aria-live="polite">
      {{ loading ? 'Cargando registros...' : `${rows.length} registros en la tabla` }}
    </p>
    <table class="w-full min-w-[600px] text-sm">
      <thead>
        <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
          <th
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-3 first:px-5"
            :class="alignClass(col)"
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
            </button>
            <template v-else>{{ col.label }}</template>
          </th>
          <th v-if="showActions" class="px-4 py-3 text-right">Acciones</th>
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
            <td
              v-for="(col, colIndex) in columns"
              :key="col.key"
              class="px-4 py-3.5 first:px-5"
              :class="alignClass(col)"
            >
              <div
                class="h-3 rounded bg-surface-raised motion-safe:animate-pulse inline-block"
                :class="skeletonWidthClass(n, colIndex)"
              />
            </td>
            <td v-if="showActions" class="px-4 py-3.5" />
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
          class="hover:bg-surface-raised transition-colors"
          :class="[
            rowBgClass(row),
            row[rowKey] === highlightId ? 'accounting-row-flash' : '',
          ]"
        >
          <td
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-3 first:px-5"
            :class="cellClass(col)"
          >
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              <template v-if="col.format === 'money'">
                {{ formatMoney(row[col.key], 'COP') }}
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
          </td>
          <td v-if="showActions" class="px-4 py-3 text-right whitespace-nowrap">
            <slot name="row-actions" :row="row" />
            <button
              type="button"
              aria-label="Editar"
              :data-testid="`accounting-edit-${row[rowKey]}`"
              class="p-2 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              @click.stop="emit('edit', row)"
            >
              <PencilSquareIcon class="w-5 h-5" />
            </button>
            <button
              type="button"
              aria-label="Eliminar"
              :data-testid="`accounting-delete-${row[rowKey]}`"
              class="p-2 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              @click.stop="emit('delete', row)"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
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
  ChevronUpIcon,
  PencilSquareIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';
import HighlightText from '~/components/ui/HighlightText.vue';
import { formatMoney } from '~/utils/formatMoney';

const props = defineProps({
  /**
   * Column config: { key, label, format ('money'|'date'|'text'|'badge'),
   * align ('left'|'right'|'center'), badgeTones ({ value: tone }),
   * sortable (Boolean) }.
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
});

const ROW_TONE_CLASSES = {
  success: 'bg-success-soft',
  warning: 'bg-warning-soft',
};

function rowBgClass(row) {
  return ROW_TONE_CLASSES[props.rowTone?.(row)] || 'bg-surface';
}

const emit = defineEmits(['edit', 'delete', 'sort']);

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

const colspan = computed(() => props.columns.length + (props.showActions ? 1 : 0));

// Deterministic width variety for skeleton cells (no randomness so SSR
// markup and snapshots stay stable).
const SKELETON_WIDTHS = ['w-24', 'w-16', 'w-32', 'w-20'];

function skeletonWidthClass(rowIndex, colIndex) {
  return SKELETON_WIDTHS[(rowIndex + colIndex) % SKELETON_WIDTHS.length];
}

function alignClass(col) {
  const align = col.align || (col.format === 'money' ? 'right' : 'left');
  if (align === 'right') return 'text-right';
  if (align === 'center') return 'text-center';
  return 'text-left';
}

function cellClass(col) {
  const classes = [alignClass(col)];
  if (col.format === 'money') classes.push('tabular-nums text-text-muted');
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
