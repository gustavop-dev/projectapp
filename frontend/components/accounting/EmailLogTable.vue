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
          <th class="px-3 py-2 text-right">Acciones</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border-muted">
        <tr v-if="entries.length === 0">
          <td :colspan="resolved.length + 1" class="px-5 py-8 text-center text-sm text-text-subtle">
            Sin envíos.
          </td>
        </tr>
        <template v-for="entry in entries" :key="entry.id">
          <tr
            :data-testid="`email-log-row-${entry.id}`"
            class="accounting-history-row hover:bg-surface-raised transition-colors bg-surface h-9"
            :class="canExpand(entry) ? 'cursor-pointer' : ''"
            @click="toggleEntry(entry)"
          >
            <td data-field="date" :class="[cell(0), 'text-text-muted text-xs tabular-nums']">
              <span class="history-mobile-label panel-landscape:hidden">Fecha</span>
              {{ formatDateTime(entry.sent_at) }}
            </td>
            <td data-field="notice" :class="[cell(1), 'text-text-muted']">
              <span class="history-mobile-label panel-landscape:hidden">Aviso</span>
              {{ entry.template_label }}
            </td>
            <td data-field="recipient" :class="[cell(2), 'min-w-0 text-text-default font-medium']">
              <span class="break-all">{{ entry.recipient }}</span>
            </td>
            <td data-field="subject" :class="[cell(3), 'text-text-muted']">
              <span class="history-mobile-label panel-landscape:hidden">Asunto</span>
              {{ entry.subject || '—' }}
            </td>
            <td data-field="status" :class="cell(4)">
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="statusClass(entry.status)"
              >
                {{ entry.status_label }}
              </span>
            </td>
            <td data-field="actions" class="px-3 py-1">
              <div class="flex items-center justify-end gap-1">
                <BaseButton
                  v-if="entry.has_body"
                  variant="ghost"
                  icon-only
                  size="sm"
                  aria-label="Ver el correo como salió"
                  title="Ver el correo como salió"
                  :data-testid="`email-log-view-body-${entry.id}`"
                  @click.stop="emit('view-body', entry)"
                >
                  <EyeIcon class="w-5 h-5" />
                </BaseButton>
                <BaseButton
                  v-if="entry.status === 'failed'"
                  variant="ghost"
                  icon-only
                  size="sm"
                  aria-label="Reintentar el envío"
                  :title="entry.is_retryable
                    ? `Reenviar solo a ${entry.recipient}`
                    : entry.retry_blocked_reason"
                  :disabled="!entry.is_retryable || retryingId === entry.id"
                  :data-testid="`email-log-retry-${entry.id}`"
                  @click.stop="emit('retry', entry)"
                >
                  <ArrowPathIcon class="w-5 h-5" />
                </BaseButton>
              </div>
            </td>
          </tr>
          <!-- What turns "no me llegó" into a diagnosis: why it failed, what
               it was about, and whether somebody already retried it. -->
          <tr
            v-if="expandedIds.has(entry.id)"
            :data-testid="`email-log-detail-${entry.id}`"
            class="bg-surface-raised"
          >
            <td :colspan="resolved.length + 1" class="px-5 py-3 space-y-1.5">
              <p v-if="entry.error_message" class="text-xs text-danger-strong">
                {{ entry.error_message }}
              </p>
              <p v-if="entry.targets && entry.targets.length" class="text-xs text-text-muted">
                <span class="font-medium text-text-default">Salió por:</span>
                {{ targetsLabel(entry) }}
              </p>
              <p v-if="entry.retry_of" class="text-xs text-text-muted">
                Reintento del envío #{{ entry.retry_of }}.
              </p>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ArrowPathIcon, EyeIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
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

const resolved = resolveColumns(COLUMNS, { hasActions: true });
const tableMinWidth = minWidthFor(resolved, { hasActions: true });

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
   * Rows: { id, template_key, template_label, recipient, subject, status,
   * status_label, error_message, sent_at, targets, has_body, is_retryable,
   * retry_blocked_reason, retry_of }.
   */
  entries: { type: Array, default: () => [] },
  /** Row whose retry is in flight, so its button cannot be double-fired. */
  retryingId: { type: [Number, String], default: null },
});

const emit = defineEmits(['view-body', 'retry']);

const STATUS_CLASSES = {
  sent: 'bg-primary-soft text-text-brand',
  delivered: 'bg-success-soft text-success-strong',
  bounced: 'bg-warning-soft text-warning-strong',
  failed: 'bg-danger-soft text-danger-strong',
};

const expandedIds = ref(new Set());

function canExpand(entry) {
  return Boolean(
    entry.error_message || entry.retry_of || (entry.targets || []).length,
  );
}

function targetsLabel(entry) {
  return (entry.targets || [])
    .map((target) => (
      target.object_repr
        ? `${target.entity_type_label}: ${target.object_repr}`
        : `${target.entity_type_label} #${target.object_id}`
    ))
    .join(' · ');
}

function toggleEntry(entry) {
  if (!canExpand(entry)) return;
  if (expandedIds.value.has(entry.id)) expandedIds.value.delete(entry.id);
  else expandedIds.value.add(entry.id);
  expandedIds.value = new Set(expandedIds.value);
}

function statusClass(status) {
  return STATUS_CLASSES[status] || 'bg-surface-raised text-text-muted';
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

  .accounting-history-row > [data-field="recipient"] {
    grid-column: 1;
    grid-row: 1;
  }

  .accounting-history-row > [data-field="status"] {
    grid-column: 2;
    grid-row: 1;
  }

  .accounting-history-row > [data-field="date"],
  .accounting-history-row > [data-field="notice"],
  .accounting-history-row > [data-field="subject"],
  .accounting-history-row > [data-field="actions"] {
    grid-column: 1 / -1;
  }

  .accounting-history-row > [data-field="actions"] > div {
    justify-content: flex-start;
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
