<template>
  <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
    <table class="w-full text-sm" :style="{ minWidth: tableMinWidth }">
      <thead>
        <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
          <th
            v-for="col in resolved"
            :key="col.key"
            :style="{ width: col.width }"
            :class="[col.headerPadClass, col.alignClass, col.nowrapClass]"
          >{{ col.label }}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border-muted">
        <tr v-if="entries.length === 0">
          <td colspan="5" class="px-5 py-8 text-center text-sm text-text-subtle">
            Sin envíos.
          </td>
        </tr>
        <template v-for="entry in entries" :key="entry.id">
          <tr
            :data-testid="`email-log-row-${entry.id}`"
            class="hover:bg-surface-raised transition-colors bg-surface h-9"
            :class="entry.error_message ? 'cursor-pointer' : ''"
            @click="toggleEntry(entry)"
          >
            <td :class="[cell(0), 'text-text-muted text-xs tabular-nums']">
              {{ formatDateTime(entry.sent_at) }}
            </td>
            <td :class="[cell(1), 'text-text-muted']">{{ entry.template_label }}</td>
            <td :class="[cell(2), 'text-text-default font-medium']">{{ entry.recipient }}</td>
            <td :class="[cell(3), 'text-text-muted']">{{ entry.subject || '—' }}</td>
            <td :class="cell(4)">
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="statusClass(entry.status)"
              >
                {{ entry.status_label }}
              </span>
            </td>
          </tr>
          <!-- Only failures have something more to say; the reason is what
               turns "no me llegó" into an actionable diagnosis. -->
          <tr
            v-if="expandedIds.has(entry.id)"
            :data-testid="`email-log-detail-${entry.id}`"
            class="bg-surface-raised"
          >
            <td colspan="5" class="px-5 py-3 text-xs text-danger-strong">
              {{ entry.error_message }}
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

// Destinatario is the identifying column here — the whole point of the view
// is answering who a notice reached — so it gets the widest floor.
const COLUMNS = [
  { key: 'sent_at', label: 'Fecha', format: 'date' },
  { key: 'template_label', label: 'Aviso' },
  { key: 'recipient', label: 'Destinatario', size: 'name' },
  { key: 'subject', label: 'Asunto' },
  { key: 'status_label', label: 'Estado', size: 'badge' },
];

const resolved = resolveColumns(COLUMNS, { hasActions: false });
const tableMinWidth = minWidthFor(resolved, { hasActions: false });

/** Padding + alignment for the nth column. */
function cell(index) {
  const col = resolved[index];
  return [col.padClass, col.alignClass, col.nowrapClass];
}

defineProps({
  /**
   * Rows: { id, template_key, template_label, recipient, subject, status,
   * status_label, error_message, sent_at }.
   */
  entries: { type: Array, default: () => [] },
});

const STATUS_CLASSES = {
  sent: 'bg-primary-soft text-text-brand',
  delivered: 'bg-success-soft text-success-strong',
  bounced: 'bg-warning-soft text-warning-strong',
  failed: 'bg-danger-soft text-danger-strong',
};

const expandedIds = ref(new Set());

function toggleEntry(entry) {
  if (!entry.error_message) return;
  if (expandedIds.value.has(entry.id)) expandedIds.value.delete(entry.id);
  else expandedIds.value.add(entry.id);
  expandedIds.value = new Set(expandedIds.value);
}

function statusClass(status) {
  return STATUS_CLASSES[status] || 'bg-surface-raised text-text-muted';
}
</script>
