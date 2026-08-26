<script setup>
import { computed } from 'vue'
import { oneOf } from './propValidators'

const props = defineProps({
  modelValue: { type: [String, Number], required: true },
  tabs: { type: Array, required: true }, // [{ id, label, badge?, disabled? }]
  variant: { type: String, default: 'underline', validator: oneOf(['underline', 'pill']) },
  fullWidth: { type: Boolean, default: false },
  // Nombra el control colapsado en móvil, donde el desplegable puede quedar
  // pegado a otro y el rótulo cerrado no dice de qué es.
  ariaLabel: { type: String, default: 'Secciones' },
})

const emit = defineEmits(['update:modelValue'])

const normalized = computed(() =>
  props.tabs.map((t) =>
    typeof t === 'object' ? t : { id: t, label: String(t) },
  ),
)

const selectOptions = computed(() =>
  normalized.value.map((t) => ({
    value: t.id,
    label: t.disabled && t.disabledReason
      ? `${t.label} — ${t.disabledReason}`
      : t.label,
    disabled: t.disabled,
    disabledReason: t.disabledReason,
  })),
)

function select(id, disabled) {
  if (disabled) return
  emit('update:modelValue', id)
}

function tabClass(tab) {
  const active = props.modelValue === tab.id
  if (props.variant === 'pill') {
    return [
      'px-3 py-2 text-sm rounded-lg',
      active ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default',
    ]
  }
  return [
    'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px',
    active ? 'border-text-brand text-text-brand' : 'border-transparent text-text-muted hover:text-text-default',
  ]
}
</script>

<template>
  <div>
    <!-- Compact + portrait tablet: one reachable native selector. -->
    <BaseMobileTabSelect
      class="mb-6"
      :model-value="modelValue"
      :options="selectOptions"
      :aria-label="ariaLabel"
      @update:model-value="select($event, false)"
    />

    <!-- Landscape tablet and wider: visible strip, allowed to wrap. -->
    <div
      :class="[
        'hidden panel-landscape:flex flex-wrap gap-1 mb-6',
        variant === 'underline' ? 'border-b border-border-default' : 'bg-surface-raised rounded-xl p-1',
        fullWidth ? 'w-full' : '',
      ]"
      role="tablist"
    >
      <button
        v-for="t in normalized"
        :key="t.id"
        type="button"
        role="tab"
        :aria-selected="modelValue === t.id"
        :disabled="t.disabled"
        :title="t.disabled ? t.disabledReason : undefined"
        :aria-description="t.disabled ? t.disabledReason : undefined"
        :class="[
          'transition-colors whitespace-nowrap outline-none focus:ring-2 focus:ring-focus-ring/30 disabled:opacity-50 disabled:cursor-not-allowed',
          fullWidth ? 'flex-1' : '',
          tabClass(t),
        ]"
        @click="select(t.id, t.disabled)"
      >
        {{ t.label }}
        <span
          v-if="t.badge != null"
          class="ml-1.5 inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full text-[10px] font-bold bg-primary-soft text-text-brand"
        >
          {{ t.badge }}
        </span>
      </button>
    </div>
  </div>
</template>
