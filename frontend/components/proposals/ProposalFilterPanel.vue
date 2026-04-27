<template>
  <div v-show="isOpen" class="mb-4">
    <div class="bg-surface border border-border-default rounded-xl divide-y divide-gray-100 dark:divide-gray-700/60">

      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-text-muted w-[5.5rem] shrink-0">Clasificación</span>
        <ProposalFilterDropdown
          label="Estado"
          :options="statusOptions"
          :model-value="modelValue.statuses"
          @update:model-value="emit('update:modelValue', { ...modelValue, statuses: $event })"
        />
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

      <!-- Valores -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-text-muted w-[5.5rem] shrink-0">Valores</span>
        <ProposalFilterDropdown
          label="Moneda"
          :options="currencyOptions"
          :model-value="modelValue.currencies"
          @update:model-value="emit('update:modelValue', { ...modelValue, currencies: $event })"
        />
        <ProposalFilterDropdown
          label="Idioma"
          :options="languageOptions"
          :model-value="modelValue.languages"
          @update:model-value="emit('update:modelValue', { ...modelValue, languages: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Inversión"
          type="number"
          :min-value="modelValue.investmentMin"
          :max-value="modelValue.investmentMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, investmentMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, investmentMax: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Heat Score"
          type="number"
          unit="/ 10"
          min-placeholder="0"
          max-placeholder="10"
          :min-value="modelValue.heatScoreMin"
          :max-value="modelValue.heatScoreMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, heatScoreMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, heatScoreMax: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Vistas"
          type="number"
          :min-value="modelValue.viewCountMin"
          :max-value="modelValue.viewCountMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, viewCountMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, viewCountMax: $event })"
        />
      </div>

      <!-- Fechas -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-text-muted w-[5.5rem] shrink-0">Fechas</span>
        <ProposalFilterRangeDropdown
          label="Creación"
          type="date"
          min-placeholder="Desde"
          max-placeholder="Hasta"
          :min-value="modelValue.createdAfter"
          :max-value="modelValue.createdBefore"
          @update:min-value="emit('update:modelValue', { ...modelValue, createdAfter: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, createdBefore: $event })"
        />
        <ProposalFilterRangeDropdown
          label="Actividad"
          type="date"
          min-placeholder="Desde"
          max-placeholder="Hasta"
          :min-value="modelValue.lastActivityAfter"
          :max-value="modelValue.lastActivityBefore"
          @update:min-value="emit('update:modelValue', { ...modelValue, lastActivityAfter: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, lastActivityBefore: $event })"
        />
      </div>

      <!-- Otros + Limpiar todo -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-text-muted w-[5.5rem] shrink-0">Otros</span>
        <ProposalFilterDropdown
          label="Activo"
          :options="activeStatusOptions"
          :model-value="modelValue.isActive !== 'all' ? [modelValue.isActive] : []"
          @update:model-value="emit('update:modelValue', { ...modelValue, isActive: $event.length ? $event[$event.length - 1] : 'all' })"
        />
        <div ref="engagementRef" class="relative">
          <button
            type="button"
            data-testid="filter-panel-engagement-toggle"
            class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors border whitespace-nowrap focus-visible:ring-2 focus-visible:ring-focus-ring/30 focus-visible:outline-none"
            :class="modelValue.technicalViewed
              ? 'bg-teal-600 text-white border-teal-600 hover:bg-teal-700'
              : 'bg-surface text-text-muted dark:text-gray-400 border-border-default hover:border-gray-300 dark:hover:border-gray-500'"
            @click="engagementOpen = !engagementOpen"
          >
            🔬 Engagement
            <span
              v-if="modelValue.technicalViewed"
              class="inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold bg-surface text-teal-600"
            >1</span>
            <svg class="w-3 h-3 ml-0.5 opacity-60" :class="{ 'rotate-180': engagementOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <Transition name="dropdown-fade">
            <div
              v-if="engagementOpen"
              class="absolute top-full left-0 mt-1 z-50 w-60 bg-surface border border-border-default rounded-xl shadow-lg py-2"
            >
              <label class="flex items-center gap-2.5 px-3 py-2 text-sm text-text-default hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
                <input
                  type="checkbox"
                  data-testid="filter-panel-technical-viewed"
                  :checked="modelValue.technicalViewed"
                  class="w-3.5 h-3.5 rounded border-gray-300 accent-teal-600"
                  @change="emit('update:modelValue', { ...modelValue, technicalViewed: $event.target.checked })"
                />
                <span>Solo det. técnico visto</span>
              </label>
            </div>
          </Transition>
        </div>
        <div class="flex-1" />
        <button
          v-if="filterCount > 0"
          type="button"
          data-testid="filter-panel-reset"
          class="text-xs text-gray-400 dark:text-text-muted hover:text-red-500 dark:hover:text-red-400 transition-colors font-medium whitespace-nowrap"
          @click="emit('reset')"
        >
          Limpiar todo
        </button>
      </div>
    </div>

    <div v-if="activeChips.length > 0" class="flex flex-wrap items-center gap-1.5 mt-2 px-1">
      <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-text-muted mr-0.5">Activos:</span>
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary-soft dark:bg-emerald-900/30 text-text-brand dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700"
      >
        {{ chip.label }}
        <button
          type="button"
          :data-testid="`filter-chip-clear-${chip.key}`"
          class="ml-0.5 hover:text-red-500 dark:hover:text-red-400 leading-none"
          @click="clearChip(chip.key)"
        >&times;</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onClickOutside } from '@vueuse/core';
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

const engagementRef = ref(null);
const engagementOpen = ref(false);
onClickOutside(engagementRef, () => { engagementOpen.value = false; });

const currencyOptions = [
  { value: 'COP', label: 'COP' },
  { value: 'USD', label: 'USD' },
];

const languageOptions = [
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
];

const activeStatusOptions = [
  { value: 'active', label: 'Activas' },
  { value: 'inactive', label: 'Inactivas' },
];

function formatRange(min, max, unit = '') {
  const u = unit ? ` ${unit}` : '';
  if (min != null && max != null) return `${min}–${max}${u}`;
  if (min != null) return `≥ ${min}${u}`;
  if (max != null) return `≤ ${max}${u}`;
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

  if (mv.statuses?.length)
    chips.push({ key: 'statuses', label: `Estado: ${mv.statuses.map((s) => statusLabelMap[s] || s).join(', ')}` });

  if (mv.projectTypes?.length)
    chips.push({ key: 'projectTypes', label: `Tipo: ${mv.projectTypes.map((t) => projectTypeLabelMap[t] || t).join(', ')}` });

  if (mv.marketTypes?.length)
    chips.push({ key: 'marketTypes', label: `Mercado: ${mv.marketTypes.map((t) => marketTypeLabelMap[t] || t).join(', ')}` });

  if (mv.currencies?.length)
    chips.push({ key: 'currencies', label: `Moneda: ${mv.currencies.join(', ')}` });

  if (mv.languages?.length)
    chips.push({ key: 'languages', label: `Idioma: ${mv.languages.join(', ').toUpperCase()}` });

  const inv = formatRange(mv.investmentMin, mv.investmentMax);
  if (inv) chips.push({ key: 'investment', label: `Inversión: ${inv}` });

  const hs = formatRange(mv.heatScoreMin, mv.heatScoreMax, '/ 10');
  if (hs) chips.push({ key: 'heatScore', label: `Heat Score: ${hs}` });

  const vc = formatRange(mv.viewCountMin, mv.viewCountMax);
  if (vc) chips.push({ key: 'viewCount', label: `Vistas: ${vc}` });

  const cr = formatDateRange(mv.createdAfter, mv.createdBefore);
  if (cr) chips.push({ key: 'createdRange', label: `Creación: ${cr}` });

  const ar = formatDateRange(mv.lastActivityAfter, mv.lastActivityBefore);
  if (ar) chips.push({ key: 'activityRange', label: `Actividad: ${ar}` });

  if (mv.isActive !== 'all')
    chips.push({ key: 'isActive', label: mv.isActive === 'active' ? 'Solo activas' : 'Solo inactivas' });

  if (mv.technicalViewed)
    chips.push({ key: 'technicalViewed', label: 'Det. técnico visto' });

  return chips;
});

const CHIP_RESET = {
  statuses:       (mv) => { mv.statuses = []; },
  projectTypes:   (mv) => { mv.projectTypes = []; },
  marketTypes:    (mv) => { mv.marketTypes = []; },
  currencies:     (mv) => { mv.currencies = []; },
  languages:      (mv) => { mv.languages = []; },
  investment:     (mv) => { mv.investmentMin = null; mv.investmentMax = null; },
  heatScore:      (mv) => { mv.heatScoreMin = null; mv.heatScoreMax = null; },
  viewCount:      (mv) => { mv.viewCountMin = null; mv.viewCountMax = null; },
  createdRange:   (mv) => { mv.createdAfter = null; mv.createdBefore = null; },
  activityRange:  (mv) => { mv.lastActivityAfter = null; mv.lastActivityBefore = null; },
  isActive:       (mv) => { mv.isActive = 'all'; },
  technicalViewed:(mv) => { mv.technicalViewed = false; },
};

function clearChip(key) {
  const mv = { ...props.modelValue };
  CHIP_RESET[key]?.(mv);
  emit('update:modelValue', mv);
}
</script>
