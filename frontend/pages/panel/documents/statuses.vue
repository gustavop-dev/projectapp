<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useDocumentStateStore } from '~/stores/document_states';
import { DOCUMENT_STATE_COLORS, stateBadgeVariant } from '~/utils/documentState';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });
useHead({ title: 'Estados de documentos | ProjectApp' });

const stateStore = useDocumentStateStore();
const notify = usePanelNotify();
const localePath = useLocalePath();
const includeRetired = ref(true);
const newState = reactive({ name: '', color: 'gray', group: '' });
const newGroup = reactive({ name: '', selection_mode: 'additive' });
const editing = reactive({});
const groupEditing = reactive({});
const mergeTargets = reactive({});

const groups = computed(() => stateStore.groups.map((group) => ({
  ...group,
  states: stateStore.states.filter((state) => state.group === group.id),
})));

onMounted(async () => {
  await stateStore.fetchCatalog({ includeRetired: includeRetired.value });
  if (!newState.group && stateStore.groups.length) {
    newState.group = stateStore.groups.find((group) => group.selection_mode === 'additive')?.id
      || stateStore.groups[0].id;
  }
});

async function createState(confirmSimilar = false) {
  const name = newState.name.trim();
  if (!name) return;
  const result = await stateStore.createState({ ...newState, name, confirm_similar: confirmSimilar });
  if (result.needsConfirmation) {
    const names = result.suggestions.map((item) => item.name).join(', ');
    if (window.confirm(`Se parecen a: ${names}. ¿Crear de todas formas?`)) {
      await createState(true);
    }
    return;
  }
  if (!result.success) {
    notify.error({ title: 'No se pudo crear', detail: result.message });
    return;
  }
  newState.name = '';
  notify.success({ title: 'Estado creado' });
}

function editDraft(state) {
  if (!editing[state.id]) {
    editing[state.id] = {
      name: state.name,
      color: state.color,
      group: state.group,
      order: state.order,
      incompatibility_ids: [...(state.incompatibility_ids || [])],
    };
  }
  return editing[state.id];
}

function groupDraft(group) {
  if (!groupEditing[group.id]) {
    groupEditing[group.id] = {
      name: group.name,
      selection_mode: group.selection_mode,
      order: group.order,
    };
  }
  return groupEditing[group.id];
}

async function saveGroup(group) {
  const result = await stateStore.updateGroup(group.id, groupDraft(group));
  if (result.success) {
    delete groupEditing[group.id];
    notify.success({ title: 'Grupo actualizado' });
  } else {
    notify.error({ title: 'No se pudo actualizar el grupo', detail: result.message });
  }
}

async function saveState(state) {
  const result = await stateStore.updateState(state.id, editDraft(state));
  if (result.success) {
    delete editing[state.id];
    notify.success({ title: 'Estado actualizado' });
  } else {
    notify.error({ title: 'No se pudo actualizar', detail: result.message });
  }
}

async function retire(state) {
  if (!window.confirm(`¿Retirar "${state.name}" del selector?`)) return;
  const result = await stateStore.retireState(state.id);
  if (result.success) notify.success({ title: 'Estado retirado' });
  else notify.error({ title: 'No se puede retirar', detail: result.message });
}

async function merge(state) {
  const target = mergeTargets[state.id];
  if (!target || !window.confirm(`¿Fusionar "${state.name}"? Su historial se conservará.`)) return;
  const result = await stateStore.mergeState(state.id, target);
  if (result.success) notify.success({ title: 'Estados fusionados' });
  else notify.error({ title: 'No se pudieron fusionar', detail: result.message });
}

async function createGroup() {
  const name = newGroup.name.trim();
  if (!name) return;
  const result = await stateStore.createGroup({ ...newGroup, name, order: stateStore.groups.length });
  if (result.success) {
    newGroup.name = '';
    notify.success({ title: 'Grupo creado' });
  } else {
    notify.error({ title: 'No se pudo crear el grupo', detail: result.message });
  }
}
</script>

<template>
  <main class="mx-auto w-full max-w-6xl space-y-6" data-testid="document-state-catalog">
    <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <NuxtLink :to="localePath('/panel/documents')" class="inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-default">
          <BaseActionIcon action="back" />
          Volver a documentos
        </NuxtLink>
        <h1 class="mt-2 text-2xl font-light text-text-default">Estados de documentos</h1>
        <p class="mt-1 max-w-2xl text-sm text-text-muted">Administra el ciclo, las señales, sus colores y las reglas de exclusión. Los episodios históricos nunca se borran.</p>
      </div>
    </header>

    <section class="grid gap-4 rounded-xl border border-border-default bg-surface p-5 lg:grid-cols-2">
      <form class="space-y-3" @submit.prevent="createState()">
        <h2 class="text-sm font-semibold text-text-default">Crear estado</h2>
        <div class="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
          <BaseInput v-model="newState.name" placeholder="Nombre" data-testid="catalog-new-state-name" />
          <select v-model="newState.group" aria-label="Grupo del nuevo estado" class="bg-input-bg rounded-lg border border-input-border px-3 py-2 text-sm">
            <option v-for="group in stateStore.groups.filter((item) => item.is_active)" :key="group.id" :value="group.id">{{ group.name }}</option>
          </select>
          <select v-model="newState.color" aria-label="Color del nuevo estado" class="bg-input-bg rounded-lg border border-input-border px-3 py-2 text-sm">
            <option v-for="color in DOCUMENT_STATE_COLORS" :key="color.value" :value="color.value">{{ color.label }}</option>
          </select>
        </div>
        <BaseButton type="submit" variant="primary" size="sm" data-testid="catalog-create-state" :disabled="!newState.name.trim()">Crear estado</BaseButton>
      </form>
      <form class="space-y-3 border-t border-border-muted pt-4 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0" @submit.prevent="createGroup">
        <h2 class="text-sm font-semibold text-text-default">Crear grupo</h2>
        <div class="flex gap-2">
          <BaseInput v-model="newGroup.name" placeholder="Nombre del grupo" />
          <select v-model="newGroup.selection_mode" aria-label="Modo del nuevo grupo" class="bg-input-bg rounded-lg border border-input-border px-3 py-2 text-sm">
            <option value="exclusive">Uno activo</option>
            <option value="additive">Varios activos</option>
          </select>
        </div>
        <BaseButton type="submit" variant="secondary" size="sm" data-testid="catalog-create-group" :disabled="!newGroup.name.trim()">Crear grupo</BaseButton>
      </form>
    </section>

    <section v-for="group in groups" :key="group.id" class="rounded-xl border border-border-default bg-surface" :data-testid="`catalog-group-${group.id}`">
      <div class="flex flex-col gap-3 border-b border-border-muted px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div class="grid flex-1 gap-2 sm:grid-cols-[minmax(0,1fr)_10rem_6rem_auto]">
          <BaseInput v-model="groupDraft(group).name" aria-label="Nombre del grupo" />
          <select v-model="groupDraft(group).selection_mode" class="bg-input-bg rounded-lg border border-input-border px-2 py-2 text-sm">
            <option value="exclusive">Uno activo</option>
            <option value="additive">Varios activos</option>
          </select>
          <BaseInput v-model.number="groupDraft(group).order" type="number" min="0" aria-label="Orden del grupo" />
          <BaseButton variant="secondary" size="sm" :data-testid="`catalog-save-group-${group.id}`" @click="saveGroup(group)">Guardar grupo</BaseButton>
        </div>
        <BaseBadge variant="neutral">{{ group.states.length }} estados</BaseBadge>
      </div>
      <div v-if="!group.states.length" class="p-5 text-sm text-text-muted">No hay estados en este grupo.</div>
      <div v-else class="divide-y divide-border-muted">
        <article v-for="state in group.states" :key="state.id" class="space-y-3 p-4 sm:p-5" :class="!state.is_active ? 'opacity-60' : ''" :data-testid="`catalog-state-${state.id}`">
          <div class="flex flex-wrap items-center gap-2">
            <BaseBadge :variant="stateBadgeVariant(state)">{{ state.name }}</BaseBadge>
            <BaseBadge v-if="state.system_key" variant="info" size="sm">Semilla</BaseBadge>
            <BaseBadge v-if="!state.is_active" variant="neutral" size="sm">Retirado</BaseBadge>
            <span class="text-xs text-text-muted">{{ state.active_document_count }} documentos activos · {{ state.historical_episode_count }} episodios</span>
          </div>
          <div v-if="state.is_active" class="grid gap-2 lg:grid-cols-[minmax(0,1fr)_8rem_10rem_6rem_auto]">
            <BaseInput v-model="editDraft(state).name" aria-label="Nombre del estado" />
            <select v-model="editDraft(state).color" class="bg-input-bg rounded-lg border border-input-border px-2 py-2 text-sm">
              <option v-for="color in DOCUMENT_STATE_COLORS" :key="color.value" :value="color.value">{{ color.label }}</option>
            </select>
            <select v-model="editDraft(state).group" class="bg-input-bg rounded-lg border border-input-border px-2 py-2 text-sm">
              <option v-for="item in stateStore.groups" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
            <BaseInput v-model.number="editDraft(state).order" type="number" min="0" aria-label="Orden" />
            <BaseButton variant="secondary" size="sm" :data-testid="`catalog-save-state-${state.id}`" @click="saveState(state)">Guardar</BaseButton>
          </div>
          <div v-if="state.is_active" class="flex flex-wrap items-center gap-2">
            <select v-model="mergeTargets[state.id]" :aria-label="`Destino para fusionar ${state.name}`" class="bg-input-bg rounded-lg border border-input-border px-2 py-1.5 text-xs">
              <option value="">Fusionar con…</option>
              <option v-for="target in stateStore.activeStates.filter((item) => item.id !== state.id && item.group === state.group)" :key="target.id" :value="target.id">{{ target.name }}</option>
            </select>
            <BaseButton variant="ghost" size="sm" :data-testid="`catalog-merge-state-${state.id}`" :disabled="!mergeTargets[state.id] || !!state.system_key" @click="merge(state)">Fusionar</BaseButton>
            <BaseButton variant="danger-ghost" size="sm" :data-testid="`catalog-retire-state-${state.id}`" @click="retire(state)">Retirar</BaseButton>
          </div>
          <details v-if="state.is_active" class="rounded-lg border border-border-muted bg-surface-raised px-3 py-2">
            <summary class="cursor-pointer text-xs font-medium text-text-muted">Combinaciones excluidas</summary>
            <div class="mt-2 flex flex-wrap gap-3">
              <label
                v-for="candidate in stateStore.activeStates.filter((item) => item.id !== state.id)"
                :key="candidate.id"
                class="flex min-w-0 max-w-full items-center gap-2 text-xs text-text-default"
              >
                <input
                  v-model="editDraft(state).incompatibility_ids"
                  type="checkbox"
                  :value="candidate.id"
                  class="rounded border-input-border text-text-brand focus:ring-focus-ring/30"
                />
                <span class="min-w-0 max-w-full [overflow-wrap:anywhere]">{{ candidate.name }}</span>
              </label>
            </div>
          </details>
        </article>
      </div>
    </section>
  </main>
</template>
