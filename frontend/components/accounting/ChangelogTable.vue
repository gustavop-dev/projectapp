<template>
  <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
    <table class="w-full min-w-[700px] text-sm">
      <thead>
        <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
          <th class="px-5 py-3">Fecha</th>
          <th class="px-4 py-3">Usuario</th>
          <th class="px-4 py-3">Entidad</th>
          <th class="px-4 py-3">Registro</th>
          <th class="px-4 py-3">Acción</th>
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
            class="hover:bg-surface-raised transition-colors bg-surface cursor-pointer"
            @click="toggleEntry(entry.id)"
          >
            <td class="px-5 py-3 text-text-muted text-xs whitespace-nowrap tabular-nums">
              {{ formatDateTime(entry.created_at) }}
            </td>
            <td class="px-4 py-3 text-text-default">
              {{ entry.actor_username || 'Sistema' }}
            </td>
            <td class="px-4 py-3 text-text-muted">{{ entry.entity_type_label }}</td>
            <td class="px-4 py-3 text-text-default font-medium">{{ entry.object_repr }}</td>
            <td class="px-4 py-3">
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
