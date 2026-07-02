<template>
  <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
    <table class="w-full min-w-[600px] text-sm">
      <thead>
        <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
          <th class="px-5 py-3">Mes</th>
          <th class="px-4 py-3 text-right">Esperado</th>
          <th class="px-4 py-3 text-right">Líquido</th>
          <th class="px-4 py-3 text-right">Gastos</th>
          <th class="px-4 py-3 text-right">Utilidad</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border-muted">
        <tr v-if="monthly.length === 0">
          <td colspan="5" class="px-5 py-8 text-center text-sm text-text-subtle">
            Sin registros.
          </td>
        </tr>
        <tr
          v-for="row in monthly"
          :key="row.period"
          :data-testid="`accounting-monthly-row-${row.period}`"
          class="hover:bg-surface-raised transition-colors bg-surface"
        >
          <td class="px-5 py-3 text-text-default font-medium">{{ row.label }}</td>
          <td class="px-4 py-3 text-right tabular-nums text-text-muted">
            {{ formatMoney(row.expected) }}
          </td>
          <td class="px-4 py-3 text-right tabular-nums text-text-muted">
            {{ formatMoney(row.liquid) }}
          </td>
          <td class="px-4 py-3 text-right tabular-nums text-text-muted">
            {{ formatMoney(row.expenses) }}
          </td>
          <td class="px-4 py-3 text-right tabular-nums" :class="utilityClass(row.utility)">
            {{ formatMoney(row.utility) }}
          </td>
        </tr>
      </tbody>
      <tfoot v-if="monthly.length > 0">
        <tr class="border-t border-border-default bg-surface-raised font-semibold">
          <td class="px-5 py-3 text-text-default">Total</td>
          <td class="px-4 py-3 text-right tabular-nums text-text-default">
            {{ formatMoney(totals.expected) }}
          </td>
          <td class="px-4 py-3 text-right tabular-nums text-text-default">
            {{ formatMoney(totals.liquid) }}
          </td>
          <td class="px-4 py-3 text-right tabular-nums text-text-default">
            {{ formatMoney(totals.expenses) }}
          </td>
          <td class="px-4 py-3 text-right tabular-nums" :class="utilityClass(totals.utility)">
            {{ formatMoney(totals.utility) }}
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { formatMoney } from '~/utils/formatMoney';

const props = defineProps({
  /**
   * Rows: { period, label, expected, liquid, expenses, expected_utility, utility }
   * — money values arrive as numbers or numeric strings.
   */
  monthly: { type: Array, default: () => [] },
});

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

const totals = computed(() =>
  props.monthly.reduce(
    (acc, row) => ({
      expected: acc.expected + toNumber(row.expected),
      liquid: acc.liquid + toNumber(row.liquid),
      expenses: acc.expenses + toNumber(row.expenses),
      utility: acc.utility + toNumber(row.utility),
    }),
    { expected: 0, liquid: 0, expenses: 0, utility: 0 },
  ),
);

function utilityClass(value) {
  return toNumber(value) < 0 ? 'text-danger-strong' : 'text-text-default';
}
</script>
