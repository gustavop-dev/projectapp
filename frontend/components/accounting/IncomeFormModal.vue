<script setup>
import { computed, ref, watch } from 'vue'
import PartnerSplitInput from './PartnerSplitInput.vue'
import PeriodDateField from './PeriodDateField.vue'
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue'
import ProjectSelect from '~/components/accounting/ProjectSelect.vue'
import ClientFormFields from '~/components/clients/ClientFormFields.vue'
import { useProposalClientsStore } from '~/stores/proposal_clients'
import { clientFormPayload, emptyClientForm } from '~/utils/billingCode'
import { todayISO } from '~/utils/periodDates'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
  /**
   * Client fixed by the parent (id + display name). Set when this modal is
   * stacked inside the cuenta-de-cobro flow, where the client was already
   * chosen: a second picker there would be redundant and could contradict it.
   */
  lockedClient: { type: Object, default: null },
  /**
   * Prefill for a form that still creates: duplicating an income opens here
   * with the original's data but no `record`, so saving POSTs a new row
   * instead of editing the one it was copied from.
   */
  seed: { type: Object, default: null },
})

const emit = defineEmits(['close', 'submit'])

const clientsStore = useProposalClientsStore()
const creatingClient = ref(false)
const inlineClientOpen = ref(false)
const inlineClient = ref(emptyClientForm())

const originOptions = [
  { value: 'development', label: 'Desarrollo' },
  { value: 'hosting', label: 'Hosting' },
  { value: 'diagnostic', label: 'Diagnóstico' },
  { value: 'other', label: 'Otro' },
]

const isEdit = computed(() => !!props.record)
const isDuplicate = computed(() => !props.record && !!props.seed)
const title = computed(() => {
  if (isEdit.value) return 'Editar Ingreso'
  return isDuplicate.value ? 'Duplicar Ingreso' : 'Nuevo Ingreso'
})

const kindOptions = [
  { value: 'expected', label: 'Esperado' },
  { value: 'liquid', label: 'Líquido' },
  { value: 'lost', label: 'Perdido' },
]

const destinationOptions = [
  { value: 'partners', label: 'Socios' },
  { value: 'pocket', label: 'Bolsillo ProjectApp' },
]

const ledgerOptions = [
  { value: 'company', label: 'Empresa' },
  { value: 'gustavo', label: 'Personal Gustavo' },
  { value: 'carlos', label: 'Personal Carlos' },
]

function defaultForm() {
  return {
    concept: '',
    kind: 'expected',
    period_date: todayISO(),
    destination: 'partners',
    ledger: 'company',
    client: null,
    project: null,
    client_name: '',
    origin: '',
    total_amount: '',
    gustavo_amount: '',
    carlos_amount: '',
    notes: '',
  }
}

const form = ref(defaultForm())
// Exact day by default; the toggle downgrades to month-only.
const exactDate = ref(true)

const isPersonal = computed(() => form.value.ledger !== 'company')

// Only while the proposed date is untouched: once it changes, the hint would
// be describing a date that is no longer the one the hosting cycle produced.
const showsCycleHint = computed(
  () => isDuplicate.value
    && props.seed?.period_date_source === 'hosting_cycle'
    && form.value.period_date === props.seed.period_date,
)

const CYCLE_LABELS = { 1: '+1 mes', 3: '+3 meses', 6: '+6 meses', 12: '+1 año' }

/**
 * Shortcuts to the next period, offered only while duplicating: a create has
 * no original to count from and an edit is not opening a new period. The
 * dates are computed by the server (`add_months` clamps the day, and this
 * codebase keeps every date advance backend-side), so this only picks one.
 */
const cycleOptions = computed(
  () => (isDuplicate.value ? props.seed?.cycle_options ?? [] : []),
)

function cycleLabel(months) {
  return CYCLE_LABELS[months] ?? `+${months} meses`
}

// Match the field's current granularity: month mode stores 'YYYY-MM', so
// handing it a full date would leave the month input showing nothing.
function cycleValue(option) {
  return exactDate.value ? option.date : option.date.slice(0, 7)
}

function isCycleActive(option) {
  return !!form.value.period_date && form.value.period_date === cycleValue(option)
}

function applyCycle(option) {
  form.value.period_date = cycleValue(option)
}

/**
 * Copy the fields the form owns out of an existing income — the record being
 * edited, or the draft a duplicate was seeded with. A duplicate may arrive
 * with no `period_date` (nothing to propose): it stays empty and the field's
 * `required` forces a date before saving.
 */
function applyRecord(source) {
  form.value = {
    concept: source.concept ?? '',
    kind: source.kind ?? 'expected',
    period_date: source.period_date ?? '',
    destination: source.destination ?? 'partners',
    ledger: source.ledger ?? 'company',
    client: source.client ?? null,
    project: source.project ?? null,
    client_name: source.client_name ?? '',
    origin: source.origin ?? '',
    total_amount: source.total_amount ?? '',
    gustavo_amount: source.gustavo_amount ?? '',
    carlos_amount: source.carlos_amount ?? '',
    notes: source.notes ?? '',
  }
}

watch(
  () => [props.open, props.record, props.seed],
  () => {
    if (!props.open) return
    // Prefill from the raw period_date — `period` is 'YYYY-MM' and would
    // silently reset the day to the 1st on every edit. Edits always open
    // in full-date mode showing the stored day (01 for month-only
    // records, whose real day was never captured); the toggle still
    // downgrades when only the month is known.
    exactDate.value = true
    const source = props.record || props.seed
    if (source) applyRecord(source)
    else form.value = defaultForm()
    inlineClientOpen.value = false
    if (props.lockedClient) {
      form.value.client = props.lockedClient.id ?? null
      form.value.client_name = props.lockedClient.name ?? ''
    }
  },
  { immediate: true },
)

function onClientSelect(client) {
  form.value.client_name = client?.name || ''
}

function onCreateNewClient(typedName) {
  inlineClientOpen.value = true
  inlineClient.value = { ...emptyClientForm(), name: typedName || '' }
}

async function createInlineClient() {
  creatingClient.value = true
  const result = await clientsStore.createClient(clientFormPayload(inlineClient.value))
  creatingClient.value = false
  if (result.success && result.data?.id) {
    inlineClientOpen.value = false
    form.value.client = result.data.id
    form.value.client_name = result.data.name || ''
  }
}

function onSubmit() {
  const payload = {
    concept: form.value.concept,
    kind: form.value.kind,
    period_date: form.value.period_date,
    // Pocket is liquid-and-company-only server-side. Deriving here (the
    // same condition that shows the Destino field) instead of syncing via
    // watches keeps the user's pocket choice across a liquid→lost→liquid
    // round-trip.
    destination:
      form.value.kind === 'liquid' && !isPersonal.value
        ? form.value.destination
        : 'partners',
    ledger: form.value.ledger,
    total_amount: form.value.total_amount,
    // Always sent, null included: that is what lets an edit UNLINK a client
    // (same reason `notes` is always sent).
    client: form.value.client,
    // Always sent, null included: that is what lets an edit unlink it.
    project: form.value.project,
    origin: form.value.origin,
  }
  if (!isPersonal.value) {
    payload.gustavo_amount = form.value.gustavo_amount
    payload.carlos_amount = form.value.carlos_amount
  }
  payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" title-id="income-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="income-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <BaseFormField label="Concepto" required>
        <BaseInput v-model="form.concept" data-testid="income-form-concept" required />
      </BaseFormField>

      <BaseFormField label="Cliente" hint="Opcional: un reembolso o un rendimiento no tiene cliente.">
        <div
          v-if="lockedClient"
          class="rounded-xl border border-border-default bg-surface-raised px-3 py-2.5 text-sm text-text-default"
          data-testid="income-form-client-locked"
        >
          {{ form.client_name || lockedClient.name }}
        </div>
        <ClientAutocomplete
          v-else
          v-model="form.client"
          :initial-label="form.client_name"
          test-id="income-form-client"
          @select="onClientSelect"
          @create-new="onCreateNewClient"
        />
      </BaseFormField>

      <ProjectSelect
        v-model="form.project"
        :client-profile-id="form.client"
        testid="income-form-project"
      />

      <!-- Inline client creation: the module de clientes without leaving the form -->
      <div
        v-if="inlineClientOpen"
        class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-3"
        data-testid="income-form-inline-client"
      >
        <p class="text-sm font-medium text-text-default">Crear cliente nuevo</p>
        <ClientFormFields
          v-model="inlineClient"
          testid-prefix="income-form-inline-client"
          dense
        />
        <div class="flex justify-end gap-2">
          <BaseButton type="button" variant="secondary" size="sm" @click="inlineClientOpen = false">
            Cancelar
          </BaseButton>
          <BaseButton
            type="button"
            variant="primary"
            size="sm"
            :disabled="creatingClient"
            data-testid="income-form-inline-client-save"
            @click="createInlineClient"
          >
            {{ creatingClient ? 'Creando...' : 'Crear cliente' }}
          </BaseButton>
        </div>
      </div>

      <BaseFormField label="Origen" hint="Línea de negocio que genera el ingreso.">
        <BaseSegmented
          v-model="form.origin"
          :options="originOptions"
          full-width
          data-testid="income-form-origin"
        />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Tipo" required>
          <BaseSegmented v-model="form.kind" :options="kindOptions" full-width />
        </BaseFormField>
        <div>
          <PeriodDateField
            v-model="form.period_date"
            v-model:exact="exactDate"
            label-exact="Fecha"
            label-month="Mes"
            required
            input-testid="income-form-period"
            toggle-testid="income-form-exact-date"
          />
          <p
            v-if="showsCycleHint"
            class="mt-1 text-xs text-text-subtle"
            data-testid="income-form-period-hint"
          >
            Siguiente ciclo del hosting. Ajústala si no corresponde.
          </p>
          <div v-if="cycleOptions.length" class="mt-2">
            <p class="mb-1.5 text-xs text-text-subtle">Siguiente período:</p>
            <div class="flex flex-wrap gap-1.5" data-testid="income-form-cycles">
              <BaseButton
                v-for="option in cycleOptions"
                :key="option.months"
                type="button"
                size="sm"
                :variant="isCycleActive(option) ? 'primary' : 'secondary'"
                :aria-pressed="isCycleActive(option)"
                :data-testid="`income-form-cycle-${option.months}`"
                @click="applyCycle(option)"
              >
                {{ cycleLabel(option.months) }}
              </BaseButton>
            </div>
          </div>
        </div>
      </div>

      <BaseFormField label="Contabilidad">
        <BaseSegmented v-model="form.ledger" :options="ledgerOptions" full-width />
      </BaseFormField>

      <BaseFormField v-if="form.kind === 'liquid' && !isPersonal" label="Destino">
        <BaseSegmented v-model="form.destination" :options="destinationOptions" full-width />
      </BaseFormField>

      <PartnerSplitInput
        v-if="!isPersonal"
        v-model:total="form.total_amount"
        v-model:gustavoAmount="form.gustavo_amount"
        v-model:carlosAmount="form.carlos_amount"
      />

      <BaseFormField v-else label="Valor" required>
        <BaseCurrencyInput v-model="form.total_amount" required />
      </BaseFormField>

      <BaseFormField label="Notas">
        <BaseTextarea v-model="form.notes" :rows="3" />
      </BaseFormField>

      <div class="flex items-center justify-end gap-3 pt-2">
        <BaseButton type="button" variant="secondary" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton
          type="submit"
          variant="primary"
          :disabled="saving"
          data-testid="income-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
