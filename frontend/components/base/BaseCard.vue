<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: { type: String, default: 'md' }, // none | sm | md | lg
  as: { type: String, default: 'div' },
})

const paddings = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-7',
}

const classes = computed(() => [
  'bg-surface border border-border-muted rounded-xl',
  props.padding in paddings ? paddings[props.padding] : paddings.md,
])
</script>

<template>
  <component :is="as" :class="classes">
    <slot />
  </component>
</template>
