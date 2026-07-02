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
  isEdit.value ? 'Editar Movimiento de bolsillo' : 'Nuevo Movimiento de bolsillo',
)

const directionOptions = [
  { value: 'in', label: 'Ingreso' },
  { value: 'out', label: 'Egreso' },
]

function defaultForm() {
  return {
    concept: '',
    movement_date: '',
    direction: 'in',
    amount: '',
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
        movement_date: props.record.movement_date ?? '',
        direction: props.record.direction ?? 'in',
        amount: props.record.amount ?? '',
        notes: props.record.notes ?? '',
      }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

function onSubmit() {
  const payload = {
    concept: form.value.concept,
    movement_date: form.value.movement_date,
    direction: form.value.direction,
    amount: form.value.amount,
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
        <BaseFormField label="Fecha" required>
          <BaseInput v-model="form.movement_date" type="date" required />
        </BaseFormField>
        <BaseFormField label="Dirección" required>
          <BaseSegmented v-model="form.direction" :options="directionOptions" full-width />
        </BaseFormField>
      </div>

      <BaseFormField label="Valor" required>
        <BaseInput v-model="form.amount" type="number" step="0.01" min="0.01" required />
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
          data-testid="pocket-movement-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
