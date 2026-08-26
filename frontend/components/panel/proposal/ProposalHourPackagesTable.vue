<template>
  <div>
    <div class="overflow-x-auto">
      <table data-testid="hour-rate-preview" class="w-full text-sm">
        <thead>
          <tr class="border-b border-border-default dark:border-white/[0.08]">
            <th class="text-left font-medium text-text-muted py-2 pr-2">{{ labels.package }}</th>
            <th class="text-center font-medium text-text-muted py-2 px-2">{{ labels.hours }}</th>
            <th class="text-center font-medium text-text-muted py-2 px-2">{{ labels.discount }}</th>
            <th class="text-right font-medium text-text-muted py-2 px-2">{{ labels.rate }}</th>
            <th class="text-right font-medium text-text-muted py-2 px-2">{{ labels.client }}</th>
            <th class="text-right font-medium text-text-muted py-2 pl-2">{{ labels.total }}</th>
            <th v-if="editable" class="w-10" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in rows"
            :key="row.key"
            :data-testid="`hour-package-row-${idx}`"
            class="border-b border-border-default/60 dark:border-white/[0.05]"
          >
            <!-- Paquete: name, with the note as an editable second line -->
            <td class="min-w-0 py-2 pr-2 align-top">
              <!-- Name and note are two cells in one column, so each carries its
                   own testid: a shared one would match both. -->
              <div
                class="min-w-0 max-w-[22rem] [overflow-wrap:anywhere]"
                :data-testid="`hour-package-cell-name-${idx}`"
              >
                <AccountingInlineCell
                  v-if="editable"
                  :value="row.name"
                  @save="emit('update', idx, 'name', $event)"
                >
                  <span class="font-medium text-text-default [overflow-wrap:anywhere]">{{ row.name || '—' }}</span>
                </AccountingInlineCell>
                <span v-else class="font-medium text-text-default [overflow-wrap:anywhere]">{{ row.name }}</span>
              </div>
              <div
                v-if="editable || row.note"
                :data-testid="`hour-package-cell-note-${idx}`"
                class="mt-0.5 min-w-0 max-w-[22rem] [overflow-wrap:anywhere]"
              >
                <AccountingInlineCell
                  v-if="editable"
                  :value="row.note"
                  @save="emit('update', idx, 'note', $event)"
                >
                  <span class="block text-[11px] text-text-subtle [overflow-wrap:anywhere]">{{ row.note || 'Sin nota' }}</span>
                </AccountingInlineCell>
                <span v-else class="block text-[11px] text-text-subtle [overflow-wrap:anywhere]">{{ row.note }}</span>
              </div>
            </td>

            <td class="py-2 px-2 text-center align-top" :data-testid="`hour-package-cell-hours-${idx}`">
              <AccountingInlineCell
                v-if="editable"
                type="number"
                :min="1"
                :value="row.hours"
                @save="emit('update', idx, 'hours', $event)"
              >
                <span class="text-text-default">{{ row.hours }} h</span>
              </AccountingInlineCell>
              <span v-else class="text-text-default">{{ row.hours }} h</span>
            </td>

            <td class="py-2 px-2 text-center align-top" :data-testid="`hour-package-cell-discount-${idx}`">
              <AccountingInlineCell
                v-if="editable"
                type="number"
                :min="0"
                :max="100"
                :value="row.discountPercent"
                @save="emit('update', idx, 'discountPercent', $event)"
              >
                <span class="text-text-default">{{ row.discountLabel }}</span>
              </AccountingInlineCell>
              <span v-else class="text-text-default">{{ row.discountLabel }}</span>
            </td>

            <!-- Tarifa: what the admin sets, before the discount -->
            <td class="py-2 px-2 text-right align-top" :data-testid="`hour-package-cell-rate-${idx}`">
              <AccountingInlineCell
                v-if="editable"
                type="money"
                align="right"
                :value="row.rate"
                @save="emit('update', idx, 'hourlyRate', $event)"
              >
                <span class="text-text-default tabular-nums">{{ row.rateLabel }}</span>
              </AccountingInlineCell>
              <span v-else class="text-text-default tabular-nums">{{ row.rateLabel }}</span>
            </td>

            <!-- Al cliente: the discounted rate the PDF actually prints -->
            <td
              class="py-2 px-2 text-right align-top text-text-default tabular-nums"
              :data-testid="`hour-rate-rate-${row.key}`"
            >
              {{ row.effectiveLabel }}/h
            </td>

            <td
              class="py-2 pl-2 text-right align-top font-medium text-text-default tabular-nums"
              :data-testid="`hour-rate-total-${row.key}`"
            >
              {{ row.totalLabel }}
            </td>

            <td v-if="editable" class="py-2 pl-2 text-right align-top">
              <BaseButton variant="danger-ghost" size="sm" :data-testid="`hour-package-delete-${idx}`" :disabled="rows.length <= 1" :title="rows.length <= 1
                  ? 'La propuesta debe conservar al menos un paquete'
                  : 'Quitar este paquete'" @click="emit('remove', idx)">
                Quitar
              </BaseButton>
            </td>
          </tr>

          <tr v-if="!rows.length">
            <td :colspan="editable ? 7 : 6" class="py-4 text-center text-xs text-text-subtle">
              No hay paquetes para mostrar.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editable" class="flex items-center justify-between gap-3 mt-2">
      <p class="text-[11px] text-text-subtle">
        Hacé clic en cualquier celda para editarla. «Al cliente» es la tarifa ya con el
        descuento aplicado: es la que se imprime en el PDF.
      </p>
      <button
        type="button"
        data-testid="hour-packages-add"
        class="shrink-0 text-xs font-medium text-text-brand hover:underline"
        @click="emit('add')"
      >
        <BaseActionIcon action="create" />
        Agregar paquete
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import AccountingInlineCell from '~/components/accounting/AccountingInlineCell.vue';
import { effectiveRate, totalPrice, formatPackageMoney } from '~/utils/hourPackagePricing.js';

/**
 * The hour-package table shown in the «Tarifa por hora» tab, mirroring the
 * columns the PDF prints plus an editable base rate.
 *
 * Presentational on purpose, like StatementAliasTable: it owns no store and
 * performs no save. Unlike the accounting tables, an inline edit here does NOT
 * fire its own PATCH — it emits `update` so the tab can fold it into the draft
 * it persists with its own «Guardar» button.
 */
const props = defineProps({
  /** Rows in content_json shape: { name, note, hours, discountPercent, hourlyRate, id? }. */
  packages: { type: Array, default: () => [] },
  /** Manual mode: cells become click-to-edit and add/remove appear. */
  editable: { type: Boolean, default: false },
  currency: { type: String, default: 'COP' },
  /** Section-level rate used by packages that carry none of their own. */
  baseRate: { type: [Number, String], default: null },
  language: { type: String, default: 'es' },
});

const emit = defineEmits(['update', 'remove', 'add']);

const labels = computed(() => {
  // Tax label lives inside the header in parentheses, like the PDF.
  const tax = props.currency === 'USD' ? '+ Tax' : '+ IVA';
  return props.language === 'en'
    ? {
      package: 'Package', hours: 'Hours', discount: 'Disc.',
      rate: 'Rate', client: `To client (${tax})`, total: `Total (${tax})`,
    }
    : {
      package: 'Paquete', hours: 'Horas', discount: 'Dcto.',
      rate: 'Tarifa', client: `Al cliente (${tax})`, total: `Total (${tax})`,
    };
});

const rows = computed(() => (props.packages || []).map((pkg, idx) => {
  const own = Number(pkg.hourlyRate);
  const rate = own > 0 ? own : (Number(props.baseRate) || 0);
  const discountPercent = Number(pkg.discountPercent) || 0;
  const hours = Number(pkg.hours) || 0;
  // hourPackagePricing speaks the catalog's snake_case shape.
  const snake = { hourly_rate: rate, discount_percent: discountPercent, hours };
  return {
    // Index-based key: manual rows can be added and removed and most have no
    // catalog id, so the position is the only identity available.
    key: pkg.id ?? `row-${idx}`,
    name: pkg.name || '',
    note: pkg.note || '',
    hours,
    discountPercent,
    rate,
    discountLabel: discountPercent ? `-${discountPercent}%` : '—',
    rateLabel: formatPackageMoney(rate, props.currency),
    effectiveLabel: formatPackageMoney(effectiveRate(snake), props.currency),
    totalLabel: formatPackageMoney(totalPrice(snake), props.currency),
  };
}));
</script>
