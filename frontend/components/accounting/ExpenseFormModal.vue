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
const title = computed(() => (isEdit.value ? 'Editar Gasto' : 'Nuevo Gasto'))

const categoryOptions = [
  { value: 'business', label: 'Negocio' },
  { value: 'personal', label: 'Personal' },
]

const ledgerOptions = [
  { value: 'company', label: 'Empresa' },
  { value: 'gustavo', label: 'Personal Gustavo' },
  { value: 'carlos', label: 'Personal Carlos' },
]

function defaultForm() {
  return {
    concept: '',
    period_date: todayISO(),
    category: 'business',
    ledger: 'company',
    total_amount: '',
    gustavo_amount: '',
    carlos_amount: '',
    register_in_pocket: true,
    notes: '',
  }
}

const form = ref(defaultForm())
// Exact payment day by default; the toggle downgrades to month-only.
const exactDate = ref(true)

const isPersonal = computed(() => form.value.ledger !== 'company')
// Deductions are born in the settlement flow; here they only get their
// amounts/notes touched, and the pocket toggle disappears — the backend
// forces register_in_pocket off for them anyway.
const isDeduction = computed(() => !!props.record?.deduction_type)

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
        period_date: exactDate.value ? periodDate : periodDate.slice(0, 7),
        category: props.record.category ?? 'business',
        ledger: props.record.ledger ?? 'company',
        total_amount: props.record.total_amount ?? '',
        gustavo_amount: props.record.gustavo_amount ?? '',
        carlos_amount: props.record.carlos_amount ?? '',
        register_in_pocket: props.record.pocket_movement != null,
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
    period_date: form.value.period_date,
    category: form.value.category,
    ledger: form.value.ledger,
    total_amount: form.value.total_amount,
  }
  if (!isPersonal.value) {
    payload.gustavo_amount = form.value.gustavo_amount
    payload.carlos_amount = form.value.carlos_amount
  }
  if (!isDeduction.value) {
    payload.register_in_pocket = form.value.register_in_pocket
  }
  payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" title-id="expense-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="expense-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <BaseFormField label="Concepto" required>
        <BaseInput v-model="form.concept" required />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <PeriodDateField
          v-model="form.period_date"
          v-model:exact="exactDate"
          label-exact="Fecha"
          label-month="Mes"
          required
          input-testid="expense-form-period"
          toggle-testid="expense-form-exact-date"
        />
        <BaseFormField label="Categoría">
          <BaseSelect v-model="form.category" :options="categoryOptions" />
        </BaseFormField>
      </div>

      <BaseFormField label="Contabilidad">
        <BaseSegmented v-model="form.ledger" :options="ledgerOptions" full-width />
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

      <div
        v-if="isDeduction"
        class="text-xs text-info-strong bg-info-soft rounded-lg px-3 py-2"
        data-testid="expense-deduction-edit-hint"
      >
        Deducción sobre ingreso ({{ record.deduction_type_label }}) — se crea
        desde Liquidar y nunca registra egreso en bolsillo.
      </div>
      <div v-else class="flex items-center justify-between gap-3">
        <div>
          <p class="text-sm font-medium text-text-default">Registrar egreso en bolsillo</p>
          <p class="text-xs text-text-subtle">
            Desactívalo para ajustes contables o gastos que no salieron del bolsillo.
          </p>
          <p
            v-if="isPersonal && form.register_in_pocket"
            class="text-xs text-warning-strong mt-1"
            data-testid="expense-pocket-draw-hint"
          >
            Al salir del bolsillo se registrará como retiro de la empresa
            asignado 100% al socio.
          </p>
        </div>
        <BaseToggle
          v-model="form.register_in_pocket"
          aria-label="Registrar egreso en bolsillo"
          data-testid="expense-register-in-pocket"
        />
      </div>

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
          data-testid="expense-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
