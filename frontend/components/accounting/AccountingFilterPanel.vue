<template>
  <div
    v-if="isOpen || appliedChips.length > 0 || resultsCount !== null"
    class="mb-4"
    data-testid="accounting-filter-panel"
  >
    <div class="bg-surface border border-border-default rounded-xl divide-y divide-border-muted">
      <div v-show="isOpen" class="flex flex-wrap items-center gap-x-4 gap-y-2.5 px-3 py-2.5">
        <template v-for="field in fields" :key="field.key || `${field.minKey}-${field.maxKey}`">
          <ProposalFilterDropdown
            v-if="field.kind === 'multi'"
            :label="field.label"
            :options="field.options"
            :model-value="modelValue[field.key] || []"
            @update:model-value="setValue(field.key, $event)"
          />
          <ProposalFilterRangeDropdown
            v-else-if="field.kind === 'range'"
            :label="field.label"
            :type="field.type || 'number'"
            live
            :min-value="modelValue[field.minKey]"
            :max-value="modelValue[field.maxKey]"
            @update:min-value="setValue(field.minKey, $event)"
            @update:max-value="setValue(field.maxKey, $event)"
          />
          <ProposalFilterRangeDropdown
            v-else-if="field.kind === 'daterange'"
            :label="field.label"
            type="date"
            live
            min-placeholder="Desde"
            max-placeholder="Hasta"
            :min-value="modelValue[field.minKey]"
            :max-value="modelValue[field.maxKey]"
            @update:min-value="setValue(field.minKey, $event)"
            @update:max-value="setValue(field.maxKey, $event)"
          />
          <div v-else-if="field.kind === 'segmented'" class="flex items-center gap-2">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-text-muted whitespace-nowrap">
              {{ field.label }}
            </span>
            <BaseSegmented
              size="sm"
              :model-value="modelValue[field.key]"
              :options="field.options"
              @update:model-value="setValue(field.key, $event)"
            />
          </div>
        </template>
      </div>

      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
        <span
          v-if="resultsCount !== null"
          class="text-xs text-text-muted tabular-nums font-medium whitespace-nowrap"
          data-testid="accounting-results-count"
        >
          {{ resultsCount }} {{ resultsCount === 1 ? 'resultado' : 'resultados' }}
        </span>

        <span
          v-for="chip in appliedChips"
          :key="chip.id"
          class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-info-soft text-info-strong font-medium"
          data-testid="accounting-filter-chip"
        >
          {{ chip.label }}
          <button
            type="button"
            class="rounded-full hover:bg-info-strong/10 transition-colors"
            :aria-label="`Quitar filtro ${chip.label}`"
            @click="removeChip(chip)"
          >
            <XMarkIcon class="w-3 h-3" />
          </button>
        </span>

        <span v-if="appliedChips.length === 0 && resultsCount !== null" class="text-xs text-text-subtle">
          Sin filtros aplicados
        </span>

        <button
          v-if="appliedChips.length > 0"
          type="button"
          data-testid="accounting-filter-reset"
          class="ml-auto text-xs text-text-muted hover:text-danger-strong transition-colors font-medium whitespace-nowrap"
          @click="emit('reset')"
        >
          Limpiar filtros
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import ProposalFilterDropdown from '~/components/proposals/ProposalFilterDropdown.vue';
import ProposalFilterRangeDropdown from '~/components/proposals/ProposalFilterRangeDropdown.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';

const props = defineProps({
  /**
   * Field config, one of:
   * { kind: 'multi', key, label, options: [{ value, label }] }
   * { kind: 'range', minKey, maxKey, label, type: 'number' }
   * { kind: 'daterange', minKey, maxKey, label }
   * { kind: 'segmented', key, label, options: [{ value, label }] }
   */
  fields: { type: Array, required: true },
  modelValue: { type: Object, required: true },
  isOpen: { type: Boolean, default: true },
  /** Filtered row count shown next to the applied-filter chips. */
  resultsCount: { type: Number, default: null },
  /** Applied (debounced) search text, rendered as a removable chip. */
  searchValue: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue', 'reset', 'clear-search']);

function setValue(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}

function hasValue(value) {
  if (Array.isArray(value)) return value.length > 0;
  return value !== '' && value !== null && value !== undefined;
}

function optionLabel(field, value) {
  const option = (field.options || []).find((opt) => opt.value === value);
  return option ? option.label : String(value);
}

const appliedChips = computed(() => {
  const chips = [];

  if (props.searchValue && props.searchValue.trim()) {
    chips.push({
      id: 'search',
      label: `"${props.searchValue.trim()}"`,
      clear: () => emit('clear-search'),
    });
  }

  for (const field of props.fields) {
    if (field.kind === 'multi') {
      for (const value of props.modelValue[field.key] || []) {
        chips.push({
          id: `${field.key}:${value}`,
          label: `${field.label}: ${optionLabel(field, value)}`,
          clear: () => setValue(
            field.key,
            (props.modelValue[field.key] || []).filter((v) => v !== value),
          ),
        });
      }
    } else if (field.kind === 'range' || field.kind === 'daterange') {
      const min = props.modelValue[field.minKey];
      const max = props.modelValue[field.maxKey];
      if (!hasValue(min) && !hasValue(max)) continue;
      let label = `${field.label}: `;
      if (hasValue(min) && hasValue(max)) label += `${min} – ${max}`;
      else if (hasValue(min)) label += `≥ ${min}`;
      else label += `≤ ${max}`;
      chips.push({
        id: `${field.minKey}-${field.maxKey}`,
        label,
        clear: () => emit('update:modelValue', {
          ...props.modelValue,
          [field.minKey]: '',
          [field.maxKey]: '',
        }),
      });
    } else if (field.kind === 'segmented') {
      const value = props.modelValue[field.key];
      if (!hasValue(value)) continue;
      chips.push({
        id: field.key,
        label: `${field.label}: ${optionLabel(field, value)}`,
        clear: () => setValue(field.key, ''),
      });
    }
  }

  return chips;
});

function removeChip(chip) {
  chip.clear();
}
</script>
