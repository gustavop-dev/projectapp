import { h } from 'vue';
import BaseCurrencyInput from '~/components/base/BaseCurrencyInput.vue';

// --- Inline sub-components (render functions for prod compatibility) ---
// Moved verbatim from SectionEditor.vue.
export const FieldInput = {
  props: { modelValue: [String, Number], label: String, placeholder: String },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('label', { class: 'block' }, [
      props.label ? h('span', { class: 'block text-xs text-text-muted mb-0.5' }, props.label) : null,
      h('input', {
        value: props.modelValue,
        placeholder: props.placeholder,
        class: 'w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm focus:ring-1 focus:ring-focus-ring/30 focus:border-focus-ring outline-none',
        onInput: (e) => emit('update:modelValue', e.target.value),
      }),
    ]);
  },
};

export const FieldCurrency = {
  props: {
    modelValue: [String, Number],
    label: String,
    placeholder: String,
    decimals: { type: Number, default: 0 },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('label', { class: 'block' }, [
      props.label ? h('span', { class: 'block text-xs text-text-muted mb-0.5' }, props.label) : null,
      h(BaseCurrencyInput, {
        modelValue: props.modelValue,
        decimals: props.decimals,
        placeholder: props.placeholder,
        'onUpdate:modelValue': (value) => emit('update:modelValue', value),
      }),
    ]);
  },
};

export const FieldTextarea = {
  props: { modelValue: String, label: String, help: String, rows: { type: Number, default: 4 }, isSingle: Boolean },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('label', { class: 'block' }, [
      props.label ? h('span', { class: 'block text-xs text-text-muted mb-0.5' }, props.label) : null,
      h('textarea', {
        value: props.modelValue,
        rows: props.rows,
        class: 'w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-lg text-sm focus:ring-1 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y',
        onInput: (e) => emit('update:modelValue', e.target.value),
      }),
      props.help ? h('p', { class: 'text-[10px] text-text-subtle mt-0.5' }, props.help) : null,
    ]);
  },
};
