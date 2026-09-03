<template>
  <div>
    <p v-if="rows.length === 0" class="py-6 text-center text-sm text-text-subtle">
      {{ emptyTitle }}
    </p>

    <div v-else class="space-y-3 panel-landscape:hidden">
      <article
        v-for="row in rows"
        :key="row.id"
        class="rounded-xl border border-border-muted bg-surface p-3"
        data-testid="receivable-row"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="break-words text-sm font-medium text-text-default">{{ row.concept }}</p>
            <p class="mt-0.5 text-xs text-text-muted">
              {{ row.client_name || 'Sin cliente' }} · {{ row.period_label || row.period_date }}
            </p>
          </div>
          <p class="shrink-0 text-sm font-semibold tabular-nums text-text-default">
            {{ money(row.total_amount) }}
          </p>
        </div>
        <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div>
            <dt class="text-text-muted">Abonado</dt>
            <dd class="tabular-nums text-text-default">{{ money(row.paid_amount) }}</dd>
          </div>
          <div>
            <dt class="text-text-muted">Saldo abierto</dt>
            <dd class="tabular-nums font-semibold text-warning-strong">
              {{ money(row.pending_amount) }}
            </dd>
          </div>
        </dl>
        <div class="mt-3 border-t border-border-muted pt-3">
          <ReceivableStateControl
            v-if="manageable"
            :row="row"
            :busy="busyIds.includes(row.id)"
            @change="emit('change', row, $event)"
          />
          <ReceivableConfidenceBadge
            v-else
            :confidence="row.collection_confidence"
          />
        </div>
      </article>
    </div>

    <div v-if="rows.length" class="hidden overflow-x-auto panel-landscape:block">
      <table class="w-full min-w-[780px] text-sm">
        <thead>
          <tr class="border-b border-border-default text-left text-xs uppercase tracking-wider text-text-muted">
            <th class="px-3 py-2 font-medium">Concepto</th>
            <th class="px-3 py-2 font-medium">Cliente / proyecto</th>
            <th class="px-3 py-2 font-medium">Período</th>
            <th class="px-3 py-2 text-right font-medium">Total original</th>
            <th class="px-3 py-2 text-right font-medium">Abonado</th>
            <th class="px-3 py-2 text-right font-medium">Saldo abierto</th>
            <th class="px-3 py-2 font-medium">Previsión</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.id"
            class="border-b border-border-muted last:border-b-0"
            data-testid="receivable-row"
          >
            <td class="max-w-[250px] px-3 py-3 font-medium text-text-default">
              <span class="block break-words">{{ row.concept }}</span>
            </td>
            <td class="px-3 py-3 text-xs text-text-muted">
              <span class="block text-text-default">{{ row.client_name || 'Sin cliente' }}</span>
              <span>{{ row.project_name || 'Sin proyecto' }}</span>
            </td>
            <td class="whitespace-nowrap px-3 py-3 text-xs text-text-muted">
              {{ row.period_label || row.period_date }}
            </td>
            <td class="whitespace-nowrap px-3 py-3 text-right tabular-nums text-text-default">
              {{ money(row.total_amount) }}
            </td>
            <td class="whitespace-nowrap px-3 py-3 text-right tabular-nums text-text-muted">
              {{ money(row.paid_amount) }}
            </td>
            <td class="whitespace-nowrap px-3 py-3 text-right font-semibold tabular-nums text-warning-strong">
              {{ money(row.pending_amount) }}
            </td>
            <td class="px-3 py-3">
              <ReceivableStateControl
                v-if="manageable"
                :row="row"
                :busy="busyIds.includes(row.id)"
                @change="emit('change', row, $event)"
              />
              <ReceivableConfidenceBadge
                v-else
                :confidence="row.collection_confidence"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import ReceivableConfidenceBadge from '~/components/accounting/ReceivableConfidenceBadge.vue';
import ReceivableStateControl from '~/components/accounting/ReceivableStateControl.vue';
import { formatMoney } from '~/utils/formatMoney';

defineProps({
  rows: { type: Array, default: () => [] },
  manageable: { type: Boolean, default: false },
  busyIds: { type: Array, default: () => [] },
  emptyTitle: { type: String, default: 'Sin ingresos en este grupo.' },
});

const emit = defineEmits(['change']);

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}
</script>
