<template>
  <div class="flex items-center gap-2">
    <span class="w-20 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-green-light/70">
      {{ label }}
    </span>
    <span
      class="min-w-0 flex-1 truncate rounded-lg bg-surface-raised px-2 py-1 font-mono text-xs text-text-brand"
      :title="isSecret ? '' : value"
    >
      {{ displayValue }}
    </span>
    <button
      type="button"
      class="rounded-lg border border-esmerald/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-text-brand transition hover:bg-primary-soft disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08]"
      :disabled="!value"
      @click="copy"
    >
      Copiar
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '' },
  isSecret: { type: Boolean, default: false },
})

const emit = defineEmits(['copy', 'error'])

const displayValue = computed(() => {
  if (!props.value) return '—'
  if (props.isSecret) return '•'.repeat(Math.min(12, props.value.length))
  return props.value
})

const copy = async () => {
  if (!props.value) return
  try {
    await navigator.clipboard.writeText(props.value)
    emit('copy')
  } catch (err) {
    emit('error', err)
  }
}
</script>
