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
          >
            {{ col.label }}
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
import { PencilSquareIcon, TrashIcon } from '@heroicons/vue/24/outline';
import { formatMoney } from '~/utils/formatMoney';

const props = defineProps({
  /**
   * Column config: { key, label, format ('money'|'date'|'text'|'badge'),
   * align ('left'|'right'|'center'), badgeTones ({ value: tone }) }.
   */
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: 'id' },
  showActions: { type: Boolean, default: true },
});

const emit = defineEmits(['edit', 'delete']);

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
