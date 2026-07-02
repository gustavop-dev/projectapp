<template>
  <div v-show="isOpen" class="mb-4">
    <div class="divide-y divide-border-muted rounded-xl border border-border-default bg-surface">

      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="w-[5.5rem] shrink-0 text-[10px] font-semibold uppercase tracking-wider text-text-subtle">Categoria</span>
        <ProposalFilterDropdown
          label="Seccion"
          :options="categoryOptions"
          :model-value="modelValue.categories"
          @update:model-value="emit('update:modelValue', { ...modelValue, categories: $event })"
        />
      </div>

      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="w-[5.5rem] shrink-0 text-[10px] font-semibold uppercase tracking-wider text-text-subtle">Audiencia</span>
        <ProposalFilterDropdown
          label="Quien la ve"
          :options="audienceOptions"
          :model-value="modelValue.audiences"
          @update:model-value="emit('update:modelValue', { ...modelValue, audiences: $event })"
        />
      </div>

      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span class="w-[5.5rem] shrink-0 text-[10px] font-semibold uppercase tracking-wider text-text-subtle">Tipo</span>
        <ProposalFilterDropdown
          label="Tipo de vista"
          :options="typeOptions"
          :model-value="modelValue.viewTypes"
          @update:model-value="emit('update:modelValue', { ...modelValue, viewTypes: $event })"
        />
      </div>

      <div class="flex items-center gap-2 px-3 py-2.5">
        <div class="flex-1" />
        <button
          v-if="filterCount > 0"
          type="button"
          class="whitespace-nowrap text-xs font-medium text-text-subtle transition-colors hover:text-danger-strong"
          @click="emit('reset')"
        >
          Limpiar todo
        </button>
      </div>
    </div>

    <!-- Active filter chips -->
    <div v-if="activeChips.length > 0" class="mt-2 flex flex-wrap items-center gap-1.5 px-1">
      <span class="mr-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-subtle">Activos:</span>
      <span
        v-for="chip in activeChips"
        :key="chip.key"
        class="inline-flex items-center gap-1 rounded-full bg-primary-soft px-2.5 py-1 text-xs font-medium text-text-brand"
      >
        {{ chip.label }}
        <button
          type="button"
          class="ml-0.5 leading-none hover:text-danger-strong"
          @click="clearChip(chip.key)"
        >&times;</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import ProposalFilterDropdown from '~/components/proposals/ProposalFilterDropdown.vue';
import {
  viewCategoryOptions as categoryOptions,
  viewAudienceOptions as audienceOptions,
  viewTypeOptions as typeOptions,
  viewCategoryLabelMap as categoryLabelMap,
  viewAudienceLabelMap as audienceLabelMap,
  viewTypeLabelMap as typeLabelMap,
} from '~/constants/viewMapFilterOptions.js';

const props = defineProps({
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: false },
  filterCount: { type: Number, default: 0 },
});

const emit = defineEmits(['update:modelValue', 'reset']);

const activeChips = computed(() => {
  const chips = [];
  const mv = props.modelValue;

  if (mv.categories?.length)
    chips.push({ key: 'categories', label: `Seccion: ${mv.categories.map((c) => categoryLabelMap[c] || c).join(', ')}` });

  if (mv.audiences?.length)
    chips.push({ key: 'audiences', label: `Audiencia: ${mv.audiences.map((a) => audienceLabelMap[a] || a).join(', ')}` });

  if (mv.viewTypes?.length)
    chips.push({ key: 'viewTypes', label: `Tipo: ${mv.viewTypes.map((t) => typeLabelMap[t] || t).join(', ')}` });

  return chips;
});

const CHIP_RESET = {
  categories: (mv) => { mv.categories = []; },
  audiences:  (mv) => { mv.audiences = []; },
  viewTypes:  (mv) => { mv.viewTypes = []; },
};

function clearChip(key) {
  const mv = { ...props.modelValue };
  CHIP_RESET[key]?.(mv);
  emit('update:modelValue', mv);
}
</script>
