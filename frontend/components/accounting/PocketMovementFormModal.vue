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

const ledgerOptions = [
  { value: 'company', label: 'Empresa' },
  { value: 'gustavo', label: 'Personal Gustavo' },
  { value: 'carlos', label: 'Personal Carlos' },
]

function defaultForm() {
  return {
    concept: '',
    movement_date: '',
    direction: 'in',
    amount: '',
    ledger: 'company',
    notes: '',
  }
}

const form = ref(defaultForm())

const isLinked = computed(() => isEdit.value && !!props.record?.is_auto_managed)
// Historical movements (unlinked) have no mirrored record to assign a ledger to.
const showLedger = computed(() => !isEdit.value || isLinked.value)
const directionLocked = computed(() => isLinked.value)

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
        ledger: props.record.linked_ledger ?? 'company',
        notes: props.record.notes ?? '',
      }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

// Pocket IN feeds the company pocket: personal ledgers only apply to egresos.
watch(
  () => form.value.direction,
  (direction) => {
    if (direction === 'in') form.value.ledger = 'company'
  },
)

function onSubmit() {
  const payload = {
    concept: form.value.concept,
    movement_date: form.value.movement_date,
    direction: form.value.direction,
    amount: form.value.amount,
  }
  if (showLedger.value) payload.ledger = form.value.ledger
  payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" title-id="pocket-movement-form-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="pocket-movement-form-title" class="text-lg font-bold text-text-default">{{ title }}</h3>
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
          <BaseSegmented
            v-model="form.direction"
            :options="directionOptions"
            :disabled="directionLocked"
            full-width
          />
          <p v-if="directionLocked" class="text-xs text-text-subtle mt-1">
            La dirección se fija al crear el movimiento vinculado.
          </p>
        </BaseFormField>
      </div>

      <BaseFormField v-if="showLedger" label="Contabilidad" required>
        <BaseSegmented
          v-model="form.ledger"
          :options="ledgerOptions"
          :disabled="form.direction === 'in'"
          full-width
          data-testid="pocket-movement-ledger"
        />
        <p v-if="form.direction === 'in'" class="text-xs text-text-subtle mt-1">
          Los ingresos al bolsillo siempre son de la empresa.
        </p>
      </BaseFormField>

      <BaseFormField label="Valor" required>
        <BaseCurrencyInput v-model="form.amount" required />
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
