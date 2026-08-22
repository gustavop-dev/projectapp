<template>
  <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
    <table class="accounting-history-table w-full text-sm" :style="{ '--table-min-width': tableMinWidth }">
      <thead>
        <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
          <th
            v-for="col in resolved"
            :key="col.key"
            :style="{ width: col.width }"
            :class="[col.headerPadClass, col.alignClass, col.nowrapClass, visibilityClass(col.key)]"
          >{{ col.label }}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border-muted">
        <tr v-if="entries.length === 0">
          <td colspan="5" class="px-5 py-8 text-center text-sm text-text-subtle">
            Sin registros.
          </td>
        </tr>
        <template v-for="entry in entries" :key="entry.id">
          <tr
            :data-testid="`changelog-row-${entry.id}`"
            class="accounting-history-row hover:bg-surface-raised transition-colors bg-surface cursor-pointer h-9"
            @click="toggleEntry(entry.id)"
          >
            <td data-field="date" :class="[cell(0), 'text-text-muted text-xs tabular-nums']">
              <span class="history-mobile-label panel-landscape:hidden">Fecha</span>
              {{ formatDateTime(entry.created_at) }}
            </td>
            <td data-field="actor" :class="[cell(1), 'text-text-default']">
              <span class="history-mobile-label panel-landscape:hidden">Usuario</span>
              {{ entry.actor_username || 'Sistema' }}
            </td>
            <td data-field="entity" :class="[cell(2), 'text-text-muted']">
              <span class="history-mobile-label panel-landscape:hidden">Entidad</span>
              {{ entry.entity_type_label }}
            </td>
            <td data-field="record" :class="[cell(3), 'min-w-0 text-text-default font-medium']">
              <span class="break-words">{{ entry.object_repr }}</span>
            </td>
            <td data-field="action" :class="cell(4)">
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="actionClass(entry.action)"
              >
                {{ entry.action_label }}
              </span>
            </td>
          </tr>
          <tr
            v-if="expandedIds.has(entry.id)"
            :data-testid="`changelog-detail-${entry.id}`"
            class="bg-surface-raised"
          >
            <td colspan="5" class="px-5 py-3">
              <p
                v-if="!entry.changes || entry.changes.length === 0"
                class="text-xs text-text-subtle"
              >
                Sin cambios de campos.
              </p>
              <ul v-else class="space-y-1">
                <li
                  v-for="(change, idx) in entry.changes"
                  :key="`${entry.id}-${change.field || idx}`"
                  class="text-xs text-text-muted"
                >
                  <span class="font-medium text-text-default">{{ change.label }}:</span>
                  {{ changeText(entry.action, change) }}
                </li>
              </ul>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { formatDateTime } from '~/utils/formatDate';
import { minWidthFor, resolveColumns } from '~/utils/tableLayout';

// Registro is the identifying column, so it gets the widest floor; the rest sit at
// the width their content needs.
const COLUMNS = [
  { key: 'created_at', label: 'Fecha', format: 'date' },
  { key: 'actor_username', label: 'Usuario' },
  { key: 'entity_type_label', label: 'Entidad' },
  { key: 'object_repr', label: 'Registro', size: 'name' },
  { key: 'action_label', label: 'Acción', size: 'badge' },
];

const resolved = resolveColumns(COLUMNS, { hasActions: false });
const tableMinWidth = minWidthFor(resolved, { hasActions: false });

function visibilityClass() {
  return '';
}

/** Padding + alignment for the nth column. */
function cell(index) {
  const col = resolved[index];
  return [col.padClass, col.alignClass, col.nowrapClass];
}

defineProps({
  /**
   * Rows: { id, entity_type, entity_type_label, object_id, object_repr,
   * action, action_label, changes: [{ field, label, old, new }],
   * actor_username, created_at }.
   */
  entries: { type: Array, default: () => [] },
});

const ACTION_CLASSES = {
  created: 'bg-success-soft text-success-strong',
  updated: 'bg-primary-soft text-text-brand',
  deleted: 'bg-danger-soft text-danger-strong',
};

const expandedIds = ref(new Set());

function toggleEntry(id) {
  if (expandedIds.value.has(id)) expandedIds.value.delete(id);
  else expandedIds.value.add(id);
  expandedIds.value = new Set(expandedIds.value);
}

function actionClass(action) {
  return ACTION_CLASSES[action] || 'bg-surface-raised text-text-muted';
}

function displayValue(value) {
  if (value === null || value === undefined || value === '') return '—';
  return String(value);
}

function changeText(action, change) {
  if (action === 'created') return displayValue(change.new);
  if (action === 'deleted') return displayValue(change.old);
  return `${displayValue(change.old)} → ${displayValue(change.new)}`;
}
</script>

<style scoped>
@media (max-width: 1023px) {
  .accounting-history-table thead {
    display: none;
  }

  .accounting-history-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.35rem 1rem;
    height: auto;
    padding: 0.85rem 1rem;
  }

  .accounting-history-row > td {
    padding: 0;
    white-space: normal;
  }

  .accounting-history-row > [data-field="record"] {
    grid-column: 1;
    grid-row: 1;
  }

  .accounting-history-row > [data-field="action"] {
    grid-column: 2;
    grid-row: 1;
  }

  .accounting-history-row > [data-field="date"],
  .accounting-history-row > [data-field="actor"],
  .accounting-history-row > [data-field="entity"] {
    grid-column: 1 / -1;
  }

  .history-mobile-label {
    display: inline-block;
    min-width: 4.5rem;
    color: var(--color-text-subtle);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
}

@media (min-width: 1024px) {
  .accounting-history-table {
    min-width: var(--table-min-width);
  }
}
</style>
