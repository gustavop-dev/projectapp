<template>
  <div ref="containerRef" class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors border whitespace-nowrap focus-visible:ring-2 focus-visible:ring-focus-ring/30 focus-visible:outline-none"
      :class="isActive
        ? 'bg-primary text-white border-emerald-600 hover:bg-primary-strong'
        : 'bg-surface text-text-muted dark:text-gray-400 border-border-default hover:border-gray-300 dark:hover:border-gray-500'"
      @click="isOpen = !isOpen"
    >
      <span v-if="icon" class="text-sm leading-none">{{ icon }}</span>
      {{ label }}
      <span
        v-if="modelValue.length > 0"
        class="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold"
        :class="isActive ? 'bg-surface text-text-brand' : 'bg-primary text-white'"
      >{{ modelValue.length }}</span>
      <svg class="w-3 h-3 ml-0.5 opacity-60" :class="{ 'rotate-180': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition name="dropdown-fade">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 mt-1 z-50 min-w-[180px] max-w-[240px] bg-surface border border-border-default rounded-xl shadow-lg overflow-hidden"
      >
        <div class="max-h-60 overflow-y-auto py-1">
          <label
            v-for="opt in options"
            :key="opt.value"
            class="flex items-center gap-2.5 px-3 py-2 text-sm text-text-default hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
          >
            <input
              type="checkbox"
              :checked="modelValue.includes(opt.value)"
              class="w-3.5 h-3.5 rounded border-gray-300 text-text-brand focus:ring-focus-ring/30 focus:ring-1 accent-emerald-600"
              @change="toggle(opt.value)"
            />
            <span class="truncate">{{ opt.label }}</span>
          </label>
        </div>
        <div v-if="modelValue.length > 0" class="border-t border-border-muted px-3 py-1.5">
          <button
            type="button"
            class="text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
            @click="$emit('update:modelValue', [])"
          >
            Limpiar
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';

const props = defineProps({
  label: { type: String, required: true },
  options: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  icon: { type: String, default: null },
});

const emit = defineEmits(['update:modelValue']);

const isOpen = ref(false);
const containerRef = ref(null);
const isActive = computed(() => props.modelValue.length > 0);

onClickOutside(containerRef, () => { isOpen.value = false; });

function toggle(value) {
  const arr = [...props.modelValue];
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
  emit('update:modelValue', arr);
}
</script>
