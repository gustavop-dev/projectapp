<template>
  <div v-show="isOpen" class="mb-4">
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl divide-y divide-gray-100 dark:divide-gray-700/60">

      <!-- Estado -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 w-[5.5rem] shrink-0">Estado</span>
        <ProposalFilterDropdown
          label="Estado"
          :options="statusOptions"
          :model-value="modelValue.statuses"
          @update:model-value="emit('update:modelValue', { ...modelValue, statuses: $event })"
        />
      </div>

      <!-- Inversión -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 w-[5.5rem] shrink-0">Inversión</span>
        <ProposalFilterRangeDropdown
          label="Monto"
          type="number"
          min-placeholder="Mín"
          max-placeholder="Máx"
          :min-value="modelValue.investmentMin"
          :max-value="modelValue.investmentMax"
          @update:min-value="emit('update:modelValue', { ...modelValue, investmentMin: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, investmentMax: $event })"
        />
      </div>

      <!-- Fechas -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 w-[5.5rem] shrink-0">Fechas</span>
        <ProposalFilterRangeDropdown
          label="Creado"
          type="date"
          min-placeholder="Desde"
          max-placeholder="Hasta"
          :min-value="modelValue.createdAfter"
          :max-value="modelValue.createdBefore"
          @update:min-value="emit('update:modelValue', { ...modelValue, createdAfter: $event })"
          @update:max-value="emit('update:modelValue', { ...modelValue, createdBefore: $event })"
        />
      </div>

      <!-- Limpiar todo -->
      <div class="flex items-center gap-2 px-3 py-2.5">
        <div class="flex-1" />
        <button
          v-if="filterCount > 0"
          type="button"
          class="text-xs text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors font-medium whitespace-nowrap"
          @click="emit('reset')"
        >
          Limpiar todo
        </button>
      </div>
    </div>

    <!-- Active filter chips -->
    <div v-if="activeChips.length > 0" class="flex flex-wrap items-center gap-1.5 mt-2 px-1">
      <span class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mr-0.5">Activos:</span>
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700"
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
import { STATUS_META } from '~/stores/diagnostics_constants';

const props = defineProps({
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: false },
  filterCount: { type: Number, default: 0 },
});

const emit = defineEmits(['update:modelValue', 'reset']);

const statusOptions = Object.entries(STATUS_META).map(([value, meta]) => ({
  value,
  label: meta.label,
}));

const statusLabelMap = Object.fromEntries(
  Object.entries(STATUS_META).map(([value, meta]) => [value, meta.label]),
);

function formatRange(min, max) {
  if (min != null && max != null && min !== '' && max !== '') return `${min}–${max}`;
  if (min != null && min !== '') return `≥ ${min}`;
  if (max != null && max !== '') return `≤ ${max}`;
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

  if (mv.statuses?.length) {
    chips.push({
      key: 'statuses',
      label: `Estado: ${mv.statuses.map((s) => statusLabelMap[s] || s).join(', ')}`,
    });
  }

  const inv = formatRange(mv.investmentMin, mv.investmentMax);
  if (inv) chips.push({ key: 'investment', label: `Inversión: ${inv}` });

  const created = formatDateRange(mv.createdAfter, mv.createdBefore);
  if (created) chips.push({ key: 'created', label: `Creado: ${created}` });

  return chips;
});

const CHIP_RESET = {
  statuses:   (mv) => { mv.statuses = []; },
  investment: (mv) => { mv.investmentMin = null; mv.investmentMax = null; },
  created:    (mv) => { mv.createdAfter = null; mv.createdBefore = null; },
};

function clearChip(key) {
  const mv = { ...props.modelValue };
  CHIP_RESET[key]?.(mv);
  emit('update:modelValue', mv);
}
</script>
