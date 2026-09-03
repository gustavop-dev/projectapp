<template>
  <div class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm">
    <table class="accounting-monthly-table w-full text-sm" :style="{ '--table-min-width': tableMinWidth }">
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
        <tr v-if="monthly.length === 0">
          <td colspan="5" class="px-5 py-8 text-center text-sm text-text-subtle">
            Sin registros.
          </td>
        </tr>
        <tr
          v-for="row in monthly"
          :key="row.period"
          :data-testid="`accounting-monthly-row-${row.period}`"
          class="hover:bg-surface-raised transition-colors bg-surface h-9"
        >
          <td :class="[cell(0), 'text-text-default font-medium']">
            {{ row.label }}
            <dl
              class="mt-2 space-y-1 text-xs font-normal panel-landscape:hidden"
              :data-testid="`accounting-monthly-grouped-${row.period}`"
            >
              <div class="flex items-center justify-between gap-3">
                <dt class="text-text-subtle">Esperado</dt>
                <dd class="tabular-nums text-text-default">{{ formatMoney(row.expected) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-3">
                <dt class="text-text-subtle">Líquido</dt>
                <dd class="tabular-nums text-text-default">{{ formatMoney(row.liquid) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-3">
                <dt class="text-text-subtle">Gastos</dt>
                <dd class="tabular-nums text-text-default">{{ formatMoney(row.expenses) }}</dd>
              </div>
            </dl>
          </td>
          <td :class="[cell(1), 'hidden tabular-nums text-text-default panel-landscape:table-cell']">
            {{ formatMoney(row.expected) }}
          </td>
          <td :class="[cell(2), 'hidden tabular-nums text-text-default panel-landscape:table-cell']">
            {{ formatMoney(row.liquid) }}
          </td>
          <td :class="[cell(3), 'hidden tabular-nums text-text-default panel-landscape:table-cell']">
            {{ formatMoney(row.expenses) }}
          </td>
          <td :class="[cell(4), 'tabular-nums', utilityClass(row.utility)]">
            {{ formatMoney(row.utility) }}
          </td>
        </tr>
      </tbody>
      <tfoot v-if="monthly.length > 0">
        <tr class="border-t border-border-default bg-surface-raised font-semibold h-9">
          <td :class="[cell(0), 'text-text-default']">
            Total
            <dl
              class="mt-2 space-y-1 text-xs font-normal panel-landscape:hidden"
              data-testid="accounting-monthly-grouped-total"
            >
              <div class="flex items-center justify-between gap-3">
                <dt class="text-text-subtle">Esperado</dt>
                <dd class="tabular-nums text-text-default">{{ formatMoney(totals.expected) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-3">
                <dt class="text-text-subtle">Líquido</dt>
                <dd class="tabular-nums text-text-default">{{ formatMoney(totals.liquid) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-3">
                <dt class="text-text-subtle">Gastos</dt>
                <dd class="tabular-nums text-text-default">{{ formatMoney(totals.expenses) }}</dd>
              </div>
            </dl>
          </td>
          <td :class="[cell(1), 'hidden tabular-nums text-text-default panel-landscape:table-cell']">
            {{ formatMoney(totals.expected) }}
          </td>
          <td :class="[cell(2), 'hidden tabular-nums text-text-default panel-landscape:table-cell']">
            {{ formatMoney(totals.liquid) }}
          </td>
          <td :class="[cell(3), 'hidden tabular-nums text-text-default panel-landscape:table-cell']">
            {{ formatMoney(totals.expenses) }}
          </td>
          <td :class="[cell(4), 'tabular-nums', utilityClass(totals.utility)]">
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
import { minWidthFor, resolveColumns } from '~/utils/tableLayout';

// The four amounts are one figure read four ways, so they sit together as a
// group and Mes takes the slack — same standard as the shared table.
const COLUMNS = [
  { key: 'label', label: 'Mes', size: 'name' },
  { key: 'expected', label: 'Esperado', format: 'money', group: 'money' },
  { key: 'liquid', label: 'Líquido', format: 'money', group: 'money' },
  { key: 'expenses', label: 'Gastos', format: 'money', group: 'money' },
  { key: 'utility', label: 'Utilidad', format: 'money', group: 'money' },
];

const resolved = resolveColumns(COLUMNS, { hasActions: false });
const tableMinWidth = minWidthFor(resolved, { hasActions: false });

function visibilityClass(key) {
  return ['expected', 'liquid', 'expenses'].includes(key)
    ? 'hidden panel-landscape:table-cell'
    : '';
}

/** Padding + alignment for the nth column, shared by body and footer rows. */
function cell(index) {
  const col = resolved[index];
  return [col.padClass, col.alignClass, col.nowrapClass];
}

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

<style scoped>
@media (min-width: 1024px) {
  .accounting-monthly-table {
    min-width: var(--table-min-width);
  }
}
</style>
