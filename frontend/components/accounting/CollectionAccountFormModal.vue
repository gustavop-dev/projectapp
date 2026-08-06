<script setup>
import { computed, ref, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import IncomeFormModal from '~/components/accounting/IncomeFormModal.vue';
import { INPUT_FIELD_BASE, INPUT_FIELD_SIZE } from '~/components/base/inputClasses';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useAccountingStore } from '~/stores/accounting';
import { useProposalClientsStore } from '~/stores/proposal_clients';
import { formatMoney } from '~/utils/formatMoney';

/**
 * Two-step create modal for cuentas de cobro: form → preview → send.
 *
 * The preview step shows the REAL email (subject + rendered body) and the
 * PDF the backend will attach — produced by the same pipeline as the send,
 * rolled back server-side — so confirming sends exactly what was reviewed.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  /** Preselected income row (entry point from the Ingresos tab). */
  income: { type: Object, default: null },
});

const emit = defineEmits(['close', 'created']);

const store = useAccountingStore();
const clientsStore = useProposalClientsStore();
const notify = usePanelNotify();

const step = ref('form');
const previewing = ref(false);
const saving = ref(false);
const preview = ref(null);
const pdfUrl = ref('');

// ── Client ──
const clientId = ref(null);
const suggestedNumber = ref('');
const numberDirty = ref(false);
const showInlineClient = ref(false);
const creatingClient = ref(false);
// Client resolved from the selected income (PA-24): shown locked.
const clientFromIncome = ref(null);
const loadingClient = ref(false);
const inlineClient = ref({ name: '', email: '', company: '' });

// ── Income ──
const selectedIncome = ref(null);
const incomeQuery = ref('');
const incomeOptions = ref([]);
const incomeOpen = ref(false);
const searchingIncomes = ref(false);
const showIncomeForm = ref(false);

function defaultForm() {
  return {
    public_number: '',
    billing_concept: '',
    unit_price: null,
    period_start: '',
    period_end: '',
    term: 'days',
    payment_term_days: 8,
    due_date: '',
    city: '',
    customer: {
      name: '',
      identification_type: '',
      identification: '',
      email: '',
      contact_name: '',
      address: '',
    },
    notes: '',
  };
}

const form = ref(defaultForm());

const termOptions = [
  { value: 'days', label: 'Días tras emisión' },
  { value: 'fixed', label: 'Fecha fija' },
];
const identTypeOptions = [
  { value: 'NIT', label: 'NIT' },
  { value: 'CC', label: 'C.C.' },
];

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    step.value = 'form';
    preview.value = null;
    revokePdf();
    form.value = defaultForm();
    clientId.value = null;
    suggestedNumber.value = '';
    numberDirty.value = false;
    showInlineClient.value = false;
    showIncomeForm.value = false;
    clientFromIncome.value = null;
    loadingClient.value = false;
    selectedIncome.value = null;
    incomeQuery.value = '';
    incomeOptions.value = [];
    if (props.income) {
      applyIncome(props.income);
    } else {
      loadIncomes('');
    }
  },
  { immediate: true },
);

// ── Income combobox (remote search over expected+liquid incomes) ──

function applyIncome(income) {
  selectedIncome.value = income;
  incomeQuery.value = income.concept || '';
  if (!form.value.billing_concept) {
    form.value.billing_concept = income.concept || '';
  }
  if (!form.value.unit_price) {
    const amount = Number(income.pending_amount ?? income.total_amount ?? 0);
    form.value.unit_price = amount > 0 ? amount : null;
  }
  // The income already knows whose money this is: resolve the client from
  // it instead of asking for it again.
  if (income.client && !clientId.value) {
    clientFromIncome.value = {
      id: income.client,
      name: income.client_name || `Cliente #${income.client}`,
    };
    clientId.value = income.client;
    applyClientById(income.client);
  }
}

/** Fill the customer snapshot + suggested number from a client id alone. */
async function applyClientById(profileId) {
  loadingClient.value = true;
  const result = await clientsStore.fetchClient(profileId);
  loadingClient.value = false;
  if (result.success && result.data) {
    await onClientSelect(result.data);
  }
}

async function loadIncomes(query) {
  searchingIncomes.value = true;
  const result = await store.searchIncomesForCollection(
    query ? { q: query } : {},
  );
  searchingIncomes.value = false;
  if (result.success) incomeOptions.value = result.data;
}

const debouncedIncomeSearch = useDebounceFn(
  () => loadIncomes(incomeQuery.value.trim()),
  250,
);

function onIncomeInput() {
  incomeOpen.value = true;
  if (selectedIncome.value && incomeQuery.value !== selectedIncome.value.concept) {
    selectedIncome.value = null;
  }
  debouncedIncomeSearch();
}

function onIncomeFocus() {
  incomeOpen.value = true;
  if (!incomeOptions.value.length) loadIncomes(incomeQuery.value.trim());
}

const incomeMatches = computed(() => incomeOptions.value.slice(0, 8));

function pickIncome(option) {
  if (option.has_collection_account) return;
  incomeOpen.value = false;
  applyIncome(option);
}

function incomeAmountLabel(option) {
  const amount = Number(option.pending_amount ?? option.total_amount ?? 0);
  return formatMoney(amount, 'COP');
}

// ── Client selection + snapshot prefill ──

async function onClientSelect(client) {
  form.value.customer = {
    name: client.company || client.name || '',
    identification_type: client.nit ? 'NIT' : (client.cedula ? 'CC' : ''),
    identification: client.nit || client.cedula || '',
    email: client.is_email_placeholder ? '' : (client.email || ''),
    contact_name: client.name || '',
    address: '',
  };
  numberDirty.value = false;
  const result = await store.fetchCollectionAccountNextNumber(client.id);
  if (result.success) {
    suggestedNumber.value = result.data.suggested_number || '';
    form.value.public_number = suggestedNumber.value;
    if (!form.value.city) form.value.city = result.data.issuer_city || '';
  }
}

function onCreateNewClient(typedName) {
  showInlineClient.value = true;
  inlineClient.value = { name: typedName || '', email: '', company: '' };
}

async function createInlineClient() {
  creatingClient.value = true;
  const result = await clientsStore.createClient({ ...inlineClient.value });
  creatingClient.value = false;
  if (result.success && result.data?.id) {
    showInlineClient.value = false;
    clientId.value = result.data.id;
    await onClientSelect(result.data);
    notify.success({ title: 'Cliente creado' });
  } else {
    notify.error({
      title: 'No se pudo crear el cliente',
      detail: result.errors?.message || '',
    });
  }
}

/** The client chosen upstream: the stacked income form inherits it instead
 *  of offering a second picker that could contradict this one. */
const lockedClientForIncome = computed(() => (
  clientId.value
    ? {
      id: clientId.value,
      name: clientFromIncome.value?.name
        || form.value.customer.name
        || form.value.customer.contact_name
        || `Cliente #${clientId.value}`,
    }
    : null
));

function onNumberInput() {
  numberDirty.value = form.value.public_number !== suggestedNumber.value;
}

// ── Inline expected-income creation (stacked IncomeFormModal) ──

async function handleIncomeCreated(payload) {
  const result = await store.createRecord('incomes', payload);
  if (result.success) {
    showIncomeForm.value = false;
    if (result.data?.kind !== 'lost') {
      applyIncome(result.data);
    }
    notify.success({ title: 'Ingreso creado' });
  } else {
    notify.error({ title: 'No se pudo crear el ingreso', detail: result.message });
  }
}

// ── Preview + confirm ──

const canPreview = computed(() => (
  !!clientId.value
  && !loadingClient.value
  && !!selectedIncome.value?.id
  && Number(form.value.unit_price) > 0
  && !!form.value.customer.email
));

function buildPayload() {
  const payload = {
    client_profile_id: clientId.value,
    income_record_id: selectedIncome.value.id,
    billing_concept: form.value.billing_concept,
    items: [{
      description: form.value.billing_concept,
      quantity: '1',
      unit_price: String(form.value.unit_price),
      period_start: form.value.period_start || null,
      period_end: form.value.period_end || null,
    }],
    city: form.value.city,
    customer: { ...form.value.customer },
    notes: form.value.notes,
  };
  if (numberDirty.value && form.value.public_number.trim()) {
    payload.public_number = form.value.public_number.trim();
  }
  if (form.value.term === 'fixed' && form.value.due_date) {
    payload.due_date = form.value.due_date;
  } else {
    payload.payment_term_days = Number(form.value.payment_term_days) || 8;
  }
  return payload;
}

async function goPreview() {
  previewing.value = true;
  const result = await store.previewCollectionAccount(buildPayload());
  previewing.value = false;
  if (!result.success) {
    notify.error({
      title: 'No se pudo generar la previsualización',
      detail: result.message,
    });
    return;
  }
  preview.value = result.data;
  revokePdf();
  if (result.data.pdf_base64) {
    const bytes = Uint8Array.from(
      atob(result.data.pdf_base64), (ch) => ch.charCodeAt(0),
    );
    pdfUrl.value = URL.createObjectURL(
      new Blob([bytes], { type: 'application/pdf' }),
    );
  }
  step.value = 'preview';
}

async function confirmSend() {
  saving.value = true;
  const result = await store.createCollectionAccount(buildPayload());
  saving.value = false;
  if (!result.success) {
    notify.error({
      title: 'No se pudo crear la cuenta de cobro',
      detail: result.message,
    });
    return;
  }
  const number = result.data?.document?.public_number || '';
  if (result.data?.email_sent) {
    notify.success({
      title: 'Cuenta de cobro enviada',
      detail: number
        ? `Documento ${number} enviado a ${preview.value?.customer_email || 'cliente'}.`
        : '',
    });
  } else {
    notify.warning({
      title: `Cuenta ${number} emitida, pero el correo falló`,
      detail: 'Reenvíala con la acción "Reenviar al cliente".',
    });
  }
  emit('created', result.data);
  close();
}

function revokePdf() {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value);
    pdfUrl.value = '';
  }
}

function close() {
  revokePdf();
  emit('close');
}

function openPdfTab() {
  if (pdfUrl.value) window.open(pdfUrl.value, '_blank', 'noopener');
}
</script>

<template>
  <BaseModal
    :model-value="open"
    size="2xl"
    title-id="collection-form-title"
    @close="close"
  >
    <div class="px-6 pt-6 pb-2 flex items-center justify-between gap-3">
      <h3 id="collection-form-title" class="text-lg font-bold text-text-default">
        {{ step === 'form' ? 'Nueva cuenta de cobro' : 'Revisar antes de enviar' }}
      </h3>
      <span class="text-xs text-text-subtle">
        Paso {{ step === 'form' ? '1' : '2' }} de 2
      </span>
    </div>

    <!-- ── Step 1: form ── -->
    <form
      v-if="step === 'form'"
      class="px-6 py-4 space-y-4"
      @submit.prevent="goPreview"
    >
      <BaseFormField label="Cliente" required>
        <div
          v-if="clientFromIncome"
          class="rounded-xl border border-border-default bg-surface-raised px-3 py-2.5 text-sm text-text-default"
          data-testid="collection-form-client-locked"
        >
          {{ clientFromIncome.name }}
          <span class="text-text-subtle">· desde el ingreso</span>
        </div>
        <ClientAutocomplete
          v-else
          v-model="clientId"
          test-id="collection-form-client"
          @select="onClientSelect"
          @create-new="onCreateNewClient"
        />
      </BaseFormField>

      <!-- Inline client creation (module de clientes, sin salir del flujo) -->
      <div
        v-if="showInlineClient"
        class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-3"
        data-testid="collection-form-inline-client"
      >
        <p class="text-sm font-medium text-text-default">Crear cliente nuevo</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <BaseFormField label="Nombre">
            <BaseInput v-model="inlineClient.name" data-testid="collection-form-inline-client-name" />
          </BaseFormField>
          <BaseFormField label="Email">
            <BaseInput v-model="inlineClient.email" type="email" />
          </BaseFormField>
          <BaseFormField label="Empresa">
            <BaseInput v-model="inlineClient.company" />
          </BaseFormField>
        </div>
        <div class="flex justify-end gap-2">
          <BaseButton type="button" variant="secondary" size="sm" @click="showInlineClient = false">
            Cancelar
          </BaseButton>
          <BaseButton
            type="button"
            variant="primary"
            size="sm"
            :disabled="creatingClient"
            data-testid="collection-form-inline-client-save"
            @click="createInlineClient"
          >
            {{ creatingClient ? 'Creando...' : 'Crear cliente' }}
          </BaseButton>
        </div>
      </div>

      <!-- Income combobox: mandatory link -->
      <BaseFormField label="Ingreso vinculado" required>
        <template v-if="props.income">
          <div
            class="rounded-xl border border-border-default bg-surface-raised px-3 py-2.5 text-sm text-text-default"
            data-testid="collection-form-income-locked"
          >
            {{ props.income.concept }}
            <span class="text-text-subtle">· {{ incomeAmountLabel(props.income) }}</span>
          </div>
        </template>
        <div v-else class="relative">
          <input
            v-model="incomeQuery"
            type="text"
            role="combobox"
            autocomplete="off"
            aria-autocomplete="list"
            aria-haspopup="listbox"
            :aria-expanded="incomeOpen"
            placeholder="Buscar ingreso por concepto..."
            data-testid="collection-form-income"
            :class="[INPUT_FIELD_BASE, INPUT_FIELD_SIZE.md]"
            @input="onIncomeInput"
            @focus="onIncomeFocus"
          >
          <ul
            v-if="incomeOpen && (incomeMatches.length || searchingIncomes)"
            class="absolute z-30 mt-1 w-full max-h-64 overflow-auto rounded-xl border border-border-default bg-surface shadow-lg"
            role="listbox"
          >
            <li v-if="searchingIncomes" class="px-3 py-2 text-sm text-text-subtle">
              Buscando...
            </li>
            <li
              v-for="option in incomeMatches"
              :key="option.id"
              role="option"
              :aria-disabled="option.has_collection_account"
              :data-testid="`collection-form-income-option-${option.id}`"
              :class="[
                'px-3 py-2 text-sm transition-colors',
                option.has_collection_account
                  ? 'opacity-50 cursor-not-allowed'
                  : 'cursor-pointer hover:bg-surface-raised text-text-default',
              ]"
              @mousedown.prevent="pickIncome(option)"
            >
              <span class="flex items-center justify-between gap-2">
                <span class="truncate">{{ option.concept }}</span>
                <span class="text-xs text-text-subtle whitespace-nowrap">
                  {{ option.kind_label }} · {{ incomeAmountLabel(option) }}
                </span>
              </span>
              <span
                v-if="option.has_collection_account"
                class="block text-xs text-warning-strong"
              >
                Ya tiene cuenta de cobro ({{ option.collection_account_number }})
              </span>
            </li>
          </ul>
          <p v-if="selectedIncome" class="text-xs text-text-subtle mt-1">
            Ingreso enlazado: {{ selectedIncome.concept }}
            <span class="tabular-nums">(#{{ selectedIncome.id }})</span>
          </p>
          <button
            type="button"
            class="text-xs text-text-brand hover:underline mt-1"
            data-testid="collection-form-create-income"
            @click="showIncomeForm = true"
          >
            + Crear ingreso esperado
          </button>
        </div>
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Consecutivo" hint="Sugerido; editable">
          <BaseInput
            v-model="form.public_number"
            data-testid="collection-form-number"
            :placeholder="suggestedNumber || 'Selecciona un cliente'"
            @input="onNumberInput"
          />
        </BaseFormField>
        <BaseFormField label="Valor" required>
          <BaseCurrencyInput
            v-model="form.unit_price"
            data-testid="collection-form-amount"
            required
          />
        </BaseFormField>
      </div>

      <BaseFormField label="Concepto del servicio" required>
        <BaseInput
          v-model="form.billing_concept"
          data-testid="collection-form-concept"
          required
        />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Período facturado (opcional)">
          <div class="flex items-center gap-2">
            <BaseInput v-model="form.period_start" type="date" />
            <span class="text-text-subtle text-sm">a</span>
            <BaseInput v-model="form.period_end" type="date" />
          </div>
        </BaseFormField>
        <BaseFormField label="Ciudad">
          <BaseInput v-model="form.city" placeholder="Ciudad de emisión" />
        </BaseFormField>
      </div>

      <BaseFormField label="Plazo de pago">
        <div class="space-y-2">
          <BaseSegmented v-model="form.term" :options="termOptions" full-width />
          <BaseInput
            v-if="form.term === 'days'"
            v-model="form.payment_term_days"
            type="number"
            min="1"
            max="120"
            data-testid="collection-form-term-days"
          />
          <BaseInput
            v-else
            v-model="form.due_date"
            type="date"
            data-testid="collection-form-due-date"
          />
        </div>
      </BaseFormField>

      <!-- Editable customer snapshot -->
      <div class="rounded-xl border border-border-default p-4 space-y-3">
        <p class="text-sm font-medium text-text-default">Datos del cliente en el documento</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <BaseFormField label="Nombre / Razón social">
            <BaseInput v-model="form.customer.name" data-testid="collection-form-customer-name" />
          </BaseFormField>
          <BaseFormField label="Email" required>
            <BaseInput
              v-model="form.customer.email"
              type="email"
              data-testid="collection-form-customer-email"
              required
            />
          </BaseFormField>
          <BaseFormField label="Tipo de identificación">
            <BaseSegmented
              v-model="form.customer.identification_type"
              :options="identTypeOptions"
              full-width
            />
          </BaseFormField>
          <BaseFormField label="Número de identificación">
            <BaseInput
              v-model="form.customer.identification"
              data-testid="collection-form-customer-identification"
            />
          </BaseFormField>
          <BaseFormField label="Contacto">
            <BaseInput v-model="form.customer.contact_name" />
          </BaseFormField>
          <BaseFormField label="Dirección">
            <BaseInput v-model="form.customer.address" />
          </BaseFormField>
        </div>
      </div>

      <p class="text-xs text-text-subtle">
        Se incluirán los datos de pago configurados del emisor; los verás en la previsualización.
      </p>

      <BaseFormField label="Notas">
        <BaseTextarea v-model="form.notes" :rows="2" />
      </BaseFormField>

      <div class="flex items-center justify-end gap-3 pt-2">
        <BaseButton type="button" variant="secondary" @click="close">
          Cancelar
        </BaseButton>
        <BaseButton
          type="submit"
          variant="primary"
          :disabled="!canPreview || previewing"
          data-testid="collection-form-preview"
        >
          {{ previewing ? 'Generando...' : 'Previsualizar' }}
        </BaseButton>
      </div>
    </form>

    <!-- ── Step 2: preview ── -->
    <div v-else class="px-6 py-4 space-y-4">
      <div class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-1 text-sm">
        <p class="text-text-default" data-testid="collection-preview-subject">
          <span class="font-medium">Asunto:</span> {{ preview?.subject }}
        </p>
        <p class="text-text-subtle">
          <span class="font-medium text-text-default">Para:</span>
          {{ preview?.customer_email }}
          <span class="mx-1">·</span>
          <span class="font-medium text-text-default">Número:</span>
          {{ preview?.public_number }}
          <span class="mx-1">·</span>
          <span class="font-medium text-text-default">Total:</span>
          {{ formatMoney(Number(preview?.total ?? 0), 'COP') }}
        </p>
      </div>

      <div>
        <p class="text-sm font-medium text-text-default mb-2">Correo que recibirá el cliente</p>
        <iframe
          v-if="preview?.html_body"
          :srcdoc="preview.html_body"
          sandbox=""
          title="Vista previa del correo"
          class="w-full h-64 rounded-xl border border-border-default bg-surface"
          data-testid="collection-preview-email"
        />
      </div>

      <div>
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-medium text-text-default">PDF adjunto</p>
          <BaseButton
            v-if="pdfUrl"
            type="button"
            variant="secondary"
            size="sm"
            data-testid="collection-preview-open-pdf"
            @click="openPdfTab"
          >
            Abrir PDF
          </BaseButton>
        </div>
        <embed
          v-if="pdfUrl"
          :src="pdfUrl"
          type="application/pdf"
          class="w-full h-72 rounded-xl border border-border-default"
          data-testid="collection-preview-pdf"
        >
        <p v-else class="text-sm text-danger-strong">
          No se pudo generar el PDF de previsualización.
        </p>
      </div>

      <div class="flex items-center justify-between gap-3 pt-2">
        <BaseButton
          type="button"
          variant="secondary"
          data-testid="collection-form-back"
          @click="step = 'form'"
        >
          Volver a editar
        </BaseButton>
        <BaseButton
          type="button"
          variant="primary"
          :disabled="saving"
          data-testid="collection-form-confirm"
          @click="confirmSend"
        >
          {{ saving ? 'Enviando...' : 'Confirmar y enviar' }}
        </BaseButton>
      </div>
    </div>
  </BaseModal>

  <!-- Stacked: create the expected income without leaving the flow -->
  <IncomeFormModal
    :open="showIncomeForm"
    :saving="store.isUpdating"
    :locked-client="lockedClientForIncome"
    @close="showIncomeForm = false"
    @submit="handleIncomeCreated"
  />
</template>
