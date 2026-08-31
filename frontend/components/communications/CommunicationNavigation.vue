<template>
  <aside class="flex h-full min-h-0 flex-col rounded-xl border border-border-muted bg-surface shadow-card">
    <div class="shrink-0 border-b border-border-muted px-4 py-3">
      <h2 class="text-xs font-semibold uppercase tracking-wider text-text-muted">Navegar por</h2>
      <EntityNavigationModeSwitch
        class="mt-3"
        :model-value="mode"
        aria-label="Agrupar comunicaciones"
        test-id-prefix="communications-mode"
        @update:model-value="$emit('update:mode', $event)"
      />
    </div>

    <div class="shrink-0 border-b border-border-muted p-3">
      <BaseInput
        v-model="search"
        size="sm"
        :placeholder="mode === 'project' ? 'Buscar proyecto...' : 'Buscar cliente...'"
        :aria-label="mode === 'project' ? 'Buscar proyecto' : 'Buscar cliente'"
        data-testid="communications-navigation-search"
      />
    </div>

    <div
      v-if="mode === 'project'"
      class="flex shrink-0 items-center justify-between gap-2 border-b border-border-muted px-3 py-2.5 transition-colors"
      :class="showInactiveProjects ? 'bg-warning-soft' : ''"
      data-testid="communications-inactive-projects-control"
    >
      <span class="flex min-w-0 items-center gap-2">
        <span
          class="truncate text-sm"
          :class="showInactiveProjects ? 'font-medium text-text-default' : 'text-text-muted'"
        >
          Ver proyectos no activos
        </span>
      </span>
      <BaseToggle
        :model-value="showInactiveProjects"
        size="sm"
        aria-label="Ver proyectos no activos"
        data-testid="communications-inactive-projects-toggle"
        @update:model-value="$emit('toggle-inactive-projects', $event)"
      />
    </div>

    <nav class="min-h-0 flex-1 overflow-y-auto p-2" :aria-label="navigationLabel">
      <ul class="space-y-1">
        <li role="presentation">
          <!-- design-tokens: allow-raw-button — cabecera de seccion plegable, no una accion -->
          <button
            type="button"
            class="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-muted transition-colors hover:bg-surface-muted"
            :class="touchMode ? 'min-h-11' : ''"
            :aria-expanded="sidebarSections.entities"
            :aria-controls="entitiesSectionId"
            data-testid="communications-entities-section-toggle"
            @click="toggleSidebarSection('entities')"
          >
            <span class="flex items-center gap-2">
              <BaseActionIcon :action="sidebarSections.entities ? 'collapse' : 'expand'" />
              {{ entitiesSectionLabel }}
            </span>
          </button>
          <BaseCollapse :id="entitiesSectionId" :open="sidebarSections.entities">
            <ul class="space-y-1" role="list">
        <li>
          <!-- design-tokens: allow-raw-button — selectable navigation row, not a standalone action. -->
          <button
            type="button"
            class="flex min-h-10 w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors"
            :class="entryClass('all')"
            :aria-current="isSelected('all') ? 'page' : undefined"
            data-testid="communications-navigation-all"
            @click="$emit('select', 'all')"
          >
            <span>Todos</span>
            <span class="shrink-0 text-xs tabular-nums text-text-subtle">{{ facets.navigation_total || 0 }}</span>
          </button>
        </li>

        <li v-for="entry in visibleActiveEntries" :key="entry.id">
          <!-- design-tokens: allow-raw-button — selectable navigation row, not a standalone action. -->
          <button
            type="button"
            class="flex min-h-10 w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors"
            :class="entryClass(entry.id)"
            :aria-current="isSelected(entry.id) ? 'page' : undefined"
            :data-testid="`communications-navigation-${mode}-${entry.id}`"
            @click="$emit('select', entry.id)"
          >
            <span class="min-w-0 flex-1">
              <span class="block truncate" :title="entry.name">{{ entry.name }}</span>
              <span v-if="entry.unavailable" class="block text-2xs text-warning-strong">
                No disponible; quita esta selección para continuar.
              </span>
            </span>
            <span class="shrink-0 text-xs tabular-nums text-text-subtle">{{ entry.count }}</span>
          </button>
        </li>
        <li v-if="visibleArchivedEntries.length" role="presentation">
          <details open data-testid="communications-navigation-archived-group">
            <summary class="flex cursor-pointer items-center justify-between gap-2 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-muted hover:bg-surface-muted">
              <span>{{ archivedGroupLabel }}</span>
              <span class="font-normal normal-case text-text-subtle">{{ visibleArchivedEntries.length }}</span>
            </summary>
            <ul class="mt-1 space-y-1" role="list">
              <li v-for="entry in visibleArchivedEntries" :key="entry.id">
                <!-- design-tokens: allow-raw-button — selectable navigation row, not a standalone action. -->
                <button
                  type="button"
                  class="flex min-h-10 w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors"
                  :class="entryClass(entry.id)"
                  :aria-current="isSelected(entry.id) ? 'page' : undefined"
                  :data-testid="`communications-navigation-${mode}-${entry.id}`"
                  @click="$emit('select', entry.id)"
                >
                  <span class="min-w-0 flex-1">
                    <span class="block truncate" :title="entry.name">{{ entry.name }}</span>
                    <span v-if="entry.unavailable" class="block text-2xs text-warning-strong">
                      No disponible; quita esta selección para continuar.
                    </span>
                  </span>
                  <span class="shrink-0 text-xs tabular-nums text-text-subtle">{{ entry.count }}</span>
                </button>
              </li>
            </ul>
          </details>
        </li>

              <li
                v-if="!visibleActiveEntries.length && !visibleArchivedEntries.length"
                class="px-3 py-6 text-center text-sm text-text-subtle"
                data-testid="communications-entities-empty"
              >
                {{ emptyMessage }}
              </li>
            </ul>
          </BaseCollapse>
        </li>

        <li
          class="flex items-center justify-between gap-2 border-y border-border-muted px-3 py-2.5 transition-colors"
          :class="archivedMode ? 'bg-warning-soft' : ''"
          data-testid="communications-archive-control"
        >
          <span class="flex min-w-0 items-center gap-2">
            <BaseActionIcon action="archive" />
            <span
              class="truncate text-sm"
              :class="archivedMode ? 'font-medium text-text-default' : 'text-text-muted'"
            >
              Ver comunicaciones archivadas
            </span>
          </span>
          <BaseToggle
            :model-value="archivedMode"
            :disabled="scopeLocked"
            size="sm"
            aria-label="Ver comunicaciones archivadas"
            disabled-reason="La búsqueda recorre activos y archivados."
            data-testid="communications-archived-entry"
            @update:model-value="$emit('toggle-archived', $event)"
          />
        </li>

        <li v-if="mode === 'project'" role="presentation" data-testid="communications-own-section">
          <!-- design-tokens: allow-raw-button — cabecera de seccion plegable, no una accion -->
          <button
            type="button"
            class="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-muted transition-colors hover:bg-surface-muted"
            :class="touchMode ? 'min-h-11' : ''"
            :aria-expanded="sidebarSections.own"
            :aria-controls="ownSectionId"
            data-testid="communications-own-section-toggle"
            @click="toggleSidebarSection('own')"
          >
            <span class="flex items-center gap-2">
              <BaseActionIcon :action="sidebarSections.own ? 'collapse' : 'expand'" />
              Comunicaciones propias
            </span>
            <span
              class="font-normal normal-case text-text-subtle"
              data-testid="communications-own-section-count"
            >
              {{ facets.without_project_count || 0 }}
            </span>
          </button>
          <BaseCollapse :id="ownSectionId" :open="sidebarSections.own">
            <ul class="space-y-1" role="list">
              <li>
                <!-- design-tokens: allow-raw-button — selectable navigation row, not a standalone action. -->
                <button
                  type="button"
                  class="flex min-h-10 w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors"
                  :class="entryClass('none')"
                  :aria-current="isSelected('none') ? 'page' : undefined"
                  data-testid="communications-navigation-without-project"
                  @click="$emit('select', 'none')"
                >
                  <span class="truncate">Sin proyecto</span>
                  <span class="shrink-0 text-xs tabular-nums text-text-subtle">
                    {{ facets.without_project_count || 0 }}
                  </span>
                </button>
              </li>
            </ul>
          </BaseCollapse>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup>
import { computed, ref, useId, watch } from 'vue';
import EntityNavigationModeSwitch from '~/components/panel/EntityNavigationModeSwitch.vue';
import BaseActionIcon from '~/components/base/BaseActionIcon.vue';
import BaseCollapse from '~/components/base/BaseCollapse.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import { usePanelSidebarSections } from '~/composables/usePanelSidebarSections';

const props = defineProps({
  mode: { type: String, default: 'project' },
  selection: { type: [String, Number], default: 'all' },
  // Eje de visibilidad, independiente de abierto/cerrado.
  archivedMode: { type: Boolean, default: false },
  // La busqueda recorre los dos estados: el interruptor no filtra nada ahi.
  scopeLocked: { type: Boolean, default: false },
  showInactiveProjects: { type: Boolean, default: false },
  touchMode: { type: Boolean, default: false },
  facets: {
    type: Object,
    default: () => ({
      navigation_total: 0,
      without_project_count: 0,
      projects: [],
      clients: [],
    }),
  },
});

defineEmits([
  'update:mode', 'select', 'toggle-archived', 'toggle-inactive-projects',
]);

const search = ref('');

// Mismo mecanismo que el panel del gestor documental, con la clave de este
// modulo. El panel se monta dos veces a la vez —fijo y dentro del drawer—, asi
// que el pliegue se comparte pero los id de aria-controls no pueden.
const {
  sections: sidebarSections,
  toggle: toggleSidebarSection,
} = usePanelSidebarSections('projectapp-communications-sidebar-sections', {
  entities: true,
  own: true,
});
const sectionUid = useId();
const entitiesSectionId = `communications-sidebar-entities-${sectionUid}`;
const ownSectionId = `communications-sidebar-own-${sectionUid}`;

const entitiesSectionLabel = computed(() => (
  props.mode === 'project' ? 'Proyectos' : 'Clientes'
));

watch(() => props.mode, () => { search.value = ''; });

const entries = computed(() => (
  props.mode === 'project' ? props.facets.projects || [] : props.facets.clients || []
));
const visibleEntries = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('es');
  if (!query) return entries.value;
  return entries.value.filter((entry) => entry.name.toLocaleLowerCase('es').includes(query));
});
// La particion ya no es project-only: el backend manda `catalog_bucket` tambien
// por cliente, asi que los clientes inactivos tienen su propio grupo.
const activeEntries = computed(() => visibleEntries.value.filter(
  (entry) => entry.catalog_bucket !== 'archived',
));
const archivedEntries = computed(() => visibleEntries.value.filter(
  (entry) => entry.catalog_bucket === 'archived',
));

// El interruptor de no-activos es EXCLUYENTE, no aditivo: encendido deja ver
// solo los no activos, apagado solo los activos. Los dos computed son las dos
// caras de la misma condicion, por eso se leen juntos.
const visibleActiveEntries = computed(() => (
  props.mode === 'project' && props.showInactiveProjects ? [] : activeEntries.value
));
const visibleArchivedEntries = computed(() => (
  props.mode === 'project' && !props.showInactiveProjects ? [] : archivedEntries.value
));
const archivedGroupLabel = computed(() => (
  props.mode === 'project' ? 'Proyectos archivados' : 'Clientes archivados'
));
const navigationLabel = computed(() => (
  props.mode === 'project' ? 'Proyectos' : 'Clientes con comunicaciones'
));
const emptyMessage = computed(() => {
  if (search.value.trim()) return 'No hay coincidencias.';
  if (props.mode === 'project' && props.showInactiveProjects) {
    return 'No hay proyectos no activos.';
  }
  return emptyLabel.value;
});
const emptyLabel = computed(() => (
  props.mode === 'project'
    ? 'No hay proyectos disponibles.'
    : 'No hay clientes con comunicaciones en este recorte.'
));

function isSelected(value) {
  return String(props.selection) === String(value);
}

function entryClass(value) {
  return isSelected(value)
    ? 'bg-primary-soft font-medium text-text-brand'
    : 'text-text-default hover:bg-surface-raised';
}
</script>
