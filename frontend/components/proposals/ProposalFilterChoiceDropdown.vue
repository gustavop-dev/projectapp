<template>
  <div ref="containerRef" class="relative">
    <!-- design-tokens: allow-raw-button -->
    <button
      type="button"
      :data-testid="testId"
      class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors border whitespace-nowrap focus-visible:ring-2 focus-visible:ring-focus-ring/30 focus-visible:outline-none"
      :class="isActive
        ? 'bg-primary text-white border-emerald-600 hover:bg-primary-strong'
        : 'bg-surface text-text-muted border-border-default hover:border-text-muted'"
      @click="isOpen = !isOpen"
    >
      <span v-if="icon" class="text-sm leading-none">{{ icon }}</span>
      {{ isActive ? selectedLabel : label }}
      <svg class="w-3 h-3 ml-0.5 opacity-60" :class="{ 'rotate-180': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition name="dropdown-fade">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 mt-1 z-50 min-w-[200px] max-w-[280px] bg-surface border border-border-default rounded-xl shadow-lg overflow-hidden"
      >
        <div class="max-h-60 overflow-y-auto py-1">
          <label
            v-for="opt in options"
            :key="opt.value"
            class="flex items-center gap-2.5 px-3 py-2 text-sm text-text-default hover:bg-surface-raised cursor-pointer"
          >
            <input
              type="radio"
              :name="radioName"
              :checked="modelValue === opt.value"
              class="w-3.5 h-3.5 border-input-border text-text-brand focus:ring-focus-ring/30 focus:ring-1 accent-emerald-600"
              @change="select(opt.value)"
            />
            <span class="truncate">{{ opt.label }}</span>
          </label>
        </div>
        <div v-if="isActive" class="border-t border-border-muted px-3 py-1.5">
          <BaseButton variant="link" size="sm" @click="select('')">
            Limpiar
          </BaseButton>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
/**
 * Single-choice sibling of ProposalFilterDropdown, for filters whose options
 * are mutually exclusive (a client either has hosting or does not).
 *
 * The trigger shows the chosen option rather than the group label once one is
 * picked: these controls mirror one-click predefined filters, and reading back
 * the exact cut is what makes the panel and the tab bar legible as the same
 * thing.
 */
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';

const props = defineProps({
  label: { type: String, required: true },
  // [{ value, label }] — `value` '' means "no cut".
  options: { type: Array, required: true },
  modelValue: { type: String, default: '' },
  icon: { type: String, default: null },
  testId: { type: String, default: null },
});

const emit = defineEmits(['update:modelValue']);

const isOpen = ref(false);
const containerRef = ref(null);
const isActive = computed(() => !!props.modelValue);
const selectedLabel = computed(
  () => props.options.find((o) => o.value === props.modelValue)?.label || props.label,
);
// Radios only behave as one group when they share a name; without this the
// panel's three choice dropdowns would let each other's selections coexist.
const radioName = computed(() => `filter-choice-${props.testId || props.label}`);

onClickOutside(containerRef, () => { isOpen.value = false; });

function select(value) {
  emit('update:modelValue', value);
  isOpen.value = false;
}
</script>
