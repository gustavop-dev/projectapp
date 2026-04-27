<template>
  <div>
    <label class="block text-sm font-medium text-text-default mb-1">Etiquetas</label>
    <div
      v-if="tags.length"
      class="flex flex-wrap gap-2 px-3 py-2 border border-border-default rounded-xl bg-surface"
    >
      <button
        v-for="tag in tags"
        :key="tag.id"
        type="button"
        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
        :class="chipClass(tag)"
        @click="toggle(tag.id)"
      >
        <span class="w-2 h-2 rounded-full" :class="tagDotClass(tag.color)"></span>
        {{ tag.name }}
      </button>
    </div>
    <p v-else class="text-xs text-text-muted italic">
      Aún no hay etiquetas disponibles.
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { tagActiveClass, tagDotClass, TAG_IDLE_CHIP_CLASS } from '~/utils/documentTagColors.js';

const props = defineProps({
  tags: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
});
const emit = defineEmits(['update:modelValue']);

const selected = computed(() => props.modelValue || []);

function toggle(id) {
  const next = [...selected.value];
  const idx = next.indexOf(id);
  if (idx === -1) next.push(id);
  else next.splice(idx, 1);
  emit('update:modelValue', next);
}

function chipClass(tag) {
  return selected.value.includes(tag.id) ? tagActiveClass(tag.color) : TAG_IDLE_CHIP_CLASS;
}
</script>
