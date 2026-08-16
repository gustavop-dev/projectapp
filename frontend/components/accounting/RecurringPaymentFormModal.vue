<script setup>
import { computed, ref, watch } from 'vue'
import { CUSTOM_FREQUENCY, FREQUENCY_OPTIONS } from '~/utils/recurring'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'submit'])

const isEdit = computed(() => !!props.record)
const title = computed(() =>
  isEdit.value ? 'Editar Pago recurrente' : 'Nuevo Pago recurrente',
)

const currencyOptions = [
  { value: 'COP', label: 'COP' },
  { value: 'USD', label: 'USD' },
]

const paymentMethodOptions = [
  { value: 'cash', label: 'Efectivo' },
  { value: 'credit_card', label: 'T.C' },
]

const frequencyOptions = FREQUENCY_OPTIONS

const costTypeOptions = [
  { value: 'fixed', label: 'Fijo' },
  { value: 'variable', label: 'Variable' },
]

const categoryOptions = computed(() => [
  { value: '', label: 'Sin categoría' },
  ...props.categories.map((category) => ({
    value: category.id,
    label: category.name,
  })),
])

function defaultForm() {
  return {
    name: '',
    price: '',
    currency: 'COP',
    cop_equivalent: '',
    payment_method: 'cash',
    frequency: 'monthly',
    custom_months: '',
    billing_day: '',
    cycle_anchor_date: '',
    cost_type: 'fixed',
    category: '',
    is_active: true,
    notes: '',
  }
}

const form = ref(defaultForm())

const isCustomFrequency = computed(() => form.value.frequency === CUSTOM_FREQUENCY)
const isMonthlyFrequency = computed(() => form.value.frequency === 'monthly')

// A day of the month cannot say *which* month a quarterly or annual charge
// lands on, so anything beyond monthly needs the reference date to be announced.
const anchorHint = computed(() => (
  isMonthlyFrequency.value
    ? 'Opcional: con periodicidad mensual basta el día de cobro.'
    : 'Cualquier cobro conocido. Sin ella este pago no genera avisos.'
))

watch(
  () => [props.open, props.record],
  () => {
    if (!props.open) return
    if (props.record) {
      form.value = {
        name: props.record.name ?? '',
        price: props.record.price ?? '',
        currency: props.record.currency ?? 'COP',
        cop_equivalent: props.record.cop_equivalent ?? '',
        payment_method: props.record.payment_method ?? 'cash',
        frequency: props.record.frequency ?? 'monthly',
        custom_months: props.record.custom_months ?? '',
        billing_day: props.record.billing_day ?? '',
        cycle_anchor_date: props.record.cycle_anchor_date ?? '',
        cost_type: props.record.cost_type ?? 'fixed',
        category: props.record.category ?? '',
        is_active: props.record.is_active ?? true,
        notes: props.record.notes ?? '',
      }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

watch(
  () => form.value.currency,
  (currency) => {
    if (currency === 'COP') form.value.cop_equivalent = ''
  },
)

function onSubmit() {
  const payload = {
    name: form.value.name,
    price: form.value.price,
    currency: form.value.currency,
    payment_method: form.value.payment_method,
    frequency: form.value.frequency,
    // Only a custom cycle carries a month count; the API clears it otherwise.
    custom_months: isCustomFrequency.value && form.value.custom_months !== ''
      ? form.value.custom_months
      : null,
    cost_type: form.value.cost_type,
    // '' is the "Sin categoría" option; the API expects an explicit null.
    category: form.value.category === '' ? null : form.value.category,
    is_active: form.value.is_active,
  }
  if (form.value.currency === 'USD' && form.value.cop_equivalent !== '') {
    payload.cop_equivalent = form.value.cop_equivalent
  }
  payload.billing_day = form.value.billing_day === '' ? null : form.value.billing_day
  payload.cycle_anchor_date =
    form.value.cycle_anchor_date === '' ? null : form.value.cycle_anchor_date
  payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" title-id="recurring-payment-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="recurring-payment-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <BaseFormField label="Nombre" required>
        <BaseInput v-model="form.name" required />
      </BaseFormField>

      <BaseFormRow :cols="2" :gap="4">
        <BaseFormField label="Precio" required>
          <BaseCurrencyInput
            v-model="form.price"
            :decimals="form.currency === 'USD' ? 2 : 0"
            required
          />
        </BaseFormField>
        <BaseFormField label="Moneda">
          <BaseSegmented v-model="form.currency" :options="currencyOptions" full-width />
        </BaseFormField>
      </BaseFormRow>

      <BaseFormField
        v-if="form.currency === 'USD'"
        label="Equivalente COP"
        hint="Para COP se toma el precio automáticamente"
      >
        <BaseCurrencyInput v-model="form.cop_equivalent" />
      </BaseFormField>

      <BaseFormRow :cols="2" :gap="4">
        <BaseFormField label="Método de pago">
          <BaseSelect v-model="form.payment_method" :options="paymentMethodOptions" />
        </BaseFormField>
        <BaseFormField label="Frecuencia">
          <BaseSelect v-model="form.frequency" :options="frequencyOptions" />
        </BaseFormField>
      </BaseFormRow>

      <BaseFormField
        v-if="isCustomFrequency"
        label="Cada cuántos meses"
        hint="El equivalente mensual es el precio dividido entre este número"
        required
      >
        <BaseInput
          v-model="form.custom_months"
          type="number"
          step="1"
          min="1"
          data-testid="recurring-payment-form-custom-months"
        />
      </BaseFormField>

      <BaseFormField
        label="Fecha de referencia del cobro"
        :hint="anchorHint"
      >
        <BaseInput
          v-model="form.cycle_anchor_date"
          type="date"
          data-testid="recurring-payment-form-cycle-anchor-date"
        />
      </BaseFormField>

      <BaseFormRow :cols="2" :gap="4">
        <BaseFormField
          label="Día de cobro"
          :hint="isMonthlyFrequency ? '' : 'Sólo referencial: el próximo cobro sale de la fecha de arriba.'"
        >
          <BaseInput v-model="form.billing_day" type="number" step="1" min="1" max="31" />
        </BaseFormField>
        <BaseFormField label="Tipo de costo">
          <BaseSegmented v-model="form.cost_type" :options="costTypeOptions" full-width />
        </BaseFormField>
      </BaseFormRow>

      <BaseFormField label="Categoría" hint="Agrupa el recurrente en la vista por categorías">
        <BaseSelect
          v-model="form.category"
          :options="categoryOptions"
          data-testid="recurring-payment-form-category"
        />
      </BaseFormField>

      <BaseFormField label="Activo">
        <BaseToggle v-model="form.is_active" aria-label="Activo" />
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
          data-testid="recurring-payment-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
