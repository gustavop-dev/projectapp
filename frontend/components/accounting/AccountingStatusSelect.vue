<template>
  <div class="relative inline-flex items-center">
    <select
      :value="String(value)"
      :disabled="updating"
      class="text-xs px-2.5 py-1 rounded-full font-medium border cursor-pointer outline-none focus:ring-2 focus:ring-focus-ring/30 pr-6 appearance-none disabled:opacity-60 disabled:cursor-not-allowed"
      :class="value
        ? 'bg-success-soft text-success-strong border-success-strong/30'
        : 'bg-surface-raised text-text-muted border-input-border'"
      :aria-label="ariaLabel"
      data-testid="accounting-status-select"
      @change="onChange"
      @click.stop
    >
      <option value="true">{{ activeLabel }}</option>
      <option value="false">{{ inactiveLabel }}</option>
    </select>
    <span v-if="updating" class="absolute right-1.5 flex items-center pointer-events-none">
      <svg class="animate-spin h-3 w-3 text-text-muted" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </span>
  </div>
</template>

<script setup>
/**
 * Badge-styled boolean status select (Activo/Inactivo). Pure intent-picker,
 * same pattern as ProposalStatusSelect: the visible value only moves when
 * the row updates after a successful PATCH; on change the select snaps back
 * and the chosen state is emitted for the page to PATCH.
 */
const props = defineProps({
  value: { type: Boolean, required: true },
  updating: { type: Boolean, default: false },
  activeLabel: { type: String, default: 'Activo' },
  inactiveLabel: { type: String, default: 'Inactivo' },
  ariaLabel: { type: String, default: 'Cambiar estado' },
});

const emit = defineEmits(['change']);

function onChange(event) {
  const next = event.target.value === 'true';
  // Snap back: the select reflects state, not intent.
  event.target.value = String(props.value);
  if (next !== props.value) emit('change', next);
}
</script>
