<template>
  <div class="space-y-6">
    <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-700/30 rounded-xl p-4 text-xs text-blue-900 dark:text-blue-200">
      <p class="font-semibold mb-1">📅 Cronograma del proyecto</p>
      <p class="leading-relaxed">
        Define las fechas de inicio y fin para cada etapa. El equipo recibirá un aviso cuando
        haya transcurrido el <strong>70%</strong> del tiempo planeado de la etapa, y un recordatorio
        cuando ya se cumpla la fecha fin (cada 3 días hasta marcarla como completada).
      </p>
    </div>

    <section
      v-for="row in stagesWithStatus"
      :key="row.stage_key"
      class="bg-surface border border-border-muted rounded-xl p-5"
      :data-testid="`stage-card-${row.stage_key}`"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <span class="text-2xl" aria-hidden="true">{{ row.emoji }}</span>
          <h3 class="text-sm font-semibold text-text-default dark:text-white">
            Etapa de {{ row.stage_label }}
          </h3>
        </div>
        <span
          v-if="row.completed_at"
          class="px-2 py-0.5 bg-primary-soft text-text-brand rounded text-[11px] font-medium"
          :data-testid="`stage-status-${row.stage_key}`"
        >
          🟢 Completada
        </span>
        <span
          v-else-if="row.status.kind === 'overdue'"
          class="px-2 py-0.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded text-[11px] font-medium"
          :data-testid="`stage-status-${row.stage_key}`"
        >
          🔴 Vencida hace {{ row.status.label }}
        </span>
        <span
          v-else-if="row.status.kind === 'pending'"
          class="px-2 py-0.5 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded text-[11px] font-medium"
          :data-testid="`stage-status-${row.stage_key}`"
        >
          🟡 Faltan {{ row.status.label }}
        </span>
        <span
          v-else-if="row.status.kind === 'not_started'"
          class="px-2 py-0.5 bg-surface-raised text-text-muted/60 rounded text-[11px] font-medium"
          :data-testid="`stage-status-${row.stage_key}`"
        >
          ⏳ Aún no inicia
        </span>
        <span
          v-else
          class="px-2 py-0.5 bg-surface-raised text-text-muted dark:text-text-subtle rounded text-[11px] font-medium"
          :data-testid="`stage-status-${row.stage_key}`"
        >
          Sin programar
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label
            :for="`start-${row.stage_key}`"
            class="block text-xs text-text-muted dark:text-white/70 mb-1"
          >
            Fecha de inicio
          </label>
          <input
            :id="`start-${row.stage_key}`"
            v-model="formState[row.stage_key].start_date"
            type="date"
            :disabled="!!row.completed_at"
            :data-testid="`stage-start-${row.stage_key}`"
            class="w-full px-3 py-2 border border-border-default dark:bg-primary-strong dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 disabled:bg-surface-raised disabled:text-text-subtle dark:disabled:text-green-light/40"
          />
        </div>
        <div>
          <label
            :for="`end-${row.stage_key}`"
            class="block text-xs text-text-muted dark:text-white/70 mb-1"
          >
            Fecha fin planeada
          </label>
          <input
            :id="`end-${row.stage_key}`"
            v-model="formState[row.stage_key].end_date"
            type="date"
            :disabled="!!row.completed_at"
            :data-testid="`stage-end-${row.stage_key}`"
            class="w-full px-3 py-2 border border-border-default dark:bg-primary-strong dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-focus-ring/30 disabled:bg-surface-raised disabled:text-text-subtle dark:disabled:text-green-light/40"
          />
        </div>
      </div>

      <p
        v-if="formError[row.stage_key]"
        class="mt-1 text-xs text-red-600"
        :data-testid="`stage-error-${row.stage_key}`"
      >
        {{ formError[row.stage_key] }}
      </p>

      <div class="flex items-center gap-3">
        <button
          type="button"
          :disabled="isSaving[row.stage_key] || !!row.completed_at"
          :data-testid="`stage-save-${row.stage_key}`"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-strong transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="handleSave(row.stage_key)"
        >
          {{ isSaving[row.stage_key] ? 'Guardando…' : 'Guardar fechas' }}
        </button>
        <button
          v-if="!row.completed_at"
          type="button"
          :disabled="isCompleting[row.stage_key]"
          :data-testid="`stage-complete-${row.stage_key}`"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface-raised text-text-default rounded-lg text-xs font-medium hover:bg-surface-raised transition-colors disabled:opacity-50"
          @click="handleComplete(row.stage_key)"
        >
          ✅ {{ isCompleting[row.stage_key] ? 'Marcando…' : 'Marcar como completada' }}
        </button>
        <span
          v-if="row.completed_at"
          class="text-xs text-text-muted"
        >
          Completada el {{ formatHumanDate(row.completed_at) }}
        </span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue';
import { useProposalStore } from '~/stores/proposals';
import { useStageStatus } from '~/composables/useStageStatus';
import { usePanelToast } from '~/composables/usePanelToast';

const { showToast } = usePanelToast();

const props = defineProps({
  proposal: { type: Object, required: true },
});

const proposalStore = useProposalStore();
const { computeStageStatus, formatHumanDate } = useStageStatus();

// Single source of truth for the placeholder catalog (rendered when the
// backend has no rows yet). Stage labels for real rows come from the
// serializer's get_stage_key_display.
const STAGE_DEFAULTS = [
  { stage_key: 'design', stage_label: 'Diseño', emoji: '🎨' },
  { stage_key: 'development', stage_label: 'Desarrollo', emoji: '💻' },
];

// Read straight from the store. The component does not own a copy.
// Falls back to props.proposal in case the parent passes a non-store
// object (e.g., in unit tests).
const stages = computed(() => {
  const source = proposalStore.currentProposal?.id === props.proposal?.id
    ? proposalStore.currentProposal
    : props.proposal;
  const existing = source?.project_stages || [];
  return STAGE_DEFAULTS.map((def) => {
    const found = existing.find((s) => s.stage_key === def.stage_key);
    return found
      ? {
          ...found,
          stage_label: found.stage_label || def.stage_label,
          emoji: def.emoji,
        }
      : { ...def, completed_at: null, start_date: null, end_date: null };
  });
});

// Precompute status once per render — avoids re-running computeStageStatus
// 5x per stage from the v-if/v-else-if chain.
const stagesWithStatus = computed(() =>
  stages.value.map((s) => ({ ...s, status: computeStageStatus(s) })),
);

// Form buffer (dirty state). Initialized once on mount and refreshed only
// when the underlying stage row's identity actually changes (e.g., the
// admin completes a stage from elsewhere). Untouched fields stay synced;
// in-progress edits are NOT clobbered by unrelated proposal mutations.
const formState = reactive({
  design: { start_date: '', end_date: '' },
  development: { start_date: '', end_date: '' },
});
const formError = reactive({ design: '', development: '' });
const isSaving = reactive({ design: false, development: false });
const isCompleting = reactive({ design: false, development: false });

function snapshotForm() {
  for (const stage of stages.value) {
    formState[stage.stage_key] = {
      start_date: stage.start_date || '',
      end_date: stage.end_date || '',
    };
    formError[stage.stage_key] = '';
  }
}

snapshotForm();

// Re-sync only when the stages array reference changes (after a successful
// save/complete). Shallow watch on the computed avoids the deep-watch
// firing on every unrelated proposal mutation.
watch(stages, () => snapshotForm());

async function handleSave(stageKey) {
  const dates = formState[stageKey];
  if (!dates.start_date || !dates.end_date) {
    formError[stageKey] = 'Debes especificar fecha de inicio y fecha fin.';
    return;
  }
  if (dates.start_date > dates.end_date) {
    formError[stageKey] = 'La fecha fin debe ser igual o posterior a la fecha de inicio.';
    return;
  }
  formError[stageKey] = '';
  isSaving[stageKey] = true;
  try {
    const result = await proposalStore.updateProjectStage(
      props.proposal.id,
      stageKey,
      { start_date: dates.start_date, end_date: dates.end_date },
    );
    if (result.success) {
      showToast({ type: 'success', text: 'Fechas de la etapa guardadas.' });
    } else {
      showToast({ type: 'error', text: 'No se pudo guardar. Revisa las fechas e inténtalo de nuevo.' });
    }
  } finally {
    isSaving[stageKey] = false;
  }
}

async function handleComplete(stageKey) {
  isCompleting[stageKey] = true;
  try {
    const result = await proposalStore.completeProjectStage(props.proposal.id, stageKey);
    if (result.success) {
      showToast({ type: 'success', text: 'Etapa marcada como completada.' });
    } else {
      showToast({ type: 'error', text: 'No se pudo marcar la etapa como completada.' });
    }
  } finally {
    isCompleting[stageKey] = false;
  }
}
</script>
