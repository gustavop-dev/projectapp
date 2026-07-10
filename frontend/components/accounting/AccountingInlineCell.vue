<template>
  <div
    v-if="!editing"
    class="min-w-0 cursor-text rounded px-1 -mx-1 hover:bg-surface-raised transition-colors"
    title="Doble clic para editar"
    data-testid="inline-cell-display"
    @dblclick="start"
  >
    <slot>{{ value ?? '—' }}</slot>
  </div>
  <div v-else class="min-w-[8rem]" data-testid="inline-cell-editor">
    <BaseCurrencyInput
      v-if="type === 'money'"
      ref="inputRef"
      v-model="draft"
      size="sm"
      :disabled="saving"
      @keydown.enter.prevent="commit"
      @keydown.esc="cancel"
      @blur="commit"
    />
    <BaseInput
      v-else
      ref="inputRef"
      v-model="draft"
      size="sm"
      :disabled="saving"
      @keydown.enter.prevent="commit"
      @keydown.esc="cancel"
      @blur="commit"
    />
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue';
import BaseCurrencyInput from '~/components/base/BaseCurrencyInput.vue';
import BaseInput from '~/components/base/BaseInput.vue';

/**
 * Double-click-to-edit table cell. Enter/blur saves (emits `save` only when
 * the value changed), Esc cancels. On a failed PATCH the parent leaves the
 * row untouched, so re-rendering falls back to the old value for free.
 * Custom display markup goes in the default slot.
 */
const props = defineProps({
  value: { type: [String, Number], default: '' },
  type: { type: String, default: 'text' }, // 'text' | 'money'
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(['save']);

const editing = ref(false);
const draft = ref(null);
const inputRef = ref(null);
let cancelled = false;

async function start() {
  if (props.saving) return;
  draft.value = props.type === 'money'
    ? (props.value === '' || props.value == null ? null : Number(props.value))
    : String(props.value ?? '');
  cancelled = false;
  editing.value = true;
  await nextTick();
  inputRef.value?.$el?.focus?.();
}

function commit() {
  if (!editing.value || cancelled) return;
  editing.value = false;
  if (props.type === 'money') {
    const previous = props.value === '' || props.value == null ? null : Number(props.value);
    if (draft.value !== previous && draft.value !== null) emit('save', draft.value);
    return;
  }
  const next = String(draft.value ?? '').trim();
  if (next !== String(props.value ?? '')) emit('save', next);
}

function cancel() {
  cancelled = true;
  editing.value = false;
}
</script>
