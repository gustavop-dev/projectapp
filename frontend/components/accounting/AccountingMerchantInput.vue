<template>
  <div ref="wrapperRef" class="relative" @focusout="onFocusout">
    <input
      ref="inputRef"
      v-model="text"
      type="text"
      role="combobox"
      autocomplete="off"
      aria-autocomplete="list"
      aria-haspopup="listbox"
      :aria-expanded="isOpen"
      :placeholder="placeholder"
      :disabled="disabled"
      :title="disabled ? disabledReason : undefined"
      :data-testid="testId"
      :class="[INPUT_FIELD_BASE, INPUT_FIELD_SIZE[size] || INPUT_FIELD_SIZE.md]"
      @input="onInput"
      @focus="isOpen = true"
      @keydown.down.prevent="move(1)"
      @keydown.up.prevent="move(-1)"
      @keydown.enter.prevent="onEnter"
      @keydown.esc.prevent="onEsc"
    >

    <ul
      v-if="isOpen && matches.length"
      class="absolute z-30 mt-1 w-full min-w-[14rem] max-h-56 overflow-auto rounded-xl border border-border-default bg-surface shadow-lg"
      role="listbox"
      data-testid="merchant-input-options"
    >
      <li
        v-for="(option, index) in matches"
        :key="option.value"
        :class="[
          'px-3 py-2 text-sm cursor-pointer transition-colors',
          index === highlight ? 'bg-primary-soft text-text-brand' : 'hover:bg-surface-raised text-text-default',
        ]"
        role="option"
        :aria-selected="index === highlight"
        :data-testid="`merchant-input-option-${index}`"
        @mousedown.prevent="pick(option)"
        @mouseenter="highlight = index"
      >
        <span class="block truncate">{{ option.value }}</span>
        <span v-if="option.categoryLabel" class="block text-xs text-text-subtle truncate">
          {{ option.categoryLabel }}
        </span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import { INPUT_FIELD_BASE, INPUT_FIELD_SIZE } from '~/components/base/inputClasses';
import { oneOf } from '~/components/base/propValidators';

/**
 * Merchant picker: a combobox over the learned merchant catalog that still
 * accepts free text — the catalog suggests, it does not restrict, because a
 * statement can always bring a merchant nobody has mapped yet.
 *
 * Options are picked with `mousedown.prevent` so the input never blurs on the
 * way to the click; that keeps `commit` (emitted on real focus loss) from
 * firing with a half-typed value and swallowing the selection.
 */
const props = defineProps({
  modelValue: { type: String, default: '' },
  /** [{ value, category, categoryLabel }] — `value` is the merchant name. */
  options: { type: Array, default: () => [] },
  size: { type: String, default: 'md', validator: oneOf(['sm', 'md']) },
  placeholder: { type: String, default: 'Comercio' },
  disabled: { type: Boolean, default: false },
  disabledReason: { type: String, default: 'Guardando los cambios. Espera un momento.' },
  testId: { type: String, default: 'merchant-input' },
});

const emit = defineEmits(['update:modelValue', 'select', 'commit', 'cancel']);

const wrapperRef = ref(null);
const inputRef = ref(null);
const text = ref(props.modelValue ?? '');
const isOpen = ref(false);
const highlight = ref(-1);

watch(() => props.modelValue, (value) => {
  if (value !== text.value) text.value = value ?? '';
});

const matches = computed(() => {
  const query = text.value.trim().toLowerCase();
  const pool = props.options.filter((option) => option.value);
  if (!query) return pool.slice(0, 8);
  return pool
    .filter((option) => option.value.toLowerCase().includes(query))
    .slice(0, 8);
});

function onInput() {
  isOpen.value = true;
  highlight.value = -1;
  emit('update:modelValue', text.value);
}

function pick(option) {
  text.value = option.value;
  isOpen.value = false;
  highlight.value = -1;
  emit('update:modelValue', option.value);
  // Picking from the catalog is the intent — commit right away, like a select.
  emit('select', option);
}

function move(step) {
  if (!isOpen.value) {
    isOpen.value = true;
    return;
  }
  if (!matches.value.length) return;
  const count = matches.value.length;
  highlight.value = (highlight.value + step + count) % count;
}

function onEnter() {
  if (isOpen.value && highlight.value >= 0 && matches.value[highlight.value]) {
    pick(matches.value[highlight.value]);
    return;
  }
  isOpen.value = false;
  emit('commit');
}

function onEsc() {
  isOpen.value = false;
  emit('cancel');
}

function onFocusout(event) {
  // Ignore focus moves that stay inside the combobox.
  if (wrapperRef.value?.contains(event.relatedTarget)) return;
  isOpen.value = false;
  emit('commit');
}

async function focus() {
  await nextTick();
  inputRef.value?.focus();
  inputRef.value?.select();
}

defineExpose({ focus });
</script>
