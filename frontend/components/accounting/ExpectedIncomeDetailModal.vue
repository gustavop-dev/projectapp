<template>
  <BaseModal
    :model-value="open"
    size="xl"
    title-id="expected-income-detail-title"
    @close="emit('close')"
  >
    <div class="px-6 pt-6 pb-2" data-testid="expected-income-detail-modal">
      <h3 id="expected-income-detail-title" class="text-lg font-bold text-text-default">
        Pendiente por cobrar — {{ periodLabel }}
      </h3>
      <p class="text-sm text-text-muted mt-1">
        Ingresos esperados de la empresa este mes. El pendiente total es
        {{ money(total) }}.
      </p>
    </div>

    <div class="px-6 py-4 space-y-4">
      <p v-if="loading" class="text-sm text-text-subtle py-4">Cargando ingresos esperados...</p>
      <p v-else-if="error" class="text-sm text-danger-strong py-4">
        No se pudieron cargar los ingresos esperados. Cierra el modal e intenta de nuevo.
      </p>
      <p v-else-if="rows.length === 0" class="text-sm text-text-subtle py-4">
        Sin ingresos esperados este mes.
      </p>
      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[560px] text-sm">
          <thead>
            <tr class="text-left text-xs text-text-subtle uppercase tracking-wider">
              <th class="px-3 py-2">Concepto</th>
              <th class="px-3 py-2">Período</th>
              <th class="px-3 py-2 text-right">Total</th>
              <th class="px-3 py-2 text-right">Abonado</th>
              <th class="px-3 py-2 text-right">Pendiente</th>
              <th class="px-3 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.id"
              class="border-t border-border-muted"
              data-testid="expected-income-row"
            >
              <td class="px-3 py-2 text-text-default">{{ row.concept }}</td>
              <td class="px-3 py-2 text-text-muted text-xs whitespace-nowrap">
                {{ row.period_label || row.period_date }}
              </td>
              <td class="px-3 py-2 text-right tabular-nums text-text-default">
                {{ money(row.total_amount) }}
              </td>
              <td class="px-3 py-2 text-right tabular-nums text-text-muted">
                {{ money(row.paid_amount) }}
              </td>
              <td class="px-3 py-2 text-right tabular-nums font-semibold text-warning-strong">
                {{ money(row.pending_amount) }}
              </td>
              <td class="px-3 py-2">
                <span
                  class="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider"
                  :class="statusPill(row.payment_status)"
                >
                  {{ row.payment_status_label || '—' }}
                </span>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t border-border-default font-semibold">
              <td class="px-3 py-2 text-text-default" colspan="2">Total</td>
              <td class="px-3 py-2 text-right tabular-nums text-text-default">
                {{ money(sums.total) }}
              </td>
              <td class="px-3 py-2 text-right tabular-nums text-text-muted">
                {{ money(sums.paid) }}
              </td>
              <td
                class="px-3 py-2 text-right tabular-nums text-warning-strong"
                data-testid="expected-income-pending-sum"
              >
                {{ money(sums.pending) }}
              </td>
              <td class="px-3 py-2"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="flex items-center justify-end pt-2">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Cerrar</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import BaseButton from '~/components/base/BaseButton.vue';
import { get_request } from '~/stores/services/request_http';
import { formatMoney } from '~/utils/formatMoney';

/**
 * Read-only breakdown of the "Pendiente por cobrar" card: the company
 * expected incomes of the card's month. `period` comes from
 * summary.expected_current_month.period (always the real current month,
 * regardless of the page's year selector).
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  /** "YYYY-MM" month of expected_current_month. */
  period: { type: String, default: '' },
  periodLabel: { type: String, default: '' },
  total: { type: [String, Number], default: 0 },
});

const emit = defineEmits(['close']);

const rows = ref([]);
const loading = ref(false);
const error = ref(false);

const STATUS_PILLS = {
  paid: 'bg-success-soft text-success-strong',
  partial: 'bg-warning-soft text-warning-strong',
  pending: 'bg-surface-raised text-text-muted',
};

function statusPill(status) {
  return STATUS_PILLS[status] || STATUS_PILLS.pending;
}

function money(value) {
  return formatMoney(Number(value ?? 0), 'COP');
}

function monthRange(period) {
  const [year, month] = period.split('-').map(Number);
  if (!year || !month) return null;
  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const pad = String(month).padStart(2, '0');
  return { from: `${period}-01`, to: `${year}-${pad}-${lastDay}` };
}

async function loadRows() {
  const range = monthRange(props.period);
  if (!range) return;
  loading.value = true;
  error.value = false;
  try {
    const response = await get_request(
      `accounting/incomes/?kind=expected&ledger=company&date_from=${range.from}&date_to=${range.to}`,
    );
    rows.value = response.data?.results || [];
  } catch (err) {
    rows.value = [];
    error.value = true;
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.open, props.period],
  () => {
    if (!props.open) return;
    loadRows();
  },
  { immediate: true },
);

const sums = computed(() =>
  rows.value.reduce(
    (acc, row) => ({
      total: acc.total + Number(row.total_amount ?? 0),
      paid: acc.paid + Number(row.paid_amount ?? 0),
      pending: acc.pending + Number(row.pending_amount ?? 0),
    }),
    { total: 0, paid: 0, pending: 0 },
  ),
);
</script>
