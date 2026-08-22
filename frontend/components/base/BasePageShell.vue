<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  width: {
    type: String,
    default: 'panel',
    validator: oneOf(['narrow', 'content', 'panel', 'full']),
  },
  as: { type: String, default: 'div' },
})

const widths = {
  narrow: 'max-w-3xl',
  content: 'max-w-7xl',
  panel: 'max-w-panel',
  full: 'max-w-none',
}

const widthClass = computed(() => widths[props.width] || widths.panel)
</script>

<template>
  <component
    :is="as"
    class="mx-auto w-full"
    :class="widthClass"
    data-testid="panel-content-shell"
  >
    <slot />
  </component>
</template>
