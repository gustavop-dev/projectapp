<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
  knownCards: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'submit'])

const isEdit = computed(() => !!props.record)
const title = computed(() =>
  isEdit.value ? 'Editar Registro de Tarjeta' : 'Nuevo Registro de Tarjeta',
)

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function defaultForm() {
  return {
    snapshot_date: todayIso(),
    card_name: '',
    available_amount: '',
    debt_amount: '',
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
        snapshot_date: props.record.snapshot_date ?? todayIso(),
        card_name: props.record.card_name ?? '',
        available_amount: props.record.available_amount ?? '',
        debt_amount: props.record.debt_amount ?? '',
        notes: props.record.notes ?? '',
      }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true },
)

function onSubmit() {
  emit('submit', {
    snapshot_date: form.value.snapshot_date,
    card_name: form.value.card_name,
    available_amount: form.value.available_amount,
    debt_amount: form.value.debt_amount,
    notes: form.value.notes,
  })
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Tarjeta" required>
          <BaseInput
            v-model="form.card_name"
            list="card-snapshot-known-cards"
            placeholder="T.C 0064"
            required
          />
          <datalist id="card-snapshot-known-cards">
            <option v-for="card in knownCards" :key="card" :value="card" />
          </datalist>
        </BaseFormField>
        <BaseFormField label="Fecha" required>
          <BaseInput v-model="form.snapshot_date" type="date" required />
        </BaseFormField>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Disponible" required>
          <BaseInput
            v-model="form.available_amount"
            type="number"
            min="0"
            step="0.01"
            required
          />
        </BaseFormField>
        <BaseFormField label="Deuda" required>
          <BaseInput
            v-model="form.debt_amount"
            type="number"
            min="0"
            step="0.01"
            required
          />
        </BaseFormField>
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
          data-testid="card-snapshot-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
