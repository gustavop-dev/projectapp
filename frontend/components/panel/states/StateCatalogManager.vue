<script setup>
import {
  computed, onMounted, reactive, ref,
} from 'vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { DOCUMENT_STATE_COLORS, stateBadgeVariant } from '~/utils/documentState';
import ProjectStateHelpBadge from '~/components/panel/projects/ProjectStateHelpBadge.vue';

const props = defineProps({
  stateStore: { type: Object, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  backTo: { type: String, required: true },
  backLabel: { type: String, required: true },
  testId: { type: String, default: 'state-catalog' },
  activeCountField: { type: String, required: true },
  activeCountLabel: { type: String, required: true },
  manageGroups: { type: Boolean, default: true },
  operationalEffects: { type: Array, default: () => [] },
});

const notify = usePanelNotify();
const localePath = useLocalePath();
const newState = reactive({
  name: '',
  description: '',
  color: 'gray',
  group: '',
  operational_effect: props.operationalEffects[0]?.value || '',
});
const newGroup = reactive({ name: '', selection_mode: 'additive' });
const editing = reactive({});
const groupEditing = reactive({});
const mergeTargets = reactive({});
const createValidationAttempted = ref(false);
const createApiErrors = reactive({});
const editValidationAttempted = reactive({});
const editApiErrors = reactive({});
const mergeValidationAttempted = reactive({});
const {
  confirmState,
  requestConfirm,
  handleConfirmed,
  handleCancelled,
} = useConfirmModal();

const groups = computed(() => props.stateStore.groups.map((group) => ({
  ...group,
  states: props.stateStore.states.filter((state) => state.group === group.id),
})));

const hasOperationalEffects = computed(() => props.operationalEffects.length > 0);
const createStateBlockReasons = computed(() => [
  !newState.name.trim() ? 'Escribe el nombre del estado.' : '',
  hasOperationalEffects.value && !newState.description.trim()
    ? 'Explica qué significa el estado.'
    : '',
  !newState.group ? 'Elige el grupo del estado.' : '',
].filter(Boolean));
const createGroupBlockReasons = computed(() => [
  !newGroup.name.trim() ? 'Escribe el nombre del grupo.' : '',
].filter(Boolean));

const projectStateFieldNames = new Set([
  'name',
  'description',
  'group',
  'operational_effect',
]);
const editableProjectStateFieldNames = new Set(['name', 'description']);

function clearErrors(target) {
  Object.keys(target).forEach((field) => delete target[field]);
}

function captureProjectFieldErrors(
  target,
  fieldErrors,
  allowedFields = projectStateFieldNames,
) {
  clearErrors(target);
  if (!fieldErrors || typeof fieldErrors !== 'object') return false;
  let captured = false;
  Object.entries(fieldErrors).forEach(([field, message]) => {
    if (!allowedFields.has(field) || !message) return;
    target[field] = String(message);
    captured = true;
  });
  return captured;
}

function createFieldError(field) {
  if (createApiErrors[field]) return createApiErrors[field];
  if (!createValidationAttempted.value) return '';
  if (field === 'name' && !newState.name.trim()) {
    return 'Escribe el nombre del estado.';
  }
  if (field === 'description' && !newState.description.trim()) {
    return 'Explica qué significa el estado.';
  }
  if (field === 'group' && !newState.group) {
    return 'Elige el grupo del estado.';
  }
  if (field === 'operational_effect' && !newState.operational_effect) {
    return 'Elige el efecto operativo del estado.';
  }
  return '';
}

function clearCreateFieldError(field) {
  delete createApiErrors[field];
}

function editFieldError(state, field) {
  if (editApiErrors[state.id]?.[field]) return editApiErrors[state.id][field];
  if (!editValidationAttempted[state.id]) return '';
  const draft = editDraft(state);
  if (field === 'name' && !draft.name.trim()) {
    return 'Escribe el nombre del estado.';
  }
  if (field === 'description' && !draft.description.trim()) {
    return 'Explica qué significa el estado.';
  }
  return '';
}

function clearEditFieldError(stateId, field) {
  if (!editApiErrors[stateId]) return;
  delete editApiErrors[stateId][field];
}

function mergeFieldError(state) {
  if (
    !hasOperationalEffects.value
    || state.system_key
    || !mergeValidationAttempted[state.id]
    || mergeTargets[state.id]
  ) return '';
  return 'Elige el estado de destino.';
}

onMounted(async () => {
  await props.stateStore.fetchCatalog({ includeRetired: true });
  if (!newState.group && props.stateStore.groups.length) {
    newState.group = props.stateStore.groups.find(
      (group) => group.selection_mode === 'additive',
    )?.id || props.stateStore.groups[0].id;
  }
});

async function createState(confirmSimilar = false) {
  if (hasOperationalEffects.value) {
    createValidationAttempted.value = true;
    if ([
      'name',
      'description',
      'group',
      'operational_effect',
    ].some((field) => createFieldError(field))) return;
  }
  const name = newState.name.trim();
  if (!name) return;
  const payload = {
    ...newState,
    name,
    confirm_similar: confirmSimilar,
  };
  if (!hasOperationalEffects.value) {
    delete payload.operational_effect;
  }
  const result = await props.stateStore.createState(payload);
  if (result.needsConfirmation) {
    const names = result.suggestions.map((item) => item.name).join(', ');
    const confirmed = await requestConfirm({
      title: 'Revisar estados parecidos',
      message: `Ya existen estados parecidos: ${names}. Crear otro puede fragmentar los filtros y el historial.`,
      confirmText: 'Crear de todas formas',
      variant: 'warning',
    });
    if (confirmed) {
      await createState(true);
    }
    return;
  }
  if (!result.success) {
    if (
      hasOperationalEffects.value
      && captureProjectFieldErrors(createApiErrors, result.fieldErrors)
    ) return;
    notify.error({ title: 'No se pudo crear', detail: result.message });
    return;
  }
  newState.name = '';
  newState.description = '';
  createValidationAttempted.value = false;
  clearErrors(createApiErrors);
  notify.success({ title: 'Estado creado' });
}

function editDraft(state) {
  if (!editing[state.id]) {
    editing[state.id] = {
      name: state.name,
      description: state.description || '',
      color: state.color,
      group: state.group,
      order: state.order,
      operational_effect: state.operational_effect || '',
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
  const result = await props.stateStore.updateGroup(group.id, groupDraft(group));
  if (result.success) {
    delete groupEditing[group.id];
    notify.success({ title: 'Grupo actualizado' });
  } else {
    notify.error({
      title: 'No se pudo actualizar el grupo',
      detail: result.message,
    });
  }
}

async function saveState(state) {
  if (hasOperationalEffects.value) {
    editValidationAttempted[state.id] = true;
    if (['name', 'description'].some((field) => editFieldError(state, field))) return;
  }
  const payload = { ...editDraft(state) };
  if (!hasOperationalEffects.value) {
    delete payload.operational_effect;
  }
  const result = await props.stateStore.updateState(state.id, payload);
  if (result.success) {
    delete editing[state.id];
    delete editValidationAttempted[state.id];
    delete editApiErrors[state.id];
    notify.success({ title: 'Estado actualizado' });
  } else {
    if (hasOperationalEffects.value) {
      const errors = {};
      if (captureProjectFieldErrors(
        errors,
        result.fieldErrors,
        editableProjectStateFieldNames,
      )) {
        editApiErrors[state.id] = errors;
        return;
      }
    }
    notify.error({ title: 'No se pudo actualizar', detail: result.message });
  }
}

function saveStateBlockReasons(state) {
  const draft = editDraft(state);
  return [
    !draft.name.trim() ? 'Escribe el nombre del estado.' : '',
    hasOperationalEffects.value && !draft.description.trim()
      ? 'Explica qué significa el estado.'
      : '',
  ].filter(Boolean);
}

async function retire(state) {
  const confirmed = await requestConfirm({
    title: 'Retirar estado',
    message: `“${state.name}” dejará de aparecer en el selector. Su historial se conservará.`,
    confirmText: 'Retirar estado',
    variant: 'warning',
  });
  if (!confirmed) return;
  const result = await props.stateStore.retireState(state.id);
  if (result.success) notify.success({ title: 'Estado retirado' });
  else notify.error({ title: 'No se puede retirar', detail: result.message });
}

async function merge(state) {
  if (hasOperationalEffects.value) {
    mergeValidationAttempted[state.id] = true;
  }
  const target = mergeTargets[state.id];
  if (!target) return;
  const targetState = props.stateStore.states.find(
    (item) => item.id === Number(target),
  );
  const confirmed = await requestConfirm({
    title: 'Fusionar estados',
    message: `“${state.name}” se fusionará con “${targetState?.name || 'el estado elegido'}”. Los episodios históricos se conservarán.`,
    confirmText: 'Fusionar estados',
    variant: 'warning',
  });
  if (!confirmed) return;
  const result = await props.stateStore.mergeState(state.id, target);
  if (result.success) {
    delete mergeValidationAttempted[state.id];
    notify.success({ title: 'Estados fusionados' });
  } else {
    notify.error({
      title: 'No se pudieron fusionar',
      detail: result.message,
    });
  }
}

function mergeBlockReasons(state) {
  if (hasOperationalEffects.value) {
    return [
      state.system_key ? 'Los estados semilla del sistema no se pueden fusionar.' : '',
    ].filter(Boolean);
  }
  return [
    !mergeTargets[state.id] ? 'Elige el estado de destino.' : '',
    state.system_key ? 'Los estados semilla del sistema no se pueden fusionar.' : '',
  ].filter(Boolean);
}

async function createGroup() {
  const name = newGroup.name.trim();
  if (!name) return;
  const result = await props.stateStore.createGroup({
    ...newGroup,
    name,
    order: props.stateStore.groups.length,
  });
  if (result.success) {
    newGroup.name = '';
    notify.success({ title: 'Grupo creado' });
  } else {
    notify.error({ title: 'No se pudo crear el grupo', detail: result.message });
  }
}

function activeCount(state) {
  return state[props.activeCountField] ?? 0;
}
</script>

<template>
  <main class="mx-auto w-full max-w-6xl space-y-6" :data-testid="testId">
    <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <NuxtLink :to="localePath(backTo)" class="inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-default">
          <BaseActionIcon action="back" />
          {{ backLabel }}
        </NuxtLink>
        <h1 class="mt-2 text-2xl font-light text-text-default">{{ title }}</h1>
        <p class="mt-1 max-w-2xl text-sm text-text-muted">{{ description }}</p>
      </div>
    </header>

    <section class="grid gap-4 rounded-xl border border-border-default bg-surface p-5" :class="manageGroups ? 'lg:grid-cols-2' : ''">
      <form class="space-y-3" @submit.prevent="createState()">
        <h2 class="text-sm font-semibold text-text-default">Crear estado</h2>
        <div class="grid gap-2" :class="hasOperationalEffects ? 'sm:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_auto_auto_auto]' : 'sm:grid-cols-[minmax(0,1fr)_auto_auto]'">
          <template v-if="hasOperationalEffects">
            <BaseFormField
              v-slot="{ invalid, errorId }"
              label="Nombre del estado"
              required
              :error="createFieldError('name')"
            >
              <BaseInput
                v-model="newState.name"
                placeholder="Nombre"
                aria-label="Nombre del nuevo estado"
                data-testid="catalog-new-state-name"
                :error="invalid"
                :aria-describedby="errorId"
                @update:model-value="clearCreateFieldError('name')"
              />
            </BaseFormField>
            <BaseFormField
              v-slot="{ errorId }"
              label="Grupo"
              :error="createFieldError('group')"
            >
              <select
                v-model="newState.group"
                aria-label="Grupo del nuevo estado"
                :aria-describedby="errorId"
                class="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm"
                @change="clearCreateFieldError('group')"
              >
                <option v-for="group in stateStore.groups.filter((item) => item.is_active)" :key="group.id" :value="group.id">{{ group.name }}</option>
              </select>
            </BaseFormField>
            <BaseFormField
              v-slot="{ errorId }"
              label="Efecto operativo"
              required
              :error="createFieldError('operational_effect')"
            >
              <select
                v-model="newState.operational_effect"
                aria-label="Efecto operativo del nuevo estado"
                :aria-describedby="errorId"
                class="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm"
                @change="clearCreateFieldError('operational_effect')"
              >
                <option v-for="effect in operationalEffects" :key="effect.value" :value="effect.value">{{ effect.label }}</option>
              </select>
            </BaseFormField>
            <BaseFormField label="Color">
              <select v-model="newState.color" aria-label="Color del nuevo estado" class="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm">
                <option v-for="color in DOCUMENT_STATE_COLORS" :key="color.value" :value="color.value">{{ color.label }}</option>
              </select>
            </BaseFormField>
          </template>
          <template v-else>
            <BaseInput v-model="newState.name" placeholder="Nombre" data-testid="catalog-new-state-name" />
            <select v-model="newState.group" aria-label="Grupo del nuevo estado" class="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm">
              <option v-for="group in stateStore.groups.filter((item) => item.is_active)" :key="group.id" :value="group.id">{{ group.name }}</option>
            </select>
            <select v-model="newState.color" aria-label="Color del nuevo estado" class="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm">
              <option v-for="color in DOCUMENT_STATE_COLORS" :key="color.value" :value="color.value">{{ color.label }}</option>
            </select>
          </template>
        </div>
        <BaseFormField
          v-if="hasOperationalEffects"
          v-slot="{ invalid, errorId }"
          label="Descripción"
          required
          :error="createFieldError('description')"
        >
          <BaseTextarea
            v-model="newState.description"
            :rows="2"
            maxlength="300"
            placeholder="Qué significa este estado para quien lo elige"
            aria-label="Descripción del nuevo estado"
            data-testid="catalog-new-state-description"
            :error="invalid"
            :aria-describedby="errorId"
            @update:model-value="clearCreateFieldError('description')"
          />
        </BaseFormField>
        <p v-if="hasOperationalEffects" class="text-xs text-text-subtle">
          El nombre se puede cambiar; el efecto define cobros, avisos y cierre.
        </p>
        <BaseButton
          v-if="hasOperationalEffects"
          type="submit"
          variant="primary"
          size="sm"
          data-testid="catalog-create-state"
        >
          Crear estado
        </BaseButton>
        <BaseControlGate
          v-else
          :reasons="createStateBlockReasons"
          label="Crear estado no disponible"
          align="start"
        >
          <template #default="{ describedBy }">
            <BaseButton
              type="submit"
              variant="primary"
              size="sm"
              data-testid="catalog-create-state"
              :disabled="Boolean(createStateBlockReasons.length)"
              :disabled-reason="createStateBlockReasons.join(' ')"
              :aria-describedby="describedBy"
            >
              Crear estado
            </BaseButton>
          </template>
        </BaseControlGate>
      </form>
      <form v-if="manageGroups" class="space-y-3 border-t border-border-muted pt-4 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0" @submit.prevent="createGroup">
        <h2 class="text-sm font-semibold text-text-default">Crear grupo</h2>
        <div class="flex gap-2">
          <BaseInput v-model="newGroup.name" placeholder="Nombre del grupo" />
          <select v-model="newGroup.selection_mode" aria-label="Modo del nuevo grupo" class="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm">
            <option value="exclusive">Uno activo</option>
            <option value="additive">Varios activos</option>
          </select>
        </div>
        <BaseControlGate
          :reasons="createGroupBlockReasons"
          label="Crear grupo no disponible"
          align="start"
        >
          <template #default="{ describedBy }">
            <BaseButton
              type="submit"
              variant="secondary"
              size="sm"
              data-testid="catalog-create-group"
              :disabled="Boolean(createGroupBlockReasons.length)"
              :disabled-reason="createGroupBlockReasons.join(' ')"
              :aria-describedby="describedBy"
            >
              Crear grupo
            </BaseButton>
          </template>
        </BaseControlGate>
      </form>
    </section>

    <section v-for="group in groups" :key="group.id" class="rounded-xl border border-border-default bg-surface" :data-testid="`catalog-group-${group.id}`">
      <div class="flex flex-col gap-3 border-b border-border-muted px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div v-if="manageGroups" class="grid flex-1 gap-2 sm:grid-cols-[minmax(0,1fr)_10rem_6rem_auto]">
          <BaseInput v-model="groupDraft(group).name" aria-label="Nombre del grupo" />
          <select v-model="groupDraft(group).selection_mode" class="rounded-lg border border-input-border bg-input-bg px-2 py-2 text-sm">
            <option value="exclusive">Uno activo</option>
            <option value="additive">Varios activos</option>
          </select>
          <BaseInput v-model.number="groupDraft(group).order" type="number" min="0" aria-label="Orden del grupo" />
          <BaseButton variant="secondary" size="sm" :data-testid="`catalog-save-group-${group.id}`" @click="saveGroup(group)">Guardar grupo</BaseButton>
        </div>
        <h2 v-else class="font-medium text-text-default">{{ group.name }}</h2>
        <BaseBadge variant="neutral">{{ group.states.length }} estados</BaseBadge>
      </div>
      <div v-if="!group.states.length" class="p-5 text-sm text-text-muted">No hay estados en este grupo.</div>
      <div v-else class="divide-y divide-border-muted">
        <article v-for="state in group.states" :key="state.id" class="space-y-3 p-4 sm:p-5" :class="!state.is_active ? 'opacity-60' : ''" :data-testid="`catalog-state-${state.id}`">
          <div class="flex flex-wrap items-center gap-2">
            <BaseBadge :variant="stateBadgeVariant(state)">{{ state.name }}</BaseBadge>
            <ProjectStateHelpBadge
              v-if="hasOperationalEffects"
              :state="state"
              position="bottom"
              :test-id="`catalog-state-help-${state.id}`"
            />
            <BaseBadge v-if="state.system_key" variant="info" size="sm">Semilla</BaseBadge>
            <BaseBadge v-if="!state.is_active" variant="neutral" size="sm">Retirado</BaseBadge>
            <span class="text-xs text-text-muted">{{ activeCount(state) }} {{ activeCountLabel }} activos · {{ state.historical_episode_count }} episodios</span>
          </div>
          <div v-if="state.is_active" class="space-y-2">
            <template v-if="hasOperationalEffects">
              <div class="grid gap-2 lg:grid-cols-[minmax(0,1fr)_8rem_11rem_6rem_auto]">
                <BaseFormField
                  v-slot="{ invalid, errorId }"
                  label="Nombre del estado"
                  required
                  :error="editFieldError(state, 'name')"
                >
                  <BaseInput
                    v-model="editDraft(state).name"
                    aria-label="Nombre del estado"
                    :error="invalid"
                    :aria-describedby="errorId"
                    @update:model-value="clearEditFieldError(state.id, 'name')"
                  />
                </BaseFormField>
                <BaseFormField label="Color">
                  <select v-model="editDraft(state).color" aria-label="Color del estado" class="rounded-lg border border-input-border bg-input-bg px-2 py-2 text-sm">
                    <option v-for="color in DOCUMENT_STATE_COLORS" :key="color.value" :value="color.value">{{ color.label }}</option>
                  </select>
                </BaseFormField>
                <BaseFormField
                  v-slot="{ errorId }"
                  label="Efecto operativo"
                  required
                  :error="editFieldError(state, 'operational_effect')"
                >
                  <select
                    v-model="editDraft(state).operational_effect"
                    aria-label="Efecto operativo del estado"
                    :aria-describedby="errorId"
                    class="rounded-lg border border-input-border bg-input-bg px-2 py-2 text-sm"
                    disabled
                    title="El efecto operativo es inmutable"
                  >
                    <option v-for="effect in operationalEffects" :key="effect.value" :value="effect.value">{{ effect.label }}</option>
                  </select>
                </BaseFormField>
                <BaseFormField label="Orden">
                  <BaseInput v-model.number="editDraft(state).order" type="number" min="0" aria-label="Orden" />
                </BaseFormField>
                <BaseButton
                  class="self-end"
                  variant="secondary"
                  size="sm"
                  :data-testid="`catalog-save-state-${state.id}`"
                  @click="saveState(state)"
                >
                  Guardar
                </BaseButton>
              </div>
              <BaseFormField
                v-slot="{ invalid, errorId }"
                label="Descripción"
                required
                :error="editFieldError(state, 'description')"
              >
                <BaseTextarea
                  v-model="editDraft(state).description"
                  :rows="2"
                  maxlength="300"
                  :aria-label="`Descripción de ${state.name}`"
                  :data-testid="`catalog-state-description-${state.id}`"
                  :error="invalid"
                  :aria-describedby="errorId"
                  @update:model-value="clearEditFieldError(state.id, 'description')"
                />
              </BaseFormField>
            </template>
            <template v-else>
              <div class="grid gap-2 lg:grid-cols-[minmax(0,1fr)_8rem_10rem_6rem_auto]">
                <BaseInput v-model="editDraft(state).name" aria-label="Nombre del estado" />
                <select v-model="editDraft(state).color" aria-label="Color del estado" class="rounded-lg border border-input-border bg-input-bg px-2 py-2 text-sm">
                  <option v-for="color in DOCUMENT_STATE_COLORS" :key="color.value" :value="color.value">{{ color.label }}</option>
                </select>
                <select v-model="editDraft(state).group" aria-label="Grupo del estado" class="rounded-lg border border-input-border bg-input-bg px-2 py-2 text-sm">
                  <option v-for="item in stateStore.groups" :key="item.id" :value="item.id">{{ item.name }}</option>
                </select>
                <BaseInput v-model.number="editDraft(state).order" type="number" min="0" aria-label="Orden" />
                <BaseControlGate
                  :reasons="saveStateBlockReasons(state)"
                  label="Guardar estado no disponible"
                  align="end"
                >
                  <template #default="{ describedBy }">
                    <BaseButton
                      variant="secondary"
                      size="sm"
                      :data-testid="`catalog-save-state-${state.id}`"
                      :disabled="Boolean(saveStateBlockReasons(state).length)"
                      :disabled-reason="saveStateBlockReasons(state).join(' ')"
                      :aria-describedby="describedBy"
                      @click="saveState(state)"
                    >
                      Guardar
                    </BaseButton>
                  </template>
                </BaseControlGate>
              </div>
            </template>
          </div>
          <div v-if="state.is_active" class="flex flex-wrap items-center gap-2">
            <BaseFormField
              v-if="hasOperationalEffects"
              v-slot="{ errorId }"
              size="sm"
              :error="mergeFieldError(state)"
            >
              <select v-model="mergeTargets[state.id]" :aria-label="`Destino para fusionar ${state.name}`" :aria-describedby="errorId" class="rounded-lg border border-input-border bg-input-bg px-2 py-1.5 text-xs">
                <option value="">Fusionar con…</option>
                <option v-for="target in stateStore.activeStates.filter((item) => item.id !== state.id && item.group === state.group && item.operational_effect === state.operational_effect)" :key="target.id" :value="target.id">{{ target.name }}</option>
              </select>
            </BaseFormField>
            <select v-else v-model="mergeTargets[state.id]" :aria-label="`Destino para fusionar ${state.name}`" class="rounded-lg border border-input-border bg-input-bg px-2 py-1.5 text-xs">
              <option value="">Fusionar con…</option>
              <option v-for="target in stateStore.activeStates.filter((item) => item.id !== state.id && item.group === state.group)" :key="target.id" :value="target.id">{{ target.name }}</option>
            </select>
            <BaseControlGate
              :reasons="mergeBlockReasons(state)"
              label="Fusionar no disponible"
              align="start"
              :visible="!hasOperationalEffects"
            >
              <template #default="{ describedBy }">
                <BaseButton
                  variant="ghost"
                  size="sm"
                  :data-testid="`catalog-merge-state-${state.id}`"
                  :disabled="Boolean(mergeBlockReasons(state).length)"
                  :disabled-reason="mergeBlockReasons(state).join(' ')"
                  :aria-describedby="describedBy"
                  @click="merge(state)"
                >
                  Fusionar
                </BaseButton>
              </template>
            </BaseControlGate>
            <BaseButton variant="danger-ghost" size="sm" :data-testid="`catalog-retire-state-${state.id}`" @click="retire(state)">Retirar</BaseButton>
          </div>
          <details v-if="state.is_active && !hasOperationalEffects" class="rounded-lg border border-border-muted bg-surface-raised px-3 py-2">
            <summary class="cursor-pointer text-xs font-medium text-text-muted">Combinaciones excluidas</summary>
            <div class="mt-2 flex flex-wrap gap-3">
              <label v-for="candidate in stateStore.activeStates.filter((item) => item.id !== state.id)" :key="candidate.id" class="flex min-w-0 max-w-full items-center gap-2 text-xs text-text-default">
                <input v-model="editDraft(state).incompatibility_ids" type="checkbox" :value="candidate.id" class="rounded border-input-border text-text-brand focus:ring-focus-ring/30" />
                <span class="min-w-0 max-w-full [overflow-wrap:anywhere]">{{ candidate.name }}</span>
              </label>
            </div>
          </details>
        </article>
      </div>
    </section>
  </main>
  <ConfirmModal
    v-model="confirmState.open"
    :title="confirmState.title"
    :message="confirmState.message"
    :confirm-text="confirmState.confirmText"
    :cancel-text="confirmState.cancelText"
    :variant="confirmState.variant"
    @confirm="handleConfirmed"
    @cancel="handleCancelled"
  />
</template>
