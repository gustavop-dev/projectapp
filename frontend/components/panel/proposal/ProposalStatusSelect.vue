<template>
  <div class="relative inline-flex items-center">
    <select
      :value="proposal.status"
      :disabled="updating"
      class="bg-input-bg text-xs px-2.5 py-1 rounded-full font-medium border border-input-border cursor-pointer outline-none focus:ring-2 focus:ring-focus-ring/30 pr-6 disabled:opacity-60 disabled:cursor-not-allowed"
      :class="statusClass(proposal.status)"
      aria-label="Cambiar estado de la propuesta"
      @change="onChange"
      @click.stop
    >
      <option :value="proposal.status" disabled>{{ statusLabel(proposal.status) }}</option>
      <optgroup v-if="naturalTargets.length" label="Flujo normal">
        <option v-for="s in naturalTargets" :key="s" :value="s">{{ statusLabel(s) }}</option>
      </optgroup>
      <optgroup v-if="forcedTargets.length" label="Forzar estado">
        <option v-for="s in forcedTargets" :key="s" :value="s">{{ statusLabel(s) }}</option>
      </optgroup>
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
import { computed } from 'vue';
import { PROPOSAL_STATUSES, statusLabel, statusClass } from '~/utils/proposalStatuses';

/**
 * Badge-styled status select (admin mode). Pure intent-picker: the visible
 * value only moves when `proposal.status` updates after a successful PATCH;
 * on change the select snaps back and the chosen status is emitted for the
 * page to confirm/PATCH (useProposalStatusChange).
 */
const props = defineProps({
  proposal: { type: Object, required: true },
  updating: { type: Boolean, default: false },
});

const emit = defineEmits(['change']);

const naturalTargets = computed(() => props.proposal.available_transitions || []);
const forcedTargets = computed(() => PROPOSAL_STATUSES
  .map((s) => s.value)
  .filter((value) => value !== props.proposal.status && !naturalTargets.value.includes(value)));

function onChange(event) {
  const value = event.target.value;
  // Snap back: the select reflects state, not intent.
  event.target.value = props.proposal.status;
  if (value && value !== props.proposal.status) emit('change', value);
}
</script>
