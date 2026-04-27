<template>
  <div>
    <div
      class="flex gap-1 mb-6 rounded-xl p-1 max-w-md"
      :class="trackClass"
    >
      <button
        type="button"
        :class="tabButtonClass('commercial')"
        @click="select('commercial')"
      >
        Propuesta comercial
      </button>
      <button
        type="button"
        :class="tabButtonClass('technical')"
        @click="select('technical')"
      >
        Detalle técnico
      </button>
    </div>
    <div v-show="modelValue === 'commercial'">
      <slot name="commercial" />
    </div>
    <div v-show="modelValue === 'technical'">
      <slot name="technical" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
    validator: (v) => v === 'commercial' || v === 'technical',
  },
  /** Use track + tab styles aligned with admin defaults page (dark mode). */
  darkTrack: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue']);

const trackClass = computed(() =>
  (props.darkTrack ? 'bg-surface-raised' : 'bg-surface-raised'),
);

function tabButtonClass(tab) {
  const active = props.modelValue === tab;
  if (props.darkTrack) {
    return [
      'flex-1 px-3 py-2 text-sm rounded-lg transition-all',
      active
        ? 'bg-surface shadow-sm font-medium text-text-default'
        : 'text-text-muted hover:text-text-default',
    ];
  }
  return [
    'flex-1 px-3 py-2 text-sm rounded-lg transition-all',
    active
      ? 'bg-surface shadow-sm font-medium text-text-default'
      : 'text-text-muted hover:text-text-default',
  ];
}

function select(tab) {
  emit('update:modelValue', tab);
}
</script>
