<template>
  <div v-show="isOpen" class="mb-4">
    <div class="bg-surface border border-border-default rounded-xl divide-y divide-gray-100 dark:divide-gray-700/60">

      <!-- Clasificación -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Clasificación</span>
        <ProposalFilterDropdown
          label="Estado"
          :options="statusOptions"
          :model-value="modelValue.lastStatuses"
          @update:model-value="emit('update:modelValue', { ...modelValue, lastStatuses: $event })"
        />
      </div>

      <!-- Proyecto -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Proyecto</span>
        <ProposalFilterDropdown
          label="Tipo de proyecto"
          :options="projectTypeOptions"
          :model-value="modelValue.projectTypes"
          @update:model-value="emit('update:modelValue', { ...modelValue, projectTypes: $event })"
        />
        <ProposalFilterDropdown
          label="Mercado"
          :options="marketTypeOptions"
          :model-value="modelValue.marketTypes"
          @update:model-value="emit('update:modelValue', { ...modelValue, marketTypes: $event })"
        />
      </div>

      <!-- Propuestas -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Propuestas</span>
        <ProposalFilterRangeDropdown
          label="Total"
          type="number"
          min-placeholder="Mín"
          max-placeholder="Máx"
          :min-value="modelValue.totalProposalsMin"
          :max-value="modelValue.totalProposalsMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, totalProposalsMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, totalProposalsMax: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Aceptadas"
          type="number"
          min-placeholder="Mín"
          max-placeholder="Máx"
          :min-value="modelValue.acceptedMin"
          :max-value="modelValue.acceptedMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, acceptedMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, acceptedMax: $event })"
        />
      </div>

      <!-- Fechas -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle w-[5.5rem] shrink-0">Fechas</span>
        <ProposalFilterRangeDropdown
          label="Última actividad"
          type="date"
          min-placeholder="Desde"
          max-placeholder="Hasta"
          :min-value="modelValue.lastActivityAfter"
          :max-value="modelValue.lastActivityBefore"
          @update:min-value="emit('update:modelValue', { ...modelValue, lastActivityAfter: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, lastActivityBefore: $event })"
        />
      </div>

      <!-- Limpiar todo -->
      <div class="flex items-center gap-2 px-3 py-2.5">
        <div class="flex-1" />
        <button
          v-if="filterCount > 0"
          type="button"
          class="text-xs text-text-subtle hover:text-red-500 dark:hover:text-red-400 transition-colors font-medium whitespace-nowrap"
          @click="emit('reset')"
        >
          Limpiar todo
        </button>
      </div>
    </div>

    <!-- Active filter chips -->
    <div v-if="activeChips.length > 0" class="flex flex-wrap items-center gap-1.5 mt-2 px-1">
      <span class="text-[10px] font-semibold uppercase tracking-wider text-text-subtle mr-0.5">Activos:</span>
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary-soft text-text-brand border border-emerald-200 dark:border-emerald-700"
      >
        {{ chip.label }}
        <button
          type="button"
          class="ml-0.5 hover:text-red-500 dark:hover:text-red-400 leading-none"
          @click="clearChip(chip.key)"
        >&times;</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import ProposalFilterDropdown from '~/components/proposals/ProposalFilterDropdown.vue';
import ProposalFilterRangeDropdown from '~/components/proposals/ProposalFilterRangeDropdown.vue';
import {
  proposalStatusOptions as statusOptions,
  projectTypeOptions,
  marketTypeOptions,
  proposalStatusLabelMap as statusLabelMap,
  projectTypeLabelMap,
  marketTypeLabelMap,
} from '~/constants/filterOptions.js';

const props = defineProps({
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: false },
  filterCount: { type: Number, default: 0 },
});

const emit = defineEmits(['update:modelValue', 'reset']);

function formatRange(min, max) {
  if (min != null && max != null) return `${min}–${max}`;
  if (min != null) return `≥ ${min}`;
  if (max != null) return `≤ ${max}`;
  return '';
}

function formatDateRange(after, before) {
  if (after && before) return `${after} → ${before}`;
  if (after) return `desde ${after}`;
  if (before) return `hasta ${before}`;
  return '';
}

const activeChips = computed(() => {
  const chips = [];
  const mv = props.modelValue;

  if (mv.lastStatuses?.length)
    chips.push({ key: 'lastStatuses', label: `Estado: ${mv.lastStatuses.map((s) => statusLabelMap[s] || s).join(', ')}` });

  if (mv.projectTypes?.length)
    chips.push({ key: 'projectTypes', label: `Tipo: ${mv.projectTypes.map((t) => projectTypeLabelMap[t] || t).join(', ')}` });

  if (mv.marketTypes?.length)
    chips.push({ key: 'marketTypes', label: `Mercado: ${mv.marketTypes.map((t) => marketTypeLabelMap[t] || t).join(', ')}` });

  const total = formatRange(mv.totalProposalsMin, mv.totalProposalsMax);
  if (total) chips.push({ key: 'totalProposals', label: `Total propuestas: ${total}` });

  const accepted = formatRange(mv.acceptedMin, mv.acceptedMax);
  if (accepted) chips.push({ key: 'accepted', label: `Aceptadas: ${accepted}` });

  const ar = formatDateRange(mv.lastActivityAfter, mv.lastActivityBefore);
  if (ar) chips.push({ key: 'activityRange', label: `Actividad: ${ar}` });

  return chips;
});

const CHIP_RESET = {
  lastStatuses:   (mv) => { mv.lastStatuses = []; },
  projectTypes:   (mv) => { mv.projectTypes = []; },
  marketTypes:    (mv) => { mv.marketTypes = []; },
  totalProposals: (mv) => { mv.totalProposalsMin = null; mv.totalProposalsMax = null; },
  accepted:       (mv) => { mv.acceptedMin = null; mv.acceptedMax = null; },
  activityRange:  (mv) => { mv.lastActivityAfter = null; mv.lastActivityBefore = null; },
};

function clearChip(key) {
  const mv = { ...props.modelValue };
  CHIP_RESET[key]?.(mv);
  emit('update:modelValue', mv);
}
</script>
