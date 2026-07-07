<script setup>
import { computed, ref, watch } from 'vue'
import PartnerSplitInput from './PartnerSplitInput.vue'

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

const paidFromOptions = [
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
    period_date: '',
    category: 'business',
    paid_from: 'partners',
    ledger: 'company',
    total_amount: '',
    gustavo_amount: '',
    carlos_amount: '',
    notes: '',
  }
}

const form = ref(defaultForm())

const isPersonal = computed(() => form.value.ledger !== 'company')

watch(
  () => [props.open, props.record],
  () => {
    if (!props.open) return
    if (props.record) {
      form.value = {
        concept: props.record.concept ?? '',
        period_date: props.record.period ?? '',
        category: props.record.category ?? 'business',
        paid_from: props.record.paid_from ?? 'partners',
        ledger: props.record.ledger ?? 'company',
        total_amount: props.record.total_amount ?? '',
        gustavo_amount: props.record.gustavo_amount ?? '',
        carlos_amount: props.record.carlos_amount ?? '',
        notes: props.record.notes ?? '',
      }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

watch(
  () => form.value.ledger,
  (ledger) => {
    if (ledger !== 'company') form.value.paid_from = 'partners'
  },
)

function onSubmit() {
  const payload = {
    concept: form.value.concept,
    period_date: form.value.period_date,
    category: form.value.category,
    paid_from: form.value.paid_from,
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
  <BaseModal :model-value="open" size="lg" title-id="expense-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="expense-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <BaseFormField label="Concepto" required>
        <BaseInput v-model="form.concept" required />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Mes" required>
          <BaseInput v-model="form.period_date" type="month" required />
        </BaseFormField>
        <BaseFormField label="Categoría">
          <BaseSelect v-model="form.category" :options="categoryOptions" />
        </BaseFormField>
      </div>

      <BaseFormField label="Contabilidad">
        <BaseSegmented v-model="form.ledger" :options="ledgerOptions" full-width />
      </BaseFormField>

      <BaseFormField v-if="!isPersonal" label="Pagado desde">
        <BaseSegmented v-model="form.paid_from" :options="paidFromOptions" full-width />
      </BaseFormField>

      <PartnerSplitInput
        v-if="!isPersonal"
        v-model:total="form.total_amount"
        v-model:gustavoAmount="form.gustavo_amount"
        v-model:carlosAmount="form.carlos_amount"
      />

      <BaseFormField v-else label="Valor" required>
        <BaseInput
          v-model="form.total_amount"
          type="number"
          min="0"
          step="0.01"
          required
        />
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
          data-testid="expense-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
