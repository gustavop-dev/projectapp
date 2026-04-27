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
        v-if="isActive"
        class="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold bg-surface text-text-brand"
      >✓</span>
      <svg class="w-3 h-3 ml-0.5 opacity-60" :class="{ 'rotate-180': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition name="dropdown-fade">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 mt-1 z-50 bg-surface border border-border-default rounded-xl shadow-lg p-3"
        :class="type === 'date' ? 'w-64' : 'w-56'"
      >
        <p class="text-[10px] font-semibold text-gray-400 dark:text-text-muted uppercase tracking-wider mb-2">
          {{ label }}<span v-if="unit" class="ml-1 normal-case font-normal">({{ unit }})</span>
        </p>
        <div :class="type === 'date' ? 'flex flex-col gap-2' : 'flex items-center gap-2'">
          <input
            :value="minValue"
            :type="type"
            :placeholder="minPlaceholder"
            class="w-full px-2.5 py-1.5 border border-border-default rounded-lg text-xs bg-surface text-text-default outline-none focus:ring-1 focus:ring-focus-ring/30"
            @change="emit('update:minValue', parseValue($event.target.value))"
          />
          <span v-if="type !== 'date'" class="text-gray-400 text-xs shrink-0">—</span>
          <input
            :value="maxValue"
            :type="type"
            :placeholder="maxPlaceholder"
            class="w-full px-2.5 py-1.5 border border-border-default rounded-lg text-xs bg-surface text-text-default outline-none focus:ring-1 focus:ring-focus-ring/30"
            @change="emit('update:maxValue', parseValue($event.target.value))"
          />
        </div>
        <div v-if="isActive" class="mt-2 pt-2 border-t border-border-muted">
          <button
            type="button"
            class="text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
            @click="clearRange"
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
  type: { type: String, default: 'number' },
  minValue: { type: [Number, String], default: null },
  maxValue: { type: [Number, String], default: null },
  minPlaceholder: { type: String, default: 'Mín' },
  maxPlaceholder: { type: String, default: 'Máx' },
  unit: { type: String, default: null },
  icon: { type: String, default: null },
});

const emit = defineEmits(['update:minValue', 'update:maxValue']);

const isOpen = ref(false);
const containerRef = ref(null);
const isActive = computed(() => props.minValue != null || props.maxValue != null);

onClickOutside(containerRef, () => { isOpen.value = false; });

function parseValue(val) {
  if (val === '' || val == null) return null;
  return props.type === 'number' ? Number(val) : val;
}

function clearRange() {
  emit('update:minValue', null);
  emit('update:maxValue', null);
}
</script>
