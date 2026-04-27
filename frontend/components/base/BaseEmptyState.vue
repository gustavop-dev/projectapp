<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="flex flex-col items-center justify-center text-center px-6 py-12 rounded-xl border border-dashed border-border-default bg-surface">
    <div v-if="$slots.icon" class="mb-3 text-text-subtle">
      <slot name="icon" />
    </div>
    <h3 v-if="title" class="text-sm font-semibold text-text-default">{{ title }}</h3>
    <p v-if="description || $slots.default" class="mt-1 text-sm text-text-muted max-w-md">
      <slot>{{ description }}</slot>
    </p>
    <div v-if="$slots.actions" class="mt-4 flex flex-wrap items-center justify-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
