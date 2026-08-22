<template>
  <div
    v-if="!editing"
    class="touch-target group flex items-center gap-1 min-w-0 cursor-pointer rounded px-1 -mx-1 hover:bg-surface-raised transition-colors"
    :class="align === 'right' ? 'justify-end' : ''"
    role="button"
    tabindex="0"
    title="Clic para editar"
    data-testid="inline-cell-display"
    @click="start"
    @keydown.enter.prevent="start"
    @keydown.space.prevent="start"
  >
    <span
      class="min-w-0 border-b border-dashed border-border-muted group-hover:border-text-brand transition-colors"
      :class="align === 'right' ? '' : 'flex-1'"
    >
      <slot>{{ value ?? '—' }}</slot>
    </span>
    <svg
      class="touch-reveal w-3 h-3 flex-shrink-0 text-text-subtle opacity-0 group-hover:opacity-100 transition-opacity"
      fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"
    >
      <path
        stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z"
      />
    </svg>
  </div>

  <div v-else class="min-w-[8rem]" data-testid="inline-cell-editor">
    <BaseCurrencyInput
      v-if="type === 'money'"
      ref="inputRef"
      v-model="draft"
      size="sm"
      :allow-negative="allowNegative"
      :disabled="saving"
      @keydown.enter.prevent="commit"
      @keydown.esc="cancel"
      @blur="commit"
    />
    <BaseSelect
      v-else-if="type === 'select'"
      ref="inputRef"
      v-model="draft"
      :options="options"
      size="sm"
      :disabled="saving"
      @update:model-value="commit"
      @keydown.esc="cancel"
      @blur="commit"
    />
    <AccountingMerchantInput
      v-else-if="type === 'merchant'"
      ref="inputRef"
      v-model="draft"
      :options="options"
      size="sm"
      :disabled="saving"
      @select="onMerchantSelect"
      @commit="commit"
      @cancel="cancel"
    />
    <div v-else-if="type === 'installments'" class="flex items-center gap-1">
      <BaseInput
        ref="inputRef"
        v-model="draft.number"
        type="number"
        min="1"
        size="sm"
        class="w-14"
        placeholder="Cuota"
        data-testid="inline-cell-installment-number"
        :disabled="saving"
        @keydown.enter.prevent="commit"
        @keydown.esc="cancel"
        @blur="onInstallmentBlur"
      />
      <span class="text-text-subtle">/</span>
      <BaseInput
        v-model="draft.total"
        type="number"
        min="1"
        size="sm"
        class="w-14"
        placeholder="Total"
        data-testid="inline-cell-installment-total"
        :disabled="saving"
        @keydown.enter.prevent="commit"
        @keydown.esc="cancel"
        @blur="onInstallmentBlur"
      />
    </div>
    <BaseInput
      v-else-if="type === 'number'"
      ref="inputRef"
      v-model="draft"
      type="number"
      :min="min"
      :max="max"
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
      :type="type === 'date' ? 'date' : 'text'"
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
import AccountingMerchantInput from '~/components/accounting/AccountingMerchantInput.vue';
import BaseCurrencyInput from '~/components/base/BaseCurrencyInput.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';

/**
 * Click-to-edit table cell. Enter/blur saves (emits `save` only when the value
 * changed), Esc cancels; a select or a merchant pick commits as soon as an
 * option is chosen (choosing one is the intent). On a failed PATCH the parent
 * leaves the row untouched, so re-rendering falls back to the old value for
 * free. Custom display markup goes in the default slot — for selects it shows
 * the label while `value`/`save` carry the option value.
 *
 * The dashed underline plus the hover pencil are the affordance: without them
 * the whole feature is invisible and nobody discovers the cells are editable.
 *
 * `save` carries an optional second argument with metadata about the choice
 * (currently the default category of a picked merchant).
 */
const props = defineProps({
  value: { type: [String, Number], default: '' },
  // 'text' | 'number' | 'money' | 'date' | 'select' | 'merchant' | 'installments'
  type: { type: String, default: 'text' },
  options: { type: Array, default: () => [] }, // select/merchant only
  saving: { type: Boolean, default: false },
  /** Money cells only: keep the sign so refunds stay negative. */
  allowNegative: { type: Boolean, default: false },
  /** 'right' mirrors the layout for right-aligned numeric columns. */
  align: { type: String, default: 'left' },
  /**
   * Number cells only. `money` is wrong for plain counts — it formats
   * thousands, so "20 horas" would render as an amount — hence a separate
   * type with its own bounds.
   */
  min: { type: [String, Number], default: null },
  max: { type: [String, Number], default: null },
});

const emit = defineEmits(['save']);

const editing = ref(false);
const draft = ref(null);
const inputRef = ref(null);
let cancelled = false;

/** `"3/12"` -> `{ number: '3', total: '12' }`; anything else -> empty pair. */
function parseInstallments(label) {
  const match = String(label ?? '').trim().match(/^(\d+)\s*\/\s*(\d+)$/);
  return match ? { number: match[1], total: match[2] } : { number: '', total: '' };
}

function installmentLabel(pair) {
  return pair.number && pair.total ? `${pair.number}/${pair.total}` : '';
}

async function start() {
  if (props.saving || editing.value) return;
  if (props.type === 'money') {
    draft.value = props.value === '' || props.value == null ? null : Number(props.value);
  } else if (props.type === 'installments') {
    draft.value = parseInstallments(props.value);
  } else {
    draft.value = String(props.value ?? '');
  }
  cancelled = false;
  editing.value = true;
  await nextTick();
  const target = inputRef.value;
  if (typeof target?.focus === 'function') target.focus();
  else target?.$el?.focus?.();
}

/**
 * The two installment inputs blur into each other; only a focus move that
 * leaves the pair should commit.
 */
function onInstallmentBlur(event) {
  const next = event?.relatedTarget;
  if (next && event.currentTarget?.parentElement?.contains(next)) return;
  commit();
}

function commit() {
  if (!editing.value || cancelled) return;
  editing.value = false;
  if (props.type === 'money') {
    const previous = props.value === '' || props.value == null ? null : Number(props.value);
    if (draft.value !== previous && draft.value !== null) emit('save', draft.value);
    return;
  }
  if (props.type === 'installments') {
    const pair = draft.value || { number: '', total: '' };
    if (installmentLabel(pair) === String(props.value ?? '')) return;
    if (!pair.number && !pair.total) {
      emit('save', null);
      return;
    }
    emit('save', { number: Number(pair.number) || null, total: Number(pair.total) || null });
    return;
  }
  if (props.type === 'number') {
    const raw = String(draft.value ?? '').trim();
    // Blanking a count is not a value: keep the previous one rather than
    // emitting 0, which would silently zero out an hours or discount cell.
    if (raw === '') return;
    let next = Number(raw);
    if (!Number.isFinite(next)) return;
    if (props.min !== null && next < Number(props.min)) next = Number(props.min);
    if (props.max !== null && next > Number(props.max)) next = Number(props.max);
    if (next !== Number(props.value)) emit('save', next);
    return;
  }
  const next = String(draft.value ?? '').trim();
  if (next !== String(props.value ?? '')) emit('save', next);
}

function onMerchantSelect(option) {
  if (!editing.value) return;
  editing.value = false;
  if (option.value !== String(props.value ?? '')) {
    emit('save', option.value, { category: option.category ?? null });
  }
}

function cancel() {
  cancelled = true;
  editing.value = false;
}
</script>
