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
const title = computed(() => (isEdit.value ? 'Editar Ingreso' : 'Nuevo Ingreso'))

const kindOptions = [
  { value: 'expected', label: 'Esperado' },
  { value: 'liquid', label: 'Líquido' },
]

const destinationOptions = [
  { value: 'partners', label: 'Socios' },
  { value: 'pocket', label: 'Bolsillo ProjectApp' },
]

function defaultForm() {
  return {
    concept: '',
    kind: 'expected',
    period_date: '',
    destination: 'partners',
    total_amount: '',
    gustavo_amount: '',
    carlos_amount: '',
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
        concept: props.record.concept ?? '',
        kind: props.record.kind ?? 'expected',
        period_date: props.record.period ?? '',
        destination: props.record.destination ?? 'partners',
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
  () => form.value.kind,
  (kind) => {
    if (kind === 'expected') form.value.destination = 'partners'
  },
)

function onSubmit() {
  const payload = {
    concept: form.value.concept,
    kind: form.value.kind,
    period_date: form.value.period_date,
    destination: form.value.destination,
    total_amount: form.value.total_amount,
    gustavo_amount: form.value.gustavo_amount,
    carlos_amount: form.value.carlos_amount,
  }
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
      <BaseFormField label="Concepto" required>
        <BaseInput v-model="form.concept" required />
      </BaseFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Tipo" required>
          <BaseSegmented v-model="form.kind" :options="kindOptions" full-width />
        </BaseFormField>
        <BaseFormField label="Mes" required>
          <BaseInput v-model="form.period_date" type="month" required />
        </BaseFormField>
      </div>

      <BaseFormField v-if="form.kind === 'liquid'" label="Destino">
        <BaseSegmented v-model="form.destination" :options="destinationOptions" full-width />
      </BaseFormField>

      <PartnerSplitInput
        v-model:total="form.total_amount"
        v-model:gustavoAmount="form.gustavo_amount"
        v-model:carlosAmount="form.carlos_amount"
      />

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
