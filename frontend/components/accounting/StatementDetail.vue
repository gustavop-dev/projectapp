<template>
  <section class="bg-surface rounded-xl border border-border-muted shadow-sm" data-testid="statement-detail">
    <header class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-5 py-4 border-b border-border-muted">
      <div>
        <h2 class="text-base font-medium text-text-default">
          {{ statement.card_name }} · <span class="capitalize">{{ statement.period_label }}</span>
        </h2>
        <p class="text-xs text-text-subtle mt-0.5">
          {{ statement.transactions.length }} transacciones · registrado {{ formatDate(statement.created_at) }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="text-xs px-2.5 py-1 rounded-full font-medium"
          :class="isProcessed ? 'bg-success-soft text-success-strong' : 'bg-warning-soft text-warning-strong'"
        >
          {{ statement.status_label }}
        </span>
        <BaseButton
          v-if="!isProcessed"
          variant="secondary"
          size="sm"
          :disabled="isUpdating"
          data-testid="statement-edit-header"
          @click="$emit('edit-header')"
        >
          Editar encabezado
        </BaseButton>
        <BaseButton
          v-if="!isProcessed"
          variant="secondary"
          size="sm"
          :disabled="isUpdating"
          data-testid="statement-add-tx"
          @click="$emit('add-tx')"
        >
          Agregar transacción
        </BaseButton>
        <BaseButton
          v-if="!isProcessed"
          variant="primary"
          size="sm"
          :disabled="isUpdating"
          data-testid="statement-finalize"
          @click="$emit('finalize')"
        >
          Finalizar
        </BaseButton>
        <BaseButton
          v-else
          variant="secondary"
          size="sm"
          :disabled="isUpdating"
          data-testid="statement-reopen"
          @click="$emit('reopen')"
        >
          Reabrir
        </BaseButton>
        <BaseButton
          variant="danger"
          size="sm"
          :disabled="isUpdating"
          data-testid="statement-delete"
          @click="$emit('delete')"
        >
          Eliminar
        </BaseButton>
      </div>
    </header>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 p-5">
      <AccountingStatCard label="Compras" :value="money(statement.purchases_total)" tone="brand" />
      <AccountingStatCard label="Pagos y abonos" :value="money(statement.payments_total)" tone="success" />
      <AccountingStatCard label="Intereses y comisiones" :value="money(statement.interest_and_fees)" tone="warning" />
      <AccountingStatCard
        label="Saldo de cierre"
        :value="money(statement.closing_balance)"
        :sub="statement.due_date ? `Pago mínimo ${money(statement.minimum_payment)} · vence ${statement.due_date}` : ''"
      />
    </div>

    <!-- Bank PDF kept as documentation -->
    <div class="px-5 pb-4">
      <div class="flex flex-col sm:flex-row sm:items-center gap-2 rounded-lg border border-border-muted bg-surface-raised px-4 py-3">
        <div class="flex-1">
          <p class="text-xs font-medium text-text-muted uppercase tracking-wider">Documento del extracto</p>
          <p class="text-xs text-text-subtle mt-0.5">
            {{ statement.pdf_file_url
              ? 'PDF del banco adjunto como documentación.'
              : 'Adjunta el PDF del banco para dejarlo como documentación.' }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <a
            v-if="statement.pdf_file_url"
            :href="statement.pdf_file_url"
            target="_blank"
            rel="noopener"
            class="text-sm font-medium text-text-brand hover:underline"
            data-testid="statement-pdf-view"
          >
            Ver PDF
          </a>
          <BaseButton
            variant="secondary"
            size="sm"
            :disabled="isUpdating"
            data-testid="statement-pdf-upload"
            @click="pdfInput?.click()"
          >
            {{ statement.pdf_file_url ? 'Reemplazar' : 'Subir PDF' }}
          </BaseButton>
          <BaseButton
            v-if="statement.pdf_file_url"
            variant="danger"
            size="sm"
            :disabled="isUpdating"
            data-testid="statement-pdf-delete"
            @click="$emit('delete-pdf')"
          >
            Eliminar
          </BaseButton>
          <input
            ref="pdfInput"
            type="file"
            accept=".pdf"
            class="hidden"
            data-testid="statement-pdf-input"
            @change="onPdfChosen"
          >
        </div>
      </div>
    </div>

    <div v-if="statement.category_totals.length" class="px-5 pb-4">
      <h3 class="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Por categoría</h3>
      <div class="space-y-1.5">
        <div
          v-for="row in statement.category_totals"
          :key="row.category"
          class="flex items-center gap-3"
        >
          <span class="text-xs text-text-muted w-44 truncate">{{ row.label }}</span>
          <div class="flex-1 h-2 rounded-full bg-surface-raised overflow-hidden">
            <div
              class="h-full rounded-full bg-primary/70"
              :style="{ width: `${categoryPercent(row)}%` }"
            />
          </div>
          <span class="text-xs font-medium text-text-default w-28 text-right">{{ money(row.total) }}</span>
        </div>
      </div>
    </div>

    <p class="px-5 pt-4 pb-2 text-xs text-text-subtle border-t border-border-muted" data-testid="statement-inline-hint">
      Haz clic en cualquier celda para editarla.
      <span v-if="isProcessed">Este extracto está finalizado: al guardar se te pedirá reabrirlo.</span>
    </p>

    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-border-muted text-left">
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Fecha</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Descripción</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Comercio</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Categoría</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Cuota</th>
            <th class="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider text-right">Valor</th>
            <th class="px-5 py-3 text-right" />
          </tr>
        </thead>
        <tbody class="divide-y divide-border-muted">
          <tr
            v-for="tx in statement.transactions"
            :key="tx.id"
            class="hover:bg-surface-raised transition-colors"
            :data-testid="`statement-tx-${tx.id}`"
          >
            <td
              class="px-5 py-3 text-sm text-text-muted whitespace-nowrap"
              :data-testid="`tx-cell-transaction_date-${tx.id}`"
            >
              <AccountingInlineCell
                type="date"
                :value="tx.transaction_date"
                :saving="inlineSavingKey === `${tx.id}:transaction_date`"
                @save="$emit('inline-save', tx, 'transaction_date', $event)"
              >
                {{ tx.transaction_date }}
              </AccountingInlineCell>
            </td>
            <td
              class="px-5 py-3 text-xs text-text-subtle max-w-[220px]"
              :title="tx.raw_description"
              :data-testid="`tx-cell-raw_description-${tx.id}`"
            >
              <AccountingInlineCell
                :value="tx.raw_description"
                :saving="inlineSavingKey === `${tx.id}:raw_description`"
                @save="$emit('inline-save', tx, 'raw_description', $event)"
              >
                <span class="block truncate">{{ tx.raw_description }}</span>
              </AccountingInlineCell>
            </td>
            <td class="px-5 py-3 text-sm" :data-testid="`tx-cell-merchant_name-${tx.id}`">
              <AccountingInlineCell
                type="merchant"
                :value="tx.merchant_name || ''"
                :options="merchantOptions"
                :saving="inlineSavingKey === `${tx.id}:merchant_name`"
                @save="(value, meta) => $emit('inline-save', tx, 'merchant_name', value, meta)"
              >
                <span v-if="tx.merchant_name" class="text-text-default">{{ tx.merchant_name }}</span>
                <span
                  v-else
                  class="text-xs px-2 py-0.5 rounded-full font-medium bg-warning-soft text-warning-strong"
                >
                  Sin identificar
                </span>
              </AccountingInlineCell>
            </td>
            <td class="px-5 py-3 text-sm text-text-muted" :data-testid="`tx-cell-category-${tx.id}`">
              <AccountingInlineCell
                type="select"
                :value="tx.category"
                :options="categoryOptions"
                :saving="inlineSavingKey === `${tx.id}:category`"
                @save="$emit('inline-save', tx, 'category', $event)"
              >
                {{ tx.category_label }}
              </AccountingInlineCell>
            </td>
            <td class="px-5 py-3 text-sm text-text-muted" :data-testid="`tx-cell-installment_label-${tx.id}`">
              <AccountingInlineCell
                type="installments"
                :value="tx.installment_label || ''"
                :saving="inlineSavingKey === `${tx.id}:installment_label`"
                @save="$emit('inline-save', tx, 'installment_label', $event)"
              >
                {{ tx.installment_label || '—' }}
              </AccountingInlineCell>
            </td>
            <td
              class="px-5 py-3 text-sm font-medium text-right whitespace-nowrap"
              :class="Number(tx.amount) < 0 ? 'text-success-strong' : 'text-text-default'"
              :data-testid="`tx-cell-amount-${tx.id}`"
            >
              <AccountingInlineCell
                type="money"
                align="right"
                allow-negative
                :value="tx.amount"
                :saving="inlineSavingKey === `${tx.id}:amount`"
                @save="$emit('inline-save', tx, 'amount', $event)"
              >
                {{ money(tx.amount) }}
              </AccountingInlineCell>
              <!-- Read-only companion: the FX pair is edited from the modal. -->
              <span v-if="tx.original_currency" class="block text-[10px] font-normal text-text-subtle">
                {{ tx.original_amount }} {{ tx.original_currency }}
              </span>
            </td>
            <td class="px-5 py-3 text-right whitespace-nowrap">
              <button
                class="text-xs text-text-muted hover:text-text-brand transition-colors"
                :class="isProcessed ? '' : 'mr-2'"
                @click="$emit('edit-tx', tx)"
              >
                Editar
              </button>
              <BaseButton variant="danger-ghost" size="sm" v-if="!isProcessed" @click="$emit('delete-tx', tx)">
                Eliminar
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import AccountingInlineCell from '~/components/accounting/AccountingInlineCell.vue';
import AccountingStatCard from '~/components/accounting/AccountingStatCard.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import { formatMoney } from '~/utils/formatMoney';
import { formatDate as formatDateBase } from '~/utils/formatDate';

const props = defineProps({
  statement: { type: Object, required: true },
  isUpdating: { type: Boolean, default: false },
  /** Category choices for the inline select: [{ value, label }]. */
  categoryOptions: { type: Array, default: () => [] },
  /** Learned merchants for the inline combobox: [{ value, category, categoryLabel }]. */
  merchantOptions: { type: Array, default: () => [] },
  /** `${txId}:${field}` of the cell whose PATCH is in flight. */
  inlineSavingKey: { type: String, default: null },
});

const emit = defineEmits([
  'finalize', 'reopen', 'delete', 'edit-tx', 'delete-tx',
  'edit-header', 'add-tx', 'upload-pdf', 'delete-pdf', 'inline-save',
]);

const pdfInput = ref(null);

function onPdfChosen(event) {
  const file = event.target.files?.[0];
  if (file) emit('upload-pdf', file);
  event.target.value = '';
}

const isProcessed = computed(() => props.statement.status === 'processed');

const maxCategoryTotal = computed(() =>
  Math.max(...props.statement.category_totals.map((row) => Math.abs(Number(row.total))), 1),
);

function categoryPercent(row) {
  return Math.round((Math.abs(Number(row.total)) / maxCategoryTotal.value) * 100);
}

function money(value) {
  if (value === null || value === undefined || value === '') return '—';
  return formatMoney(Number(value));
}

function formatDate(iso) {
  return formatDateBase(iso, { fallback: '' });
}
</script>
