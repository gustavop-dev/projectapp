<script setup>
defineProps({
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  required: { type: Boolean, default: false },
  for: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm | md
})
</script>

<template>
  <div>
    <label
      v-if="label"
      :for="$props.for"
      class="block font-medium text-text-default mb-1"
      :class="size === 'sm' ? 'text-xs' : 'text-sm'"
    >
      {{ label }}
      <span v-if="required" class="text-danger-strong">*</span>
    </label>
    <slot />
    <p
      v-if="error"
      class="text-xs text-danger-strong mt-1"
    >
      {{ error }}
    </p>
    <p
      v-else-if="hint"
      class="text-xs text-text-muted mt-1"
    >
      {{ hint }}
    </p>
  </div>
</template>
