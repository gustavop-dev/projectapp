<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Buscar por título o cliente...' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="relative">
    <BaseActionIcon action="search" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-subtle pointer-events-none" />
    <BaseInput
      :model-value="modelValue"
      type="search"
      :placeholder="placeholder"
      class="pl-10 pr-12 shadow-sm [&::-webkit-search-cancel-button]:hidden"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <BaseButton
      unstyled
      icon-only
      v-if="modelValue"
      type="button"
      aria-label="Limpiar búsqueda"
      title="Limpiar búsqueda"
      class="absolute right-0 top-1/2 -translate-y-1/2 flex items-center justify-center w-11 h-11 rounded-xl
             text-text-subtle hover:text-text-muted transition-colors
             outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40"
      @click="$emit('update:modelValue', '')"
    >
      <BaseActionIcon action="clear" />
    </BaseButton>
  </div>
</template>
