<template>
  <div
    v-if="isOpen || appliedChips.length > 0 || resultsCount !== null"
    class="mb-4"
    data-testid="accounting-filter-panel"
  >
    <div class="bg-surface border border-border-default rounded-xl divide-y divide-border-muted">
      <div v-show="isOpen" class="flex flex-wrap items-center gap-x-4 gap-y-2.5 px-3 py-2.5">
        <div
          v-for="field in fields"
          :key="field.key || `${field.minKey}-${field.maxKey}`"
          class="w-full panel-portrait:w-auto"
        >
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
          <div v-else-if="field.kind === 'text'" class="flex flex-col gap-2 panel-portrait:flex-row panel-portrait:items-center">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-text-muted whitespace-nowrap">
              {{ field.label }}
            </span>
            <BaseInput
              size="sm"
              class="w-full panel-portrait:w-44"
              :placeholder="field.placeholder || ''"
              :data-testid="`accounting-filter-text-${field.key}`"
              :model-value="modelValue[field.key] || ''"
              @update:model-value="setValue(field.key, $event)"
            />
          </div>
          <div v-else-if="field.kind === 'segmented'" class="flex flex-col gap-2 panel-portrait:flex-row panel-portrait:items-center">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-text-muted whitespace-nowrap">
              {{ field.label }}
            </span>
            <BaseSegmentedMulti
              size="sm"
              full-width
              nowrap
              :label="field.label"
              :model-value="asArray(modelValue[field.key])"
              :options="field.options"
              :test-id-prefix="`accounting-filter-${field.key}`"
              @update:model-value="setValue(field.key, $event)"
            />
          </div>
        </div>

        <!-- Requisito: la lógica de combinación tiene que ser legible, porque el
             resultado sorprende cuando se marcan varias cosas a la vez. -->
        <p class="w-full text-[11px] text-text-subtle" data-testid="accounting-filter-logic-hint">
          Dentro de un filtro los valores se suman; entre filtros se restringen.
        </p>
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
          <!-- Whitespace here is content: the tags stay glued so the chip reads
               "Cobro: Sin pagos, Parcial" and not "Sin pagos ,Parcial". -->
          <span
            v-for="(value, index) in chip.values"
            :key="value.id"
            class="inline-flex items-center gap-1"
            data-testid="accounting-filter-chip-value"
          >{{ index > 0 ? ', ' : '' }}{{ value.label }}<button
            type="button"
            class="rounded-full hover:bg-info-strong/10 transition-colors"
            :aria-label="`Quitar filtro ${chip.label} ${value.label}`.trim()"
            :data-testid="`accounting-filter-chip-remove-${chip.id}-${value.token}`"
            @click="value.clear()"
          ><XMarkIcon class="w-3 h-3" /></button></span>
        </span>

        <span v-if="appliedChips.length === 0 && resultsCount !== null" class="text-xs text-text-subtle">
          Sin filtros aplicados
        </span>

        <BaseButton variant="link" size="sm" class="ml-auto whitespace-nowrap" v-if="appliedChips.length > 0" data-testid="accounting-filter-reset" @click="emit('reset')">
          Limpiar filtros
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import ProposalFilterDropdown from '~/components/proposals/ProposalFilterDropdown.vue';
import ProposalFilterRangeDropdown from '~/components/proposals/ProposalFilterRangeDropdown.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseSegmentedMulti from '~/components/base/BaseSegmentedMulti.vue';

const props = defineProps({
  /**
   * Field config, one of:
   * { kind: 'multi', key, label, options: [{ value, label }] }
   * { kind: 'range', minKey, maxKey, label, type: 'number' }
   * { kind: 'daterange', minKey, maxKey, label }
   * { kind: 'segmented', key, label, options: [{ value, label }] }
   * { kind: 'text', key, label, placeholder }
   *
   * `multi` and `segmented` are both multi-valued; they differ only in the
   * control. `segmented` lays every option out flat (few, stable options that
   * are worth seeing at a glance); `multi` collapses into a checkbox dropdown
   * (long, data-derived lists like clients).
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

/** A tab saved before this dimension went multi-valued still holds a scalar. */
function asArray(value) {
  if (Array.isArray(value)) return value;
  return value === '' || value === null || value === undefined ? [] : [value];
}

function hasValue(value) {
  if (Array.isArray(value)) return value.length > 0;
  return value !== '' && value !== null && value !== undefined;
}

function optionLabel(field, value) {
  const option = (field.options || []).find((opt) => opt.value === value);
  return option ? option.label : String(value);
}

/**
 * One chip per DIMENSION, listing the values chosen inside it — "Cobro: Sin
 * pagos, Parcial" — each with its own ⨯ so one value can go without dismantling
 * the whole dimension.
 *
 * A single-value dimension renders exactly as it always did ("Tipo: Líquido",
 * one chip, one button): that is deliberate, not incidental. The common case
 * must not get noisier just because the uncommon one became possible.
 */
const appliedChips = computed(() => {
  const chips = [];

  if (props.searchValue && props.searchValue.trim()) {
    const text = props.searchValue.trim();
    chips.push({
      id: 'search',
      label: '',
      values: [{ id: 'search', token: 'q', label: `"${text}"`, clear: () => emit('clear-search') }],
    });
  }

  for (const field of props.fields) {
    if (field.kind === 'multi' || field.kind === 'segmented') {
      const selected = asArray(props.modelValue[field.key]);
      if (!selected.length) continue;
      chips.push({
        id: field.key,
        label: `${field.label}:`,
        values: selected.map((value) => ({
          id: `${field.key}:${value}`,
          token: value,
          label: optionLabel(field, value),
          clear: () => setValue(field.key, selected.filter((v) => v !== value)),
        })),
      });
    } else if (field.kind === 'range' || field.kind === 'daterange') {
      const min = props.modelValue[field.minKey];
      const max = props.modelValue[field.maxKey];
      if (!hasValue(min) && !hasValue(max)) continue;
      let label = '';
      if (hasValue(min) && hasValue(max)) label = `${min} – ${max}`;
      else if (hasValue(min)) label = `≥ ${min}`;
      else label = `≤ ${max}`;
      chips.push({
        id: `${field.minKey}-${field.maxKey}`,
        label: `${field.label}:`,
        values: [{
          id: `${field.minKey}-${field.maxKey}`,
          token: 'range',
          label,
          clear: () => emit('update:modelValue', {
            ...props.modelValue,
            [field.minKey]: '',
            [field.maxKey]: '',
          }),
        }],
      });
    } else if (field.kind === 'text') {
      const value = props.modelValue[field.key];
      if (!hasValue(value) || !String(value).trim()) continue;
      chips.push({
        id: field.key,
        label: `${field.label}:`,
        values: [{
          id: field.key,
          token: 'text',
          label: String(value).trim(),
          clear: () => setValue(field.key, ''),
        }],
      });
    }
  }

  return chips;
});
</script>
