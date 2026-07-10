<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Buscar por título o cliente...' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="relative">
    <svg
      class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
    <BaseInput
      :model-value="modelValue"
      type="search"
      :placeholder="placeholder"
      class="pl-10 pr-12 shadow-sm [&::-webkit-search-cancel-button]:hidden"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <button
      v-if="modelValue"
      type="button"
      aria-label="Limpiar búsqueda"
      class="absolute right-0 top-1/2 -translate-y-1/2 flex items-center justify-center w-11 h-11 rounded-xl
             text-text-subtle hover:text-text-muted transition-colors
             outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40"
      @click="$emit('update:modelValue', '')"
    >
      <span class="w-5 h-5 flex items-center justify-center rounded-full hover:bg-surface-raised">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </span>
    </button>
  </div>
</template>
