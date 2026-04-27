<script setup>
import { computed } from 'vue'
import { SELECT_ARROW_STYLE as selectArrowStyle } from '~/utils/selectArrowStyle'
import { oneOf } from './propValidators'

const props = defineProps({
  modelValue: { type: [String, Number], required: true },
  tabs: { type: Array, required: true }, // [{ id, label, badge?, disabled? }]
  variant: { type: String, default: 'underline', validator: oneOf(['underline', 'pill']) },
  fullWidth: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const normalized = computed(() =>
  props.tabs.map((t) =>
    typeof t === 'object' ? t : { id: t, label: String(t) },
  ),
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
    <!-- Mobile: select fallback -->
    <div class="md:hidden mb-6">
      <select
        :value="modelValue"
        class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text rounded-xl text-sm font-medium focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none appearance-none cursor-pointer"
        :style="selectArrowStyle"
        @change="select($event.target.value, false)"
      >
        <option v-for="t in normalized" :key="t.id" :value="t.id" :disabled="t.disabled">
          {{ t.label }}
        </option>
      </select>
    </div>

    <!-- Desktop: underline or pill -->
    <div
      :class="[
        'hidden md:flex gap-1 mb-6',
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
