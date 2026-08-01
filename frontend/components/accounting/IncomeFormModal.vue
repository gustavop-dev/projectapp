<script setup>
import { computed, ref, watch } from 'vue'
import PartnerSplitInput from './PartnerSplitInput.vue'
import PeriodDateField from './PeriodDateField.vue'
import { todayISO } from '~/utils/periodDates'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

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
      // silently reset the day to the 1st on every edit. Day 1 IS the
      // month-only convention, so it prefills in month mode.
      const periodDate = props.record.period_date ?? ''
      exactDate.value = !!periodDate && !periodDate.endsWith('-01')
      form.value = {
        concept: props.record.concept ?? '',
        kind: props.record.kind ?? 'expected',
        period_date: exactDate.value ? periodDate : periodDate.slice(0, 7),
        destination: props.record.destination ?? 'partners',
        ledger: props.record.ledger ?? 'company',
        total_amount: props.record.total_amount ?? '',
        gustavo_amount: props.record.gustavo_amount ?? '',
        carlos_amount: props.record.carlos_amount ?? '',
        notes: props.record.notes ?? '',
      }
    } else {
      exactDate.value = true
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

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
