<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useDocumentStateStore } from '~/stores/document_states';
import { formatStateDuration, stateBadgeVariant } from '~/utils/documentState';

const props = defineProps({
  documentId: { type: [Number, String], required: true },
  episodes: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  disabledReason: {
    type: String,
    default: 'Esta cuenta de cobro ya fue emitida. Anúlala y crea una nueva para cambiar sus estados.',
  },
});
const emit = defineEmits(['changed', 'history']);
const stateStore = useDocumentStateStore();
const selectedStateId = ref('');
const useExactTime = ref(false);
const openedAt = ref('');
const newName = ref('');
const suggestions = ref([]);
const errorMessage = ref('');
let suggestionTimer;

const activeIds = computed(() => new Set(props.episodes.map((episode) => episode.state?.id)));
const availableGroups = computed(() => stateStore.statesByGroup.map((group) => ({
  ...group,
  states: group.states.filter((state) => !activeIds.value.has(state.id)),
})).filter((group) => group.states.length));

onMounted(() => stateStore.fetchCatalog());

watch(newName, (value) => {
  window.clearTimeout(suggestionTimer);
  suggestions.value = [];
  if (value.trim().length < 2) return;
  suggestionTimer = window.setTimeout(async () => {
    const result = await stateStore.suggest(value);
    if (result.success) suggestions.value = result.data;
  }, 250);
});

async function addState() {
  if (!selectedStateId.value) return;
  errorMessage.value = '';
  const value = useExactTime.value && openedAt.value
    ? new Date(openedAt.value).toISOString()
    : null;
  const result = await stateStore.openEpisode(props.documentId, selectedStateId.value, value);
  if (!result.success) {
    errorMessage.value = result.message;
    return;
  }
  selectedStateId.value = '';
  useExactTime.value = false;
  openedAt.value = '';
  emit('changed');
}

async function finishEpisode(episode, outcome) {
  const action = outcome === 'removed' ? 'quitar' : 'cerrar';
  if (!window.confirm(`¿${action === 'quitar' ? 'Quitar' : 'Cerrar'} "${episode.state.name}"?`)) return;
  const note = window.prompt(
    outcome === 'removed' ? '¿Por qué sobraba la marca? (opcional)' : '¿Qué se hizo? (opcional)',
    '',
  );
  if (note === null) return;
  const result = await stateStore.closeEpisode(props.documentId, episode.id, outcome, note);
  if (!result.success) {
    errorMessage.value = result.message;
    return;
  }
  emit('changed');
}

async function chooseSuggestion(state) {
  selectedStateId.value = state.id;
  newName.value = '';
  suggestions.value = [];
  await addState();
}

async function createInline(confirmSimilar = false) {
  const name = newName.value.trim();
  if (!name) return;
  errorMessage.value = '';
  const result = await stateStore.createState({ name, confirm_similar: confirmSimilar });
  if (result.needsConfirmation) {
    suggestions.value = result.suggestions;
    if (window.confirm('Hay estados parecidos. ¿Crear uno nuevo de todas formas?')) {
      await createInline(true);
    }
    return;
  }
  if (!result.success) {
    errorMessage.value = result.message;
    return;
  }
  newName.value = '';
  selectedStateId.value = result.data.id;
  await addState();
}
</script>

<template>
  <section class="space-y-3 rounded-xl border border-border-default bg-surface-raised p-4" data-testid="document-state-selector">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h3 class="text-sm font-semibold text-text-default">Estados</h3>
        <p class="text-xs text-text-subtle">El ciclo admite uno; las señales se suman.</p>
      </div>
      <BaseButton variant="ghost" size="sm" @click="$emit('history')">Historial ◷</BaseButton>
    </div>

    <div v-if="episodes.length" class="space-y-2">
      <div v-for="episode in episodes" :key="episode.id" class="flex flex-wrap items-center gap-2 rounded-lg bg-surface p-2">
        <BaseBadge :variant="stateBadgeVariant(episode.state)" size="sm">
          {{ episode.state.name }} · {{ formatStateDuration(episode.duration_seconds) }}
        </BaseBadge>
        <span class="mr-auto text-xs text-text-subtle">{{ episode.state.group_name }}</span>
        <BaseButton size="sm" variant="ghost" :data-testid="`document-state-close-${episode.id}`" :disabled="disabled" :disabled-reason="disabledReason" @click="finishEpisode(episode, 'completed')">Cerrar</BaseButton>
        <BaseButton size="sm" variant="danger-ghost" :data-testid="`document-state-remove-${episode.id}`" :disabled="disabled" :disabled-reason="disabledReason" @click="finishEpisode(episode, 'removed')">Quitar</BaseButton>
      </div>
    </div>
    <p v-else class="text-xs text-text-muted">Sin estados activos: queda en Por clasificar.</p>

    <div class="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
      <select
        v-model="selectedStateId"
        aria-label="Estado para agregar"
        data-testid="document-state-add-select"
        class="bg-input-bg rounded-lg border border-input-border px-3 py-2 text-sm"
        :disabled="disabled"
        :title="disabled ? disabledReason : undefined"
      >
        <option value="">Agregar un estado…</option>
        <optgroup v-for="group in availableGroups" :key="group.id" :label="group.name">
          <option v-for="state in group.states" :key="state.id" :value="state.id">{{ state.name }}</option>
        </optgroup>
      </select>
      <BaseButton
        data-testid="document-state-add"
        variant="primary"
        size="sm"
        :disabled="!selectedStateId || disabled"
        :disabled-reason="disabled ? disabledReason : 'Selecciona un estado para agregarlo.'"
        @click="addState"
      >Agregar</BaseButton>
    </div>
    <label class="flex items-center gap-2 text-xs text-text-muted">
      <BaseToggle v-model="useExactTime" size="sm" :disabled="disabled" :disabled-reason="disabledReason" />
      Registrar la fecha real de apertura
    </label>
    <input
      v-if="useExactTime"
      v-model="openedAt"
      type="datetime-local"
      :max="new Date().toISOString().slice(0, 16)"
      class="bg-input-bg w-full rounded-lg border border-input-border px-3 py-2 text-sm"
    />

    <div class="border-t border-border-muted pt-3">
      <p class="mb-2 text-xs font-medium text-text-muted">Crear al vuelo</p>
      <div class="flex gap-2">
        <BaseInput v-model="newName" data-testid="document-state-inline-name" placeholder="Nombre del nuevo estado" :disabled="disabled" :disabled-reason="disabledReason" @keyup.enter="createInline()" />
        <BaseButton data-testid="document-state-inline-create" variant="secondary" size="sm" :disabled="!newName.trim() || disabled" :disabled-reason="disabled ? disabledReason : 'Escribe el nombre del nuevo estado.'" @click="createInline()">Crear</BaseButton>
      </div>
      <div v-if="suggestions.length" class="mt-2 flex flex-wrap gap-1.5" data-testid="document-state-suggestions">
        <button
          v-for="state in suggestions"
          :key="state.id"
          type="button"
          class="rounded-full border border-border-default bg-surface px-2 py-1 text-xs text-text-default hover:bg-surface-raised"
          @click="chooseSuggestion(state)"
        >
          ¿{{ state.name }}?
        </button>
      </div>
    </div>
    <BaseAlert v-if="errorMessage" variant="danger" data-testid="document-state-error">{{ errorMessage }}</BaseAlert>
  </section>
</template>
