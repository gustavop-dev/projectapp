<script setup>
import { stateBadgeVariant } from '~/utils/documentState';

const localePath = useLocalePath();

defineProps({
  states: { type: Array, default: () => [] },
  activeIds: { type: Array, default: () => [] },
  withoutIds: { type: Array, default: () => [] },
  activePreset: { type: String, default: '' },
});
defineEmits(['toggle', 'toggle-absence', 'clear', 'preset']);

const presets = [
  { value: 'needs_fix', label: 'Algo por solucionar' },
  { value: 'sent_not_closed', label: 'Enviados sin cerrar' },
  { value: 'closed', label: 'Cerrados' },
  { value: 'unclassified', label: 'Por clasificar' },
];
</script>

<template>
  <div class="space-y-2" data-testid="document-state-filters">
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-xs font-medium text-text-muted">Consultas:</span>
      <button
        v-for="preset in presets"
        :key="preset.value"
        type="button"
        class="rounded-full border px-2.5 py-1 text-xs font-medium transition-colors"
        :class="activePreset === preset.value ? 'border-primary-strong bg-primary-soft text-text-brand' : 'border-border-default bg-surface text-text-muted hover:bg-surface-raised'"
        :data-testid="`document-state-preset-${preset.value}`"
        @click="$emit('preset', activePreset === preset.value ? '' : preset.value)"
      >
        {{ preset.label }}
      </button>
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-xs font-medium text-text-muted">Estados:</span>
      <button
        v-for="state in states"
        :key="state.id"
        type="button"
        class="rounded-full border px-2.5 py-1 text-xs font-medium transition-colors"
        :class="activeIds.includes(state.id) ? 'border-primary-strong bg-primary-soft text-text-brand' : 'border-border-default bg-surface text-text-muted hover:bg-surface-raised'"
        :data-testid="`document-state-filter-${state.id}`"
        @click="$emit('toggle', state.id)"
      >
        <BaseActionIcon v-if="state.system_key === 'needs_fix'" action="analyze" />
        {{ state.name }}
      </button>
      <button
        v-for="state in states.filter((item) => item.system_key === 'closed')"
        :key="`without-${state.id}`"
        type="button"
        class="rounded-full border px-2.5 py-1 text-xs font-medium"
        :class="withoutIds.includes(state.id) ? 'border-warning-strong bg-warning-soft text-warning-strong' : 'border-border-default bg-surface text-text-muted'"
        :data-testid="`document-state-without-${state.id}`"
        @click="$emit('toggle-absence', state.id)"
      >
        Sin {{ state.name.toLowerCase() }}
      </button>
      <button
        v-if="activeIds.length || withoutIds.length || activePreset"
        type="button"
        class="text-xs text-text-muted underline"
        @click="$emit('clear')"
      >
        Limpiar
      </button>
      <NuxtLink
        :to="localePath('/panel/documents/statuses')"
        data-testid="document-state-catalog-link"
        class="ml-auto text-xs font-medium text-text-brand"
      >
        Administrar estados
      </NuxtLink>
    </div>
  </div>
</template>
