<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const isEdit = computed(() => !!props.record)
const title = computed(() => (isEdit.value ? 'Editar Hosting' : 'Nuevo Hosting'))

const modalityOptions = [
  { value: 'monthly', label: 'Mensual' },
  { value: 'quarterly', label: 'Trimestral' },
  { value: 'semiannual', label: 'Semestral' },
  { value: 'annual', label: 'Anual' },
]

function defaultForm() {
  return {
    client_name: '',
    domain_url: '',
    monthly_value: '',
    payment_modality: 'monthly',
    benefit: '',
    valid_from: '',
    valid_to: '',
    cycles_count: '',
    payment_per_cycle: '',
    total_paid: '',
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
        client_name: props.record.client_name ?? '',
        domain_url: props.record.domain_url ?? '',
        monthly_value: props.record.monthly_value ?? '',
        payment_modality: props.record.payment_modality ?? 'monthly',
        benefit: props.record.benefit ?? '',
        valid_from: props.record.valid_from ?? '',
        valid_to: props.record.valid_to ?? '',
        cycles_count: props.record.cycles_count ?? '',
        payment_per_cycle: props.record.payment_per_cycle ?? '',
        total_paid: props.record.total_paid ?? '',
        is_active: props.record.is_active ?? true,
        notes: props.record.notes ?? '',
      }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

function addIfFilled(payload, key, value) {
  if (value !== '' && value !== null && value !== undefined) payload[key] = value
}

function onSubmit() {
  const payload = {
    client_name: form.value.client_name,
    monthly_value: form.value.monthly_value,
    payment_modality: form.value.payment_modality,
    is_active: form.value.is_active,
  }
  payload.domain_url = form.value.domain_url
  payload.benefit = form.value.benefit
  payload.notes = form.value.notes
  payload.valid_from = form.value.valid_from || null
  payload.valid_to = form.value.valid_to || null
  addIfFilled(payload, 'cycles_count', form.value.cycles_count)
  addIfFilled(payload, 'payment_per_cycle', form.value.payment_per_cycle)
  addIfFilled(payload, 'total_paid', form.value.total_paid)
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" title-id="hosting-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="hosting-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Cliente" required>
          <BaseInput v-model="form.client_name" required />
        </BaseFormField>
        <BaseFormField label="Dominio">
          <BaseInput v-model="form.domain_url" placeholder="https://ejemplo.com" />
        </BaseFormField>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Valor por mes" required>
          <BaseCurrencyInput v-model="form.monthly_value" required />
        </BaseFormField>
        <BaseFormField label="Modalidad de pago">
          <BaseSelect v-model="form.payment_modality" :options="modalityOptions" />
        </BaseFormField>
      </div>

      <BaseFormField label="Beneficio">
        <BaseInput v-model="form.benefit" />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Vigente desde">
          <BaseInput v-model="form.valid_from" type="date" />
        </BaseFormField>
        <BaseFormField label="Vigente hasta">
          <BaseInput v-model="form.valid_to" type="date" />
        </BaseFormField>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Ciclos">
          <BaseInput v-model="form.cycles_count" type="number" step="1" min="0" />
        </BaseFormField>
        <BaseFormField
          label="Pago por ciclo"
          hint="Si lo dejas vacío al crear, se calcula desde la modalidad"
        >
          <BaseCurrencyInput v-model="form.payment_per_cycle" />
        </BaseFormField>
      </div>

      <BaseFormField label="Total pagado a la fecha">
        <BaseCurrencyInput v-model="form.total_paid" />
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
          data-testid="hosting-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
