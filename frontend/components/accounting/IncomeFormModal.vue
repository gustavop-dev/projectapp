<script setup>
import { computed, ref, watch } from 'vue'
import PartnerSplitInput from './PartnerSplitInput.vue'
import PeriodDateField from './PeriodDateField.vue'
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue'
import { useProposalClientsStore } from '~/stores/proposal_clients'
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
})

const emit = defineEmits(['close', 'submit'])

const clientsStore = useProposalClientsStore()
const creatingClient = ref(false)
const inlineClientOpen = ref(false)
const inlineClient = ref({ name: '', email: '', company: '' })

const originOptions = [
  { value: 'development', label: 'Desarrollo' },
  { value: 'hosting', label: 'Hosting' },
  { value: 'diagnostic', label: 'Diagnóstico' },
  { value: 'other', label: 'Otro' },
]

const isEdit = computed(() => !!props.record)
const title = computed(() => (isEdit.value ? 'Editar Ingreso' : 'Nuevo Ingreso'))

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

watch(
  () => [props.open, props.record],
  () => {
    if (!props.open) return
    if (props.record) {
      // Prefill from the raw period_date — `period` is 'YYYY-MM' and would
      // silently reset the day to the 1st on every edit. Edits always open
      // in full-date mode showing the stored day (01 for month-only
      // records, whose real day was never captured); the toggle still
      // downgrades when only the month is known.
      exactDate.value = true
      form.value = {
        concept: props.record.concept ?? '',
        kind: props.record.kind ?? 'expected',
        period_date: props.record.period_date ?? '',
        destination: props.record.destination ?? 'partners',
        ledger: props.record.ledger ?? 'company',
        client: props.record.client ?? null,
        client_name: props.record.client_name ?? '',
        origin: props.record.origin ?? '',
        total_amount: props.record.total_amount ?? '',
        gustavo_amount: props.record.gustavo_amount ?? '',
        carlos_amount: props.record.carlos_amount ?? '',
        notes: props.record.notes ?? '',
      }
    } else {
      exactDate.value = true
      form.value = defaultForm()
    }
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
  inlineClient.value = { name: typedName || '', email: '', company: '' }
}

async function createInlineClient() {
  creatingClient.value = true
  const result = await clientsStore.createClient({ ...inlineClient.value })
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

      <!-- Inline client creation: the module de clientes without leaving the form -->
      <div
        v-if="inlineClientOpen"
        class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-3"
        data-testid="income-form-inline-client"
      >
        <p class="text-sm font-medium text-text-default">Crear cliente nuevo</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <BaseFormField label="Nombre">
            <BaseInput v-model="inlineClient.name" data-testid="income-form-inline-client-name" />
          </BaseFormField>
          <BaseFormField label="Email">
            <BaseInput v-model="inlineClient.email" type="email" />
          </BaseFormField>
          <BaseFormField label="Empresa">
            <BaseInput v-model="inlineClient.company" />
          </BaseFormField>
        </div>
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
        <PeriodDateField
          v-model="form.period_date"
          v-model:exact="exactDate"
          label-exact="Fecha"
          label-month="Mes"
          required
          input-testid="income-form-period"
          toggle-testid="income-form-exact-date"
        />
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
