<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const isEdit = computed(() => !!props.record)
const title = computed(() => (isEdit.value ? 'Editar Gasto en Ads' : 'Nuevo Gasto en Ads'))

const platformOptions = [
  { value: 'facebook', label: 'Facebook Ads' },
  { value: 'google', label: 'Google Ads' },
  { value: 'other', label: 'Otro' },
]

function defaultForm() {
  return {
    spend_date: '',
    platform: 'facebook',
    origin_card: '',
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
        spend_date: props.record.spend_date ?? '',
        platform: props.record.platform ?? 'facebook',
        origin_card: props.record.origin_card ?? '',
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
    spend_date: form.value.spend_date,
    platform: form.value.platform,
    amount: form.value.amount,
  }
  payload.origin_card = form.value.origin_card
  payload.notes = form.value.notes
  emit('submit', payload)
}
</script>

<template>
  <BaseModal :model-value="open" size="lg" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 class="text-lg font-bold text-text-default">{{ title }}</h3>
    </div>
    <form class="px-6 py-4 space-y-4" @submit.prevent="onSubmit">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Fecha" required>
          <BaseInput v-model="form.spend_date" type="date" required />
        </BaseFormField>
        <BaseFormField label="Plataforma">
          <BaseSelect v-model="form.platform" :options="platformOptions" />
        </BaseFormField>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BaseFormField label="Tarjeta origen">
          <BaseInput v-model="form.origin_card" placeholder="T.C 0655" />
        </BaseFormField>
        <BaseFormField label="Valor" required>
          <BaseInput v-model="form.amount" type="number" step="0.01" min="0" required />
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
          data-testid="ad-spend-form-submit"
        >
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
