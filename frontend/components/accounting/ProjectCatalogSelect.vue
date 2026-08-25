<template>
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
        :data-testid="testId"
        autocomplete="off"
        class="w-full pl-9 pr-9 py-2.5 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
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
        title="Quitar proyecto"
        :data-testid="`${testId}-clear`"
        @click="clearSelection"
      >
        <BaseActionIcon action="clear" />
      </button>
    </div>

    <div
      v-if="isOpen"
      class="absolute z-30 mt-1 w-full bg-surface border border-border-default rounded-xl shadow-lg max-h-72 overflow-auto"
      role="listbox"
    >
      <div v-if="store.isLoading" class="px-4 py-3 text-sm text-text-subtle text-center">
        Cargando proyectos...
      </div>

      <ul v-else-if="filteredProjects.length > 0" class="divide-y divide-border-muted">
        <li
          v-for="(project, idx) in filteredProjects"
          :key="project.id"
          :data-testid="`${testId}-option-${project.id}`"
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
          <span v-if="project.client?.name" class="text-xs text-text-subtle">
            · {{ project.client.name }}
          </span>
          <span v-if="project.status !== 'active'" class="text-xs text-text-subtle">
            · {{ project.status_label }}
          </span>
        </li>
      </ul>

      <div v-else class="px-4 py-3 text-sm text-text-muted">
        {{ term ? `Sin proyectos que coincidan con "${term}".` : 'No hay proyectos registrados.' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline';
import { usePanelProjectsStore } from '~/stores/panel_projects';
import { normalizeName } from '~/utils/clientMatch';

/**
 * Catalog-wide project combobox for the bulk bar: unlike `ProjectSelect`
 * (scoped to ONE client, with inline creation) this one searches every
 * project by name or client, offers no creation, and emits the FULL catalog
 * row — the assignment plan needs `client.profile_id` to name the rows the
 * action must not touch. Active projects list first; a selection of mixed
 * clients is legal here, so ownership is the plan's problem, not the
 * picker's.
 */
const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  testId: { type: String, default: 'project-catalog-select' },
  placeholder: { type: String, default: 'Buscar el proyecto a asignar...' },
});

const emit = defineEmits(['update:modelValue', 'select']);

const store = usePanelProjectsStore();

const wrapperRef = ref(null);
const inputRef = ref(null);
const isOpen = ref(false);
const inputText = ref('');
const highlightIndex = ref(-1);

const term = computed(() => inputText.value.trim());

const catalog = computed(() => {
  const records = store.records ?? [];
  // Actives first, alphabetical inside each group: archived projects stay
  // reachable (historical rows point at them) but never on top.
  return [...records].sort((a, b) => {
    const activeDelta = (a.status === 'active' ? 0 : 1) - (b.status === 'active' ? 0 : 1);
    return activeDelta !== 0 ? activeDelta : a.name.localeCompare(b.name);
  });
});

const selectedProject = computed(() => {
  if (props.modelValue == null) return null;
  return catalog.value.find((p) => p.id === Number(props.modelValue)) || null;
});

const filteredProjects = computed(() => {
  const needle = normalizeName(term.value);
  if (!needle) return catalog.value;
  return catalog.value.filter((p) =>
    normalizeName(p.name).includes(needle)
    || normalizeName(p.client?.name || '').includes(needle));
});

function syncInputToSelection() {
  if (selectedProject.value) inputText.value = selectedProject.value.name;
  else if (props.modelValue == null && !isOpen.value) inputText.value = '';
}

watch([selectedProject, () => props.modelValue], syncInputToSelection, { immediate: true });

function openDropdown() {
  isOpen.value = true;
  if (!store.records.length && !store.isLoading) store.fetchProjects();
}

function closeDropdown() {
  isOpen.value = false;
  highlightIndex.value = -1;
  syncInputToSelection();
}

function onInput() {
  isOpen.value = true;
  if (props.modelValue !== null) {
    emit('update:modelValue', null);
    emit('select', null);
  }
  highlightIndex.value = filteredProjects.value.length > 0 ? 0 : -1;
}

function selectProject(project) {
  emit('update:modelValue', Number(project.id));
  emit('select', project);
  inputText.value = project.name;
  isOpen.value = false;
  highlightIndex.value = -1;
}

function clearSelection() {
  emit('update:modelValue', null);
  emit('select', null);
  inputText.value = '';
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
  if (highlightIndex.value >= 0 && filteredProjects.value[highlightIndex.value]) {
    selectProject(filteredProjects.value[highlightIndex.value]);
  }
}

onClickOutside(wrapperRef, closeDropdown);
</script>
