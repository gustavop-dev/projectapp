<script setup>
import { formatDateTime } from '~/utils/formatDate';
import {
  formatStateDuration,
  relativeStateTime,
  stateBadgeVariant,
} from '~/utils/documentState';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  history: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  title: { type: String, default: 'Historial de estados' },
  testId: { type: String, default: 'state-history' },
  allowOpeningCorrection: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'correct-opening']);

function updateOpen(value) {
  if (!value && props.busy) return;
  emit('update:modelValue', value);
}

const outcomeLabels = {
  completed: 'Cerrado',
  removed: 'Quitado',
  transitioned: 'Transición',
  merged: 'Fusionado',
};
const eventLabels = {
  opened: 'Apertura',
  closed: 'Cierre',
  removed: 'Retiro',
  transitioned: 'Transición',
  merged: 'Fusión',
  opened_at_corrected: 'Corrección de apertura',
};
</script>

<template>
  <BaseModal
    :model-value="modelValue"
    kind="detail"
    padding="none"
    :close-on-backdrop="!busy"
    :close-on-esc="!busy"
    @update:model-value="updateOpen"
  >
    <div class="flex items-center justify-between border-b border-border-muted px-5 py-4 sm:px-6">
      <div>
        <h2 class="text-lg font-semibold text-text-default">{{ title }}</h2>
        <p class="text-xs text-text-subtle">Episodios más recientes primero.</p>
      </div>
      <BaseActionButton
        action="close"
        label="Cerrar historial"
        :disabled="busy"
        @click="updateOpen(false)"
      />
    </div>
    <div
      class="max-h-[calc(100dvh-5rem)] space-y-3 overflow-y-auto p-4 sm:max-h-[75vh] sm:p-6"
      :data-testid="testId"
    >
      <p v-if="loading" class="py-8 text-center text-sm text-text-muted">Cargando historial…</p>
      <p v-else-if="!history.length" class="py-8 text-center text-sm text-text-muted">Todavía no hay episodios.</p>
      <template v-else>
        <article
          v-for="episode in history"
          :key="episode.id"
          class="rounded-xl border border-border-default bg-surface p-4"
        >
          <div class="flex flex-wrap items-start justify-between gap-2">
            <BaseBadge :variant="stateBadgeVariant(episode.state)">{{ episode.state.name }}</BaseBadge>
            <span class="text-xs font-medium text-text-muted">
              {{ episode.closed_at ? outcomeLabels[episode.outcome] : 'Vigente' }}
            </span>
          </div>
          <dl class="mt-3 grid gap-2 text-xs sm:grid-cols-2">
            <div>
              <dt class="text-text-subtle">Apertura</dt>
              <dd class="text-text-default">
                {{ episode.opening_time_known ? formatDateTime(episode.opened_at) : 'Fecha histórica desconocida' }}
                <span v-if="episode.opened_at" class="text-text-subtle">· {{ relativeStateTime(episode.opened_at) }}</span>
              </dd>
              <dd class="text-text-subtle">por {{ episode.opened_by_name || 'autor desconocido' }}</dd>
            </div>
            <div>
              <dt class="text-text-subtle">{{ episode.closed_at ? 'Cierre' : 'Duración abierta' }}</dt>
              <dd class="text-text-default">
                {{ episode.closed_at ? formatDateTime(episode.closed_at) : formatStateDuration(episode.duration_seconds) }}
                <span v-if="episode.closed_at" class="text-text-subtle">· {{ relativeStateTime(episode.closed_at) }}</span>
              </dd>
              <dd v-if="episode.closed_at" class="text-text-subtle">por {{ episode.closed_by_name || 'autor desconocido' }}</dd>
            </div>
          </dl>
          <p v-if="episode.close_note" class="mt-3 rounded-lg bg-surface-raised px-3 py-2 text-xs text-text-default">{{ episode.close_note }}</p>
          <div v-if="episode.notes?.length" class="mt-3 space-y-1">
            <p class="text-xs font-medium text-text-muted">Observaciones enlazadas</p>
            <div v-for="note in episode.notes" :key="note.id" class="rounded-lg border border-border-muted px-3 py-2 text-xs">
              <strong>{{ note.title || 'Observación' }}</strong> — {{ note.content }}
              <span class="text-text-subtle"> · {{ note.status }}</span>
            </div>
          </div>
          <details v-if="episode.events?.length" class="mt-3 rounded-lg border border-border-muted px-3 py-2">
            <summary class="cursor-pointer text-xs font-medium text-text-muted">
              Movimientos ({{ episode.events.length }})
            </summary>
            <ol class="mt-2 space-y-2">
              <li v-for="event in episode.events" :key="event.id" class="border-l-2 border-border-default pl-3 text-xs">
                <p class="font-medium text-text-default">{{ eventLabels[event.event_type] || event.event_type }}</p>
                <p class="text-text-subtle">
                  Efectivo: {{ event.effective_at ? formatDateTime(event.effective_at) : 'fecha desconocida' }}
                  <span v-if="event.effective_at">· {{ relativeStateTime(event.effective_at) }}</span>
                </p>
                <p class="text-text-subtle">
                  Registrado: {{ formatDateTime(event.recorded_at) }} · {{ relativeStateTime(event.recorded_at) }}
                  · {{ event.actor_name || 'autor desconocido' }}
                </p>
              </li>
            </ol>
          </details>
          <slot name="episode-actions" :episode="episode">
            <div v-if="allowOpeningCorrection" class="mt-3 flex justify-end">
              <BaseButton variant="ghost" size="sm" @click="emit('correct-opening', episode)">Corregir apertura</BaseButton>
            </div>
          </slot>
        </article>
      </template>
    </div>
  </BaseModal>
</template>
