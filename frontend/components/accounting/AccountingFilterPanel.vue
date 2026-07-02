<template>
  <div v-show="isOpen" class="mb-4">
    <div class="bg-surface border border-border-default rounded-xl divide-y divide-border-muted">
      <div class="flex flex-wrap items-center gap-2 px-3 py-2.5">
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
            :min-value="modelValue[field.minKey]"
            :max-value="modelValue[field.maxKey]"
            @update:min-value="setValue(field.minKey, $event)"
            @update:max-value="setValue(field.maxKey, $event)"
          />
          <ProposalFilterRangeDropdown
            v-else-if="field.kind === 'daterange'"
            :label="field.label"
            type="date"
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

      <div class="flex items-center justify-end px-3 py-2.5">
        <button
          type="button"
          data-testid="accounting-filter-reset"
          class="text-xs text-text-muted hover:text-danger-strong transition-colors font-medium whitespace-nowrap"
          @click="emit('reset')"
        >
          Limpiar filtros
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
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
});

const emit = defineEmits(['update:modelValue', 'reset']);

function setValue(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}
</script>
