<template>
  <div class="space-y-3" data-testid="client-bulk-summary">
    <!--
      Desglose por grupo. En una selección mixta las dos operaciones se
      cuentan por separado: asignar a una fila suelta y quitarle el cliente a
      otra para dárselo a este no son lo mismo, aunque el botón sea uno.
    -->
    <ul class="space-y-1 text-sm">
      <li
        v-if="plan.toAssign.length"
        class="flex items-center gap-2 text-text-default"
        data-testid="client-bulk-summary-assign"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-success-strong flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.toAssign.length }}</span>
          {{ plan.toAssign.length === 1 ? 'sin cliente pasa a' : 'sin cliente pasan a' }}
          {{ plan.targetClientLabel }}
        </span>
      </li>
      <li
        v-if="plan.toReassign.length"
        class="flex items-center gap-2 text-text-default"
        data-testid="client-bulk-summary-reassign"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-warning-strong flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.toReassign.length }}</span>
          {{ plan.toReassign.length === 1 ? 'cambia de cliente a' : 'cambian de cliente a' }}
          {{ plan.targetClientLabel }}
        </span>
      </li>
      <li
        v-if="plan.toUnlink.length"
        class="flex items-center gap-2 text-text-default"
        data-testid="client-bulk-summary-unlink"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-danger-strong flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.toUnlink.length }}</span>
          {{ plan.toUnlink.length === 1 ? 'queda sin cliente' : 'quedan sin cliente' }}
        </span>
      </li>
      <li
        v-if="plan.unchanged.length"
        class="flex items-center gap-2 text-text-subtle"
        data-testid="client-bulk-summary-unchanged"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-border-default flex-shrink-0" />
        <span>
          <span class="font-semibold tabular-nums">{{ plan.unchanged.length }}</span>
          sin cambios
        </span>
      </li>
    </ul>

    <!-- Los registros, uno por uno: es una acción masiva y el alcance exacto
         no puede quedar en un número. -->
    <div>
      <p class="text-xs font-semibold uppercase tracking-wide text-text-subtle mb-1.5">
        Registros afectados ({{ plan.affected.length }})
      </p>
      <ul
        class="max-h-64 overflow-y-auto rounded-lg border border-border-muted bg-surface-muted divide-y divide-border-muted"
        data-testid="client-bulk-summary-list"
      >
        <li
          v-for="row in plan.affected"
          :key="row.id"
          class="flex items-baseline justify-between gap-3 px-3 py-1.5 text-xs"
        >
          <span class="text-text-default truncate">{{ recordLabel(row) }}</span>
          <span class="text-text-muted whitespace-nowrap flex-shrink-0">
            {{ clientLabelOf(row) }}
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
import { clientLabelOf, NO_CLIENT_LABEL } from '~/utils/incomeClients';

/**
 * Body of the bulk client (un)assignment confirmation: the per-group counts
 * and the full list of records the action will write, each showing where its
 * client goes from and to.
 *
 * Purely presentational — it renders whatever `buildAssignmentPlan` decided.
 */
const props = defineProps({
  /** Plan from `buildAssignmentPlan`. */
  plan: { type: Object, required: true },
  /** (row) => the row's identity in the list (domain, concept, ...). */
  recordLabel: { type: Function, required: true },
});

const destinationLabel = computed(
  () => (props.plan.mode === 'unlink' ? NO_CLIENT_LABEL : props.plan.targetClientLabel),
);
</script>
