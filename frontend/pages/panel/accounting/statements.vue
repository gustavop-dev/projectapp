<template>
  <div>
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Extractos de tarjeta</h1>
        <p class="text-sm text-text-subtle mt-1">
          Libro analítico mensual de la tarjeta de crédito. Se alimenta desde el
          chat del asistente (conector contable) adjuntando el extracto del banco.
        </p>
      </div>
      <BaseButton
        variant="secondary"
        size="md"
        data-testid="statements-copy-prompt"
        @click="copyKickoffPrompt"
      >
        Copiar prompt
      </BaseButton>
    </div>

    <AccountingSubnav active="statements" />

    <!-- Year + card filters -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <BaseSegmented v-model="selectedYear" :options="yearOptions" />
      <BaseSelect
        v-if="cardOptions.length > 1"
        v-model="selectedCard"
        :options="cardOptions"
        class="w-56"
        data-testid="statements-card-filter"
      />
    </div>

    <!-- Loading -->
    <div v-if="store.isLoading && !status" class="flex justify-center py-12">
      <div class="w-6 h-6 border-2 border-focus-ring/30 border-t-focus-ring rounded-full animate-spin" />
    </div>

    <template v-else-if="status">
      <StatementMonthGrid
        :months="status.months"
        :selected-id="selectedStatementId"
        class="mb-6"
        @select="selectStatement"
      />

      <StatementDetail
        v-if="detail"
        :statement="detail"
        :is-updating="store.isUpdating"
        class="mb-6"
        @finalize="handleFinalize"
        @reopen="handleReopen"
        @delete="handleDeleteStatement"
        @edit-tx="openTxModal"
        @delete-tx="handleDeleteTx"
        @edit-header="headerModalOpen = true"
        @add-tx="openCreateTxModal"
        @upload-pdf="handleUploadPdf"
        @delete-pdf="handleDeletePdf"
      />

      <!-- Learned merchant aliases -->
      <button
        type="button"
        class="flex items-center gap-2 text-sm font-medium text-text-default hover:text-text-brand transition-colors"
        :aria-expanded="aliasesOpen"
        aria-controls="statement-aliases"
        data-testid="statements-aliases-toggle"
        @click="aliasesOpen = !aliasesOpen"
      >
        <svg
          class="w-4 h-4 transition-transform"
          :class="{ 'rotate-90': aliasesOpen }"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        Comercios aprendidos ({{ store.merchantAliases.length }})
      </button>
      <BaseCollapse id="statement-aliases" :open="aliasesOpen">
        <div class="bg-surface rounded-xl border border-border-muted shadow-sm overflow-hidden mt-2">
          <p v-if="store.merchantAliases.length === 0" class="px-5 py-6 text-sm text-text-subtle">
            Aún no hay alias aprendidos. Se crean al aprobar comercios en el chat.
          </p>
          <table v-else class="w-full">
            <tbody class="divide-y divide-border-muted">
              <tr
                v-for="alias in store.merchantAliases"
                :key="alias.id"
                class="hover:bg-surface-raised transition-colors"
              >
                <td class="px-5 py-2.5 text-xs text-text-subtle font-mono max-w-[240px] truncate" :title="alias.match_text">
                  {{ alias.match_text }}
                </td>
                <td class="px-5 py-2.5 text-sm text-text-default">{{ alias.merchant_name }}</td>
                <td class="px-5 py-2.5 text-sm text-text-muted">{{ alias.default_category_label }}</td>
                <td class="px-5 py-2.5 text-right whitespace-nowrap">
                  <button
                    class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors"
                    @click="handleDeleteAlias(alias)"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </BaseCollapse>
    </template>

    <AccountingErrorState v-else @retry="loadStatus" />

    <!-- Statement header edit modal -->
    <StatementHeaderFormModal
      :open="headerModalOpen"
      :statement="detail"
      :saving="store.isUpdating"
      @close="headerModalOpen = false"
      @submit="saveHeader"
    />

    <!-- Transaction create/edit modal -->
    <BaseModal v-model="txModalOpen" size="md" padding="md">
      <h3 class="text-base font-medium text-text-default mb-4">
        {{ txForm.id ? 'Editar transacción' : 'Agregar transacción' }}
      </h3>
      <div class="space-y-3">
        <template v-if="!txForm.id">
          <BaseFormField label="Fecha" required>
            <BaseInput v-model="txForm.transaction_date" type="date" data-testid="tx-date-input" />
          </BaseFormField>
          <BaseFormField label="Descripción del extracto" required>
            <BaseInput v-model="txForm.raw_description" data-testid="tx-description-input" />
          </BaseFormField>
        </template>
        <BaseFormField label="Comercio">
          <BaseInput v-model="txForm.merchant_name" data-testid="tx-merchant-input" />
        </BaseFormField>
        <BaseFormField label="Categoría">
          <BaseSelect v-model="txForm.category" :options="categoryOptions" />
        </BaseFormField>
        <BaseFormField label="Valor (COP)">
          <BaseInput v-model="txForm.amount" type="number" step="0.01" />
        </BaseFormField>
        <BaseFormField label="Notas">
          <BaseTextarea v-model="txForm.notes" :rows="2" />
        </BaseFormField>
      </div>
      <div class="flex justify-end gap-2 mt-5">
        <BaseButton variant="ghost" size="sm" @click="txModalOpen = false">Cancelar</BaseButton>
        <BaseButton
          variant="primary"
          size="sm"
          :disabled="store.isUpdating"
          data-testid="tx-save"
          @click="saveTx"
        >
          Guardar
        </BaseButton>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import StatementDetail from '~/components/accounting/StatementDetail.vue';
import StatementHeaderFormModal from '~/components/accounting/StatementHeaderFormModal.vue';
import StatementMonthGrid from '~/components/accounting/StatementMonthGrid.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseCollapse from '~/components/base/BaseCollapse.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import BaseTextarea from '~/components/base/BaseTextarea.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const KICKOFF_PROMPT =
  'Adjunto el extracto de mi tarjeta de crédito. Procésalo con las herramientas '
  + 'del conector de contabilidad: empieza llamando get_statement_instructions '
  + 'y sigue el flujo completo (verificar mes, extraer, resolver comercios '
  + 'conmigo, guardar y consolidar).';

const CATEGORY_OPTIONS = [
  { value: 'software', label: 'Software y suscripciones' },
  { value: 'advertising', label: 'Publicidad' },
  { value: 'fuel', label: 'Gasolina' },
  { value: 'groceries', label: 'Supermercado' },
  { value: 'restaurants', label: 'Restaurantes' },
  { value: 'utilities', label: 'Servicios' },
  { value: 'travel', label: 'Viajes' },
  { value: 'shopping', label: 'Compras' },
  { value: 'other', label: 'Otros' },
];

const store = useAccountingStore();
const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const selectedCard = ref('');
const selectedStatementId = ref(null);
const aliasesOpen = ref(false);
const categoryOptions = CATEGORY_OPTIONS;

const status = computed(() => store.statementStatus);
const detail = computed(() => store.statementDetail);

// Year range comes from the backend (card catalog `statements_since`);
// before the first load it falls back to the current year only.
const yearOptions = computed(() =>
  (status.value?.year_options || [currentYear]).map((year) => ({
    value: year,
    label: String(year),
    testId: `statements-year-${year}`,
  })),
);

watch(yearOptions, (options) => {
  if (!options.some((option) => option.value === selectedYear.value)) {
    selectedYear.value = options[options.length - 1].value;
  }
});

const cardOptions = computed(() => [
  { value: '', label: 'Todas las tarjetas' },
  ...(status.value?.cards || []).map((card) => ({ value: card, label: card })),
]);

async function loadStatus() {
  await store.fetchStatementStatus(selectedYear.value, selectedCard.value);
  if (
    selectedStatementId.value
    && !statementVisible(selectedStatementId.value)
  ) {
    selectedStatementId.value = null;
    store.statementDetail = null;
  }
}

function statementVisible(id) {
  return (status.value?.months || []).some((month) =>
    month.statements.some((statement) => statement.id === id),
  );
}

async function loadAll() {
  await Promise.all([
    loadStatus(),
    store.fetchRecords('merchantAliases'),
  ]);
  if (selectedStatementId.value) {
    await store.fetchStatementDetail(selectedStatementId.value);
  }
}

onMounted(loadAll);
usePanelRefresh(loadAll);
watch([selectedYear, selectedCard], loadStatus);

async function selectStatement(id) {
  selectedStatementId.value = id;
  const result = await store.fetchStatementDetail(id);
  if (!result.success) notify.error('No se pudo cargar el extracto.');
}

async function handleFinalize() {
  const result = await store.finalizeStatement(detail.value.id);
  if (result.success) {
    notify.success('Extracto consolidado.');
    await loadStatus();
    return;
  }
  const message = result.message || 'No se pudo finalizar el extracto.';
  if (message.includes('diferencia')) {
    requestConfirm({
      title: 'Los totales no cuadran',
      message: `${message} ¿Cerrar de todas formas?`,
      variant: 'danger',
      confirmText: 'Forzar cierre',
      onConfirm: async () => {
        const forced = await store.finalizeStatement(detail.value.id, true);
        if (forced.success) {
          notify.success('Extracto consolidado (forzado).');
          await loadStatus();
        } else {
          notify.error('No se pudo finalizar el extracto.');
        }
      },
    });
  } else {
    notify.error(message);
  }
}

async function handleReopen() {
  const result = await store.reopenStatement(detail.value.id);
  if (result.success) {
    notify.success('Extracto reabierto.');
    await loadStatus();
  } else {
    notify.error('No se pudo reabrir el extracto.');
  }
}

function handleDeleteStatement() {
  const statement = detail.value;
  requestConfirm({
    title: 'Eliminar extracto',
    message: `¿Eliminar el extracto de ${statement.card_name} (${statement.period_label}) con sus ${statement.transactions.length} transacciones?`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await store.deleteRecord('statements', statement.id);
      if (result.success) {
        notify.success('Extracto eliminado.');
        selectedStatementId.value = null;
        store.statementDetail = null;
        await loadStatus();
      } else {
        notify.error('No se pudo eliminar el extracto.');
      }
    },
  });
}

// ── Statement header editing ──

const headerModalOpen = ref(false);

async function saveHeader(payload) {
  const result = await store.updateRecord('statements', detail.value.id, payload);
  if (result.success) {
    headerModalOpen.value = false;
    notify.success('Encabezado actualizado.');
    await Promise.all([
      store.fetchStatementDetail(detail.value.id),
      loadStatus(),
    ]);
  } else {
    notify.error(result.message || 'No se pudo actualizar el encabezado.');
  }
}

// ── Statement PDF ──

async function handleUploadPdf(file) {
  const result = await store.uploadStatementPdf(detail.value.id, file);
  if (result.success) {
    notify.success('PDF del extracto guardado.');
  } else {
    notify.error(result.message || 'No se pudo subir el PDF.');
  }
}

function handleDeletePdf() {
  requestConfirm({
    title: 'Eliminar PDF del extracto',
    message: '¿Eliminar el PDF adjunto? El archivo se borra del servidor.',
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await store.deleteStatementPdf(detail.value.id);
      if (result.success) {
        notify.success('PDF eliminado.');
      } else {
        notify.error(result.message || 'No se pudo eliminar el PDF.');
      }
    },
  });
}

// ── Transaction editing ──

const txModalOpen = ref(false);
const txForm = reactive({
  id: null,
  transaction_date: '',
  raw_description: '',
  merchant_name: '',
  category: 'other',
  amount: '',
  notes: '',
});

function openTxModal(tx) {
  txForm.id = tx.id;
  txForm.merchant_name = tx.merchant_name;
  txForm.category = tx.category;
  txForm.amount = tx.amount;
  txForm.notes = tx.notes || '';
  txModalOpen.value = true;
}

function openCreateTxModal() {
  txForm.id = null;
  txForm.transaction_date = new Date().toISOString().slice(0, 10);
  txForm.raw_description = '';
  txForm.merchant_name = '';
  txForm.category = 'other';
  txForm.amount = '';
  txForm.notes = '';
  txModalOpen.value = true;
}

async function saveTx() {
  const payload = {
    merchant_name: txForm.merchant_name,
    category: txForm.category,
    amount: txForm.amount,
    notes: txForm.notes,
    is_identified: Boolean(txForm.merchant_name),
  };
  if (!txForm.id) {
    if (!txForm.transaction_date || !txForm.raw_description) {
      notify.error('La fecha y la descripción son obligatorias.');
      return;
    }
    const created = await store.createStatementTransactions(detail.value.id, [{
      ...payload,
      transaction_date: txForm.transaction_date,
      raw_description: txForm.raw_description,
    }]);
    if (created.success) {
      txModalOpen.value = false;
      notify.success('Transacción agregada.');
    } else {
      notify.error(created.message || 'No se pudo agregar la transacción.');
    }
    return;
  }
  const result = await store.updateStatementTransaction(
    detail.value.id, txForm.id, payload,
  );
  if (result.success) {
    txModalOpen.value = false;
    notify.success('Transacción actualizada.');
    await store.fetchStatementDetail(detail.value.id);
  } else {
    notify.error(result.message || 'No se pudo actualizar la transacción.');
  }
}

function handleDeleteTx(tx) {
  requestConfirm({
    title: 'Eliminar transacción',
    message: `¿Eliminar "${tx.merchant_name || tx.raw_description}"?`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await store.deleteStatementTransaction(detail.value.id, tx.id);
      if (result.success) {
        notify.success('Transacción eliminada.');
        await store.fetchStatementDetail(detail.value.id);
      } else {
        notify.error('No se pudo eliminar la transacción.');
      }
    },
  });
}

// ── Aliases ──

function handleDeleteAlias(alias) {
  requestConfirm({
    title: 'Eliminar alias',
    message: `¿Eliminar el alias "${alias.match_text}" → ${alias.merchant_name}? Los próximos extractos dejarán de resolverlo automáticamente.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await store.deleteRecord('merchantAliases', alias.id);
      if (result.success) {
        notify.success('Alias eliminado.');
      } else {
        notify.error('No se pudo eliminar el alias.');
      }
    },
  });
}

// ── Kick-off prompt ──

async function copyKickoffPrompt() {
  try {
    await navigator.clipboard.writeText(KICKOFF_PROMPT);
    notify.success('Prompt copiado. Pégalo en el chat del asistente junto con el PDF del extracto.');
  } catch {
    notify.error('No se pudo copiar el prompt.');
  }
}
</script>
