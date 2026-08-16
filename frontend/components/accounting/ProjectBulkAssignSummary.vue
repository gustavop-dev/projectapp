<template>
  <div class="space-y-3" data-testid="project-bulk-summary">
    <ul class="space-y-1 text-sm">
      <li
        v-if="plan.toAssign.length"
        class="flex items-center gap-2 text-text-default"
        data-testid="project-bulk-summary-assign"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-success-strong flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.toAssign.length }}</span>
          {{ plan.toAssign.length === 1 ? 'sin proyecto pasa a' : 'sin proyecto pasan a' }}
          {{ plan.targetProjectLabel }}
        </span>
      </li>
      <li
        v-if="plan.toReassign.length"
        class="flex items-center gap-2 text-text-default"
        data-testid="project-bulk-summary-reassign"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-warning-strong flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.toReassign.length }}</span>
          {{ plan.toReassign.length === 1 ? 'cambia de proyecto a' : 'cambian de proyecto a' }}
          {{ plan.targetProjectLabel }}
        </span>
      </li>
      <li
        v-if="plan.toUnlink.length"
        class="flex items-center gap-2 text-text-default"
        data-testid="project-bulk-summary-unlink"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-danger-strong flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.toUnlink.length }}</span>
          {{ plan.toUnlink.length === 1 ? 'queda sin proyecto' : 'quedan sin proyecto' }}
        </span>
      </li>
      <li
        v-if="plan.unchanged.length"
        class="flex items-center gap-2 text-text-subtle"
        data-testid="project-bulk-summary-unchanged"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-border-default flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.unchanged.length }}</span>
          sin cambios
        </span>
      </li>
    </ul>

    <!-- El grupo que la acción deja a propósito por fuera: un proyecto es de
         UN cliente, así que las filas de otro cliente no se tocan. -->
    <div
      v-if="plan.blockedClientMismatch.length"
      class="rounded-lg border border-border-default bg-surface-muted px-3 py-2"
      data-testid="project-bulk-summary-blocked"
    >
      <p class="text-xs font-semibold text-text-default mb-1">
        No se {{ plan.blockedClientMismatch.length === 1 ? 'toca' : 'tocan' }} (cliente distinto):
        reasigna primero su cliente.
      </p>
      <ul class="text-xs text-text-muted space-y-0.5">
        <li v-for="row in plan.blockedClientMismatch" :key="row.id" class="truncate">
          {{ recordLabel(row) }}
        </li>
      </ul>
    </div>

    <!-- Los registros, uno por uno: es una acción masiva y el alcance exacto
         no puede quedar en un número. -->
    <div>
      <p class="text-xs font-semibold uppercase tracking-wide text-text-subtle mb-1.5">
        Registros afectados ({{ plan.affected.length }})
      </p>
      <ul
        class="max-h-64 overflow-y-auto rounded-lg border border-border-muted bg-surface-muted divide-y divide-border-muted"
        data-testid="project-bulk-summary-list"
      >
        <li
          v-for="row in plan.affected"
          :key="row.id"
          class="flex items-baseline justify-between gap-3 px-3 py-1.5 text-xs"
        >
          <span class="text-text-default truncate">{{ recordLabel(row) }}</span>
          <span class="text-text-muted whitespace-nowrap flex-shrink-0">
            {{ row.project_name || 'Sin proyecto' }}
            <span aria-hidden="true">→</span>
            <span class="font-medium text-text-default">{{ destinationLabel }}</span>
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

/**
 * Body of the bulk project (un)assignment confirmation: per-group counts,
 * the blocked-by-ownership section, and the full origen → destino list.
 * Purely presentational — it renders whatever `buildProjectAssignmentPlan`
 * decided.
 */
const props = defineProps({
  /** Plan from `buildProjectAssignmentPlan`. */
  plan: { type: Object, required: true },
  /** (row) => the row's identity in the list (domain, concept, ...). */
  recordLabel: { type: Function, required: true },
});

const destinationLabel = computed(
  () => (props.plan.mode === 'unlink' ? 'Sin proyecto' : props.plan.targetProjectLabel),
);
</script>
