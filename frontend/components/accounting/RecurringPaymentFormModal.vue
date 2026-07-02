<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
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

const frequencyOptions = [
  { value: 'monthly', label: 'Mensual' },
  { value: 'annual', label: 'Anual' },
  { value: 'biennial', label: 'Cada 2 años' },
  { value: 'triennial', label: 'Cada 3 años' },
]

const costTypeOptions = [
  { value: 'fixed', label: 'Fijo' },
  { value: 'variable', label: 'Variable' },
]

function defaultForm() {
  return {
    name: '',
    price: '',
    currency: 'COP',
    cop_equivalent: '',
    payment_method: 'cash',
    frequency: 'monthly',
    billing_day: '',
    cost_type: 'fixed',
    is_active: true,
    notes: '',
  }
}

const form = ref(defaultForm())

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
        billing_day: props.record.billing_day ?? '',
        cost_type: props.record.cost_type ?? 'fixed',
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
    cost_type: form.value.cost_type,
    is_active: form.value.is_active,
  }
  if (form.value.currency === 'USD' && form.value.cop_equivalent !== '') {
    payload.cop_equivalent = form.value.cop_equivalent
  }
  if (form.value.billing_day !== '') payload.billing_day = form.value.billing_day
  if (form.value.notes) payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <BaseFormField label="Nombre" required>
        <BaseInput v-model="form.name" required />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Precio" required>
          <BaseInput v-model="form.price" type="number" step="0.01" min="0" required />
        </BaseFormField>
        <BaseFormField label="Moneda">
          <BaseSegmented v-model="form.currency" :options="currencyOptions" full-width />
        </BaseFormField>
      </div>

      <BaseFormField
        v-if="form.currency === 'USD'"
        label="Equivalente COP"
        hint="Para COP se toma el precio automáticamente"
      >
        <BaseInput v-model="form.cop_equivalent" type="number" step="0.01" min="0" />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Método de pago">
          <BaseSelect v-model="form.payment_method" :options="paymentMethodOptions" />
        </BaseFormField>
        <BaseFormField label="Frecuencia">
          <BaseSelect v-model="form.frequency" :options="frequencyOptions" />
        </BaseFormField>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Día de cobro">
          <BaseInput v-model="form.billing_day" type="number" step="1" min="1" max="31" />
        </BaseFormField>
        <BaseFormField label="Tipo de costo">
          <BaseSegmented v-model="form.cost_type" :options="costTypeOptions" full-width />
        </BaseFormField>
      </div>

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
