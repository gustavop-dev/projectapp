<script setup>
import { watch } from 'vue'

/**
 * Period input honouring the accounting convention: day 1 means
 * "month only", any other day is the exact date. Exact mode is the
 * parent's choice via `v-model:exact`; the toggle downgrades to month
 * granularity when only the month is known.
 */
const model = defineModel({ type: [String, null], default: '' })
const exact = defineModel('exact', { type: Boolean, default: true })

defineProps({
  labelExact: { type: String, required: true },
  labelMonth: { type: String, required: true },
  toggleLabel: { type: String, default: 'Registrar el día exacto' },
  required: { type: Boolean, default: false },
  inputTestid: { type: String, default: '' },
  toggleTestid: { type: String, default: '' },
})

// Keep whatever was typed when flipping modes: 'YYYY-MM' ⇄ 'YYYY-MM-DD'.
watch(exact, (isExact) => {
  const value = model.value
  if (!value) return
  model.value = isExact ? `${value.slice(0, 7)}-01` : value.slice(0, 7)
})
</script>

<template>
  <BaseFormField :label="exact ? labelExact : labelMonth" :required="required">
    <BaseInput
      v-model="model"
      :type="exact ? 'date' : 'month'"
      :required="required"
      :data-testid="inputTestid || undefined"
    />
    <label class="flex items-center gap-2 mt-2 text-xs text-text-subtle">
      <BaseToggle
        v-model="exact"
        :aria-label="toggleLabel"
        :data-testid="toggleTestid || undefined"
      />
      {{ toggleLabel }}
    </label>
  </BaseFormField>
</template>
