<template>
  <BaseFormField :label="label" :hint="hint">
    <div ref="wrapperRef" class="relative">
      <div class="relative">
        <span
          class="absolute inset-y-0 left-0 flex items-center pl-3 text-text-subtle pointer-events-none"
        >
          <MagnifyingGlassIcon class="w-4 h-4" />
        </span>
        <input
          ref="inputRef"
          v-model="inputText"
          type="text"
          :placeholder="placeholder"
          :disabled="!clientProfileId"
          :data-testid="testid"
          autocomplete="off"
          class="w-full pl-9 pr-9 py-2.5 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none disabled:opacity-60 disabled:cursor-not-allowed"
          role="combobox"
          :aria-expanded="isOpen"
          aria-autocomplete="list"
          aria-haspopup="listbox"
          @input="onInput"
          @focus="openDropdown"
          @keydown.down.prevent="onArrowDown"
          @keydown.up.prevent="onArrowUp"
          @keydown.enter.prevent="onEnter"
          @keydown.esc.prevent="closeDropdown"
        >
        <button
          v-if="modelValue || inputText"
          type="button"
          class="absolute inset-y-0 right-0 flex items-center pr-3 text-text-subtle hover:text-text-default transition-colors"
          aria-label="Quitar proyecto"
          :data-testid="`${testid}-clear`"
          @click="clearSelection"
        >
          <XMarkIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- Dropdown -->
      <div
        v-if="isOpen && clientProfileId"
        class="absolute z-30 mt-1 w-full bg-surface border border-border-default rounded-xl shadow-lg max-h-72 overflow-auto"
        role="listbox"
      >
        <div v-if="loading" class="px-4 py-3 text-sm text-text-subtle text-center">
          Cargando proyectos...
        </div>

        <!-- Inline creation: the module's minimum without leaving this form -->
        <div
          v-else-if="inlineOpen"
          class="p-3 space-y-2"
          :data-testid="`${testid}-inline-create`"
        >
          <p class="text-sm font-medium text-text-default">Crear proyecto</p>
          <BaseInput
            v-model="inlineName"
            :data-testid="`${testid}-inline-name`"
            placeholder="Nombre del proyecto"
          />
          <p class="text-xs text-text-subtle">
            Para <span class="font-medium text-text-default">{{ clientLabel || 'el cliente elegido' }}</span>.
            Los demás datos se completan en /panel/projects.
          </p>
          <p
            v-if="inlineDuplicate"
            class="text-xs text-text-muted rounded-lg border border-border-default bg-surface-raised px-2.5 py-1.5"
            :data-testid="`${testid}-duplicate-warning`"
          >
            Este cliente ya tiene un proyecto llamado
            <span class="font-medium text-text-default">{{ inlineDuplicate.name }}</span>.
            Puedes crearlo igual si es otro.
          </p>
          <p
            v-if="inlineError"
            class="text-xs text-danger-strong"
            :data-testid="`${testid}-inline-create-error`"
          >
            {{ inlineError }}
          </p>
          <div class="flex justify-end gap-2 pt-1">
            <BaseButton type="button" variant="secondary" size="sm" @click="inlineOpen = false">
              Cancelar
            </BaseButton>
            <BaseButton
              type="button"
              variant="primary"
              size="sm"
              :disabled="creating || !inlineName.trim()"
              :data-testid="`${testid}-inline-create-save`"
              @click="createInlineProject"
            >
              {{ creating ? 'Creando...' : 'Crear proyecto' }}
            </BaseButton>
          </div>
        </div>

        <!-- Options (local filtering: the client's projects are already here) -->
        <ul v-else-if="filteredProjects.length > 0" class="divide-y divide-border-muted">
          <li
            v-for="(project, idx) in filteredProjects"
            :key="project.id"
            :data-testid="`${testid}-option-${project.id}`"
            :class="[
              'px-4 py-2.5 cursor-pointer transition-colors text-sm',
              highlightIndex === idx ? 'bg-primary-soft' : 'hover:bg-surface-raised',
            ]"
            role="option"
            :aria-selected="highlightIndex === idx"
            @click="selectProject(project)"
            @mouseenter="highlightIndex = idx"
          >
            <span class="text-text-default">{{ project.name }}</span>
            <span v-if="project.status !== 'active'" class="text-xs text-text-subtle">
              · {{ project.status_label }}
            </span>
          </li>
        </ul>

        <!-- No matches — offer to create with the typed term (R2) -->
        <div v-else class="px-4 py-3 text-sm text-text-muted">
          <p v-if="term" class="mb-2">Sin proyectos que coincidan con "{{ term }}".</p>
          <p v-else class="mb-2">Este cliente no tiene proyectos.</p>
          <!-- design-tokens: allow-raw-button -->
          <button
            v-if="allowCreate"
            type="button"
            class="w-full text-left px-3 py-2 rounded-lg bg-primary-soft text-text-brand hover:opacity-90 transition-colors font-medium text-xs flex items-center gap-2"
            :data-testid="`${testid}-create-new`"
            @click="openInlineCreate"
          >
            <PlusIcon class="w-4 h-4" />
            <span>{{ term ? `Crear proyecto "${term}"` : 'Crear un proyecto nuevo' }}</span>
          </button>
        </div>
      </div>
    </div>
  </BaseFormField>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { onClickOutside } from '@vueuse/core';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline';
import { useAccountingStore } from '~/stores/accounting';
import { normalizeName } from '~/utils/clientMatch';

/**
 * Project picker scoped to one client, with on-the-fly creation.
 *
 * A combobox over the client's ALREADY-FETCHED projects (a handful, so the
 * filtering is local — no server search), mirroring ClientAutocomplete so
 * both selectors are learned once. When nothing matches, the dropdown
 * offers creating the project with the typed term as name; the new project
 * is selected on save and persists even if the outer form is cancelled —
 * it is a record of its own, not a draft of this form.
 *
 * Disabled until a client is chosen: the ownership rule the backend
 * enforces (the project must belong to the record's client) cannot even be
 * evaluated without one, and it means the inline create always has its
 * client inherited.
 */
const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  /** UserProfile pk of the selected client, or null. */
  clientProfileId: { type: [Number, String], default: null },
  /** Display name of that client, shown inside the inline create panel. */
  clientLabel: { type: String, default: '' },
  label: { type: String, default: 'Proyecto' },
  testid: { type: String, default: 'project-select' },
  /** Turn off the create affordance where only picking makes sense. */
  allowCreate: { type: Boolean, default: true },
});

const emit = defineEmits(['update:modelValue', 'created']);

const store = useAccountingStore();

const wrapperRef = ref(null);
const inputRef = ref(null);
const projects = ref([]);
const loading = ref(false);
const isOpen = ref(false);
const inputText = ref('');
const highlightIndex = ref(-1);

const inlineOpen = ref(false);
const inlineName = ref('');
const inlineError = ref('');
const creating = ref(false);

const term = computed(() => inputText.value.trim());

const placeholder = computed(() => {
  if (!props.clientProfileId) return 'Elige un cliente primero';
  return 'Buscar o crear un proyecto...';
});

const hint = computed(() => {
  if (!props.clientProfileId) return '';
  // Item 3 of the original requirement: an empty project is a legitimate
  // state, not pending work — a cobro por diagnóstico happens before there
  // is one. Creation lives here AND in /panel/projects.
  return 'Opcional. Si no existe, créalo aquí mismo sin salir del formulario.';
});

/** The committed selection, resolved against the loaded list. */
const selectedProject = computed(() => {
  if (props.modelValue == null) return null;
  return projects.value.find((p) => p.id === Number(props.modelValue)) || null;
});

const filteredProjects = computed(() => {
  const needle = normalizeName(term.value);
  if (!needle) return projects.value;
  return projects.value.filter((p) => normalizeName(p.name).includes(needle));
});

const inlineDuplicate = computed(() => {
  const needle = normalizeName(inlineName.value);
  if (!needle) return null;
  return projects.value.find((p) => normalizeName(p.name) === needle) || null;
});

async function load() {
  if (!props.clientProfileId) {
    projects.value = [];
    return;
  }
  loading.value = true;
  const result = await store.fetchProjectsForClient(props.clientProfileId);
  projects.value = result.success ? result.data : [];
  loading.value = false;
}

function syncInputToSelection() {
  if (selectedProject.value) inputText.value = selectedProject.value.name;
  else if (props.modelValue == null && !isOpen.value) inputText.value = '';
}

watch(
  () => props.clientProfileId,
  (next, previous) => {
    load();
    // The previous project belonged to the previous client; keeping it would
    // send the backend a pair it is going to reject anyway.
    if (previous !== undefined && next !== previous && props.modelValue) {
      emit('update:modelValue', null);
      inputText.value = '';
    }
  },
  { immediate: true },
);

watch([selectedProject, () => props.modelValue], syncInputToSelection, { immediate: true });

function openDropdown() {
  if (!props.clientProfileId) return;
  isOpen.value = true;
}

function closeDropdown() {
  isOpen.value = false;
  inlineOpen.value = false;
  inlineError.value = '';
  highlightIndex.value = -1;
  syncInputToSelection();
}

function onInput() {
  isOpen.value = true;
  inlineOpen.value = false;
  // Typing clears any committed selection so the parent knows to re-pick.
  if (props.modelValue !== null) emit('update:modelValue', null);
  highlightIndex.value = filteredProjects.value.length > 0 ? 0 : -1;
}

function selectProject(project) {
  emit('update:modelValue', Number(project.id));
  inputText.value = project.name;
  isOpen.value = false;
  inlineOpen.value = false;
  highlightIndex.value = -1;
}

function clearSelection() {
  emit('update:modelValue', null);
  inputText.value = '';
  inlineOpen.value = false;
  inputRef.value?.focus();
}

function onArrowDown() {
  if (!isOpen.value) {
    openDropdown();
    return;
  }
  if (filteredProjects.value.length === 0) return;
  highlightIndex.value = (highlightIndex.value + 1) % filteredProjects.value.length;
}

function onArrowUp() {
  if (!isOpen.value || filteredProjects.value.length === 0) return;
  highlightIndex.value = (highlightIndex.value - 1 + filteredProjects.value.length)
    % filteredProjects.value.length;
}

function onEnter() {
  if (!isOpen.value) return;
  if (inlineOpen.value) return;
  if (highlightIndex.value >= 0 && filteredProjects.value[highlightIndex.value]) {
    selectProject(filteredProjects.value[highlightIndex.value]);
  } else if (props.allowCreate && filteredProjects.value.length === 0) {
    openInlineCreate();
  }
}

function openInlineCreate() {
  inlineOpen.value = true;
  inlineName.value = term.value;
  inlineError.value = '';
}

async function createInlineProject() {
  creating.value = true;
  inlineError.value = '';
  const result = await store.createProjectForClient(props.clientProfileId, {
    name: inlineName.value.trim(),
  });
  creating.value = false;
  if (!result.success) {
    // The panel stays open: the operator fixes the name and retries.
    inlineError.value = result.message || 'No se pudo crear el proyecto.';
    return;
  }
  // The store already updated its per-client cache; reread it so the new
  // project is pickable immediately, then commit the selection (R2-4).
  await load();
  emit('created', result.data);
  selectProject(result.data);
}

onClickOutside(wrapperRef, closeDropdown);
</script>
