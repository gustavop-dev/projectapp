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

    <nav class="min-h-0 flex-1 overflow-y-auto p-2" :aria-label="navigationLabel">
      <ul class="space-y-1">
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

        <li v-if="showWithoutProject">
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
            <span class="shrink-0 text-xs tabular-nums text-text-subtle">{{ facets.without_project_count || 0 }}</span>
          </button>
        </li>

        <li v-if="visibleEntries.length" class="my-1 border-t border-border-muted" aria-hidden="true" />
        <li v-for="entry in activeEntries" :key="entry.id">
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
        <li v-if="archivedEntries.length" role="presentation">
          <details open data-testid="communications-navigation-archived-group">
            <summary class="flex cursor-pointer items-center justify-between gap-2 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-muted hover:bg-surface-muted">
              <span>Proyectos archivados</span>
              <span class="font-normal normal-case text-text-subtle">{{ archivedEntries.length }}</span>
            </summary>
            <ul class="mt-1 space-y-1" role="list">
              <li v-for="entry in archivedEntries" :key="entry.id">
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
      </ul>

      <p v-if="visibleEntries.length === 0 && !showWithoutProject" class="px-3 py-6 text-center text-sm text-text-subtle">
        {{ search.trim() ? 'No hay coincidencias.' : emptyLabel }}
      </p>
    </nav>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import EntityNavigationModeSwitch from '~/components/panel/EntityNavigationModeSwitch.vue';

const props = defineProps({
  mode: { type: String, default: 'project' },
  selection: { type: [String, Number], default: 'all' },
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

defineEmits(['update:mode', 'select']);

const search = ref('');

watch(() => props.mode, () => { search.value = ''; });

const entries = computed(() => (
  props.mode === 'project' ? props.facets.projects || [] : props.facets.clients || []
));
const visibleEntries = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('es');
  if (!query) return entries.value;
  return entries.value.filter((entry) => entry.name.toLocaleLowerCase('es').includes(query));
});
const activeEntries = computed(() => visibleEntries.value.filter((entry) => (
  props.mode !== 'project' || entry.catalog_bucket !== 'archived'
)));
const archivedEntries = computed(() => (
  props.mode === 'project'
    ? visibleEntries.value.filter((entry) => entry.catalog_bucket === 'archived')
    : []
));
const showWithoutProject = computed(() => (
  props.mode === 'project'
  && (
    isSelected('none')
    || (
      props.facets.without_project_count > 0
      && (
        !search.value.trim()
        || 'sin proyecto'.includes(search.value.trim().toLocaleLowerCase('es'))
      )
    )
  )
));
const navigationLabel = computed(() => (
  props.mode === 'project' ? 'Proyectos' : 'Clientes con comunicaciones'
));
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
