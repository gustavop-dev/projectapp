<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  variant: { type: String, default: 'info', validator: oneOf(['info', 'success', 'warning', 'danger']) },
  title: { type: String, default: '' },
  dismissible: { type: Boolean, default: false },
})

defineEmits(['dismiss'])

const variants = {
  info: 'bg-primary-soft text-text-default border-primary',
  success: 'bg-success-soft text-success-strong border-success-strong/30',
  warning: 'bg-warning-soft text-warning-strong border-warning-strong/30',
  danger: 'bg-danger-soft text-danger-strong border-danger-strong/30',
}

const cls = computed(() => variants[props.variant] || variants.info)
</script>

<template>
  <div
    role="alert"
    class="relative flex items-start gap-3 px-4 py-3 rounded-xl border-l-4"
    :class="cls"
  >
    <slot name="icon" />
    <div class="flex-1 min-w-0">
      <p v-if="title" class="text-sm font-semibold mb-0.5">{{ title }}</p>
      <div class="text-sm">
        <slot />
      </div>
    </div>
    <button
      v-if="dismissible"
      type="button"
      aria-label="Cerrar"
      class="flex-shrink-0 -mr-1 -mt-1 p-1 rounded-lg hover:bg-surface-raised transition-colors"
      @click="$emit('dismiss')"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
