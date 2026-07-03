<template>
  <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
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
              class="inline-flex items-center gap-1 uppercase tracking-wider hover:text-text-default transition-colors"
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
        <tr v-if="rows.length === 0">
          <td :colspan="colspan" class="px-5 py-8 text-center text-sm text-text-subtle">
            Sin registros.
          </td>
        </tr>
        <tr
          v-for="row in rows"
          :key="row[rowKey]"
          :data-testid="`accounting-row-${row[rowKey]}`"
          class="hover:bg-surface-raised transition-colors bg-surface"
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
            <button
              type="button"
              aria-label="Editar"
              :data-testid="`accounting-edit-${row[rowKey]}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors"
              @click.stop="emit('edit', row)"
            >
              <PencilSquareIcon class="w-4 h-4" />
            </button>
            <button
              type="button"
              aria-label="Eliminar"
              :data-testid="`accounting-delete-${row[rowKey]}`"
              class="p-1.5 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors"
              @click.stop="emit('delete', row)"
            >
              <TrashIcon class="w-4 h-4" />
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
});

const emit = defineEmits(['edit', 'delete', 'sort']);

function ariaSort(col) {
  if (!col.sortable) return undefined;
  if (props.sortKey !== col.key) return 'none';
  return props.sortDir === 'desc' ? 'descending' : 'ascending';
}

const TONE_CLASSES = {
  success: 'bg-success-soft text-success-strong',
  danger: 'bg-danger-soft text-danger-strong',
  info: 'bg-primary-soft text-text-brand',
  neutral: 'bg-surface-raised text-text-muted',
};

const colspan = computed(() => props.columns.length + (props.showActions ? 1 : 0));

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
