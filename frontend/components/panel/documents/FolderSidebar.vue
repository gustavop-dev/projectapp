<template>
  <aside class="bg-surface rounded-xl shadow-sm border border-border-muted flex flex-col">
    <div class="px-4 py-3 border-b border-border-muted flex items-center justify-between flex-shrink-0">
      <h3 class="text-xs font-semibold text-text-muted uppercase tracking-wider">Carpetas</h3>
      <button
        type="button"
        class="text-xs font-medium text-text-brand hover:text-text-brand"
        @click="$emit('manage')"
      >
        Gestionar
      </button>
    </div>

    <!--
      Interruptor de modo, deliberadamente FUERA de la lista. Como pseudo-entrada
      entre las carpetas, «Archivados» se leía como un destino más y el usuario no
      tenía cómo saber que el archivo es el ámbito en que se ve TODO el panel:
      volvía a «Todos», seguía viendo archivados y lo tomaba por documentos
      perdidos. Un interruptor sí declara un modo.
    -->
    <div
      class="px-3 py-2.5 border-b border-border-muted flex items-center justify-between gap-2 flex-shrink-0 transition-colors"
      :class="archivedMode ? 'bg-warning-soft' : ''"
    >
      <span class="flex items-center gap-2 min-w-0">
        <svg class="w-3.5 h-3.5 flex-shrink-0 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
        <span class="text-sm truncate" :class="archivedMode ? 'font-medium text-text-default' : 'text-text-muted'">
          Ver archivados
        </span>
        <span class="text-xs text-text-subtle flex-shrink-0" data-testid="folder-archived-count">{{ archivedCount }}</span>
      </span>
      <BaseToggle
        :model-value="archivedMode"
        :disabled="scopeLocked"
        size="sm"
        aria-label="Ver archivados"
        :title="scopeLocked ? 'La búsqueda recorre activos y archivados' : undefined"
        data-testid="folder-archived-entry"
        @update:model-value="$emit('toggle-archived', $event)"
      />
    </div>

    <ul class="p-2 space-y-1 flex-1 overflow-y-auto" role="list" data-testid="folder-list">
      <li>
        <!-- design-tokens: allow-raw-button — selectable list row, not an action -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all"
          :class="entryClass('all')"
          :aria-current="ariaCurrent('all')"
          @click="$emit('select', 'all')"
        >
          <span>Todos</span>
          <span class="text-xs text-text-subtle">{{ totalCount }}</span>
        </button>
      </li>

      <!-- No folder — also a drop target -->
      <li>
        <!-- design-tokens: allow-raw-button — selectable list row, not an action -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all"
          :class="[entryClass('none'), dropZoneClass('none')]"
          :aria-current="ariaCurrent('none')"
          @click="$emit('select', 'none')"
          @dragover.prevent="dragOverId = 'none'"
          @dragleave="dragOverId = null"
          @drop.prevent="onDrop(null)"
        >
          <span>Sin carpeta</span>
          <svg v-if="isDragging" class="w-3 h-3 text-text-subtle flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
          <span v-else class="text-xs text-text-subtle">{{ unfiledCount }}</span>
        </button>
      </li>

      <li v-if="folders.length" class="my-1 border-t border-border-muted"></li>

      <!-- Folder entries — draggable to reorder, also drop targets for documents -->
      <draggable
        v-model="localFolders"
        item-key="id"
        handle=".folder-drag-handle"
        ghost-class="opacity-40"
        chosen-class="ring-1 ring-emerald-300"
        :disabled="isDragging"
        tag="div"
        @start="isFolderDragging = true"
        @end="handleFolderReorder"
      >
        <template #item="{ element: folder }">
          <li :key="folder.id" class="group">
            <div
              class="flex items-center rounded-lg transition-all"
              :class="[entryClass(folder.id), dropZoneClass(folder.id)]"
              @dragover.prevent="onFolderDragOver(folder.id)"
              @dragleave="dragOverId = null"
              @drop.prevent="onFolderDrop(folder.id)"
            >
              <!-- Comparte padding, radio y tamaño con Todos/Sin carpeta para que la
                   columna entera lea sobre un único eje.
                   design-tokens: allow-raw-button — selectable list row, not an action -->
              <button
                type="button"
                class="flex-1 min-w-0 flex items-center gap-1 px-3 py-2 text-sm text-left"
                :aria-current="ariaCurrent(folder.id)"
                @click="$emit('select', folder.id)"
              >
                <span class="truncate flex-1 min-w-0">{{ folder.name }}</span>
                <svg
                  v-if="folder.children_count > 0"
                  class="w-3 h-3 text-text-subtle flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <title>Tiene subcarpetas</title>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
                <FolderArchivedBadge
                  v-if="folderStore.archivedContentCount(folder)"
                  :count="folderStore.archivedContentCount(folder)"
                  :folder-name="folder.name"
                  @view="$emit('view-archived', folder)"
                />
                <span v-if="!isDragging || dragOverId !== folder.id" class="text-xs text-text-subtle flex-shrink-0">{{ scopedDocumentCount(folder, archiveScope) }}</span>
                <svg v-else class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <!-- Clúster derecho: reordenar (hover) + archivar + eliminar. -->
              <div class="flex items-center flex-shrink-0 pr-1.5">
                <div
                  class="folder-drag-handle w-5 flex items-center justify-center text-text-subtle dark:text-text-muted opacity-0 group-hover:opacity-100 cursor-grab active:cursor-grabbing transition-opacity"
                  :class="{ invisible: isDragging }"
                  title="Arrastrar para reordenar"
                >
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 13.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zM8 21a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm8 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" />
                  </svg>
                </div>

                <!-- Archivar vive acá y no sólo en el gestor de carpetas: es la
                     salida para una carpeta con contenido, que no se puede
                     eliminar. Por eso está siempre habilitado. -->
                <BaseTooltip position="top" width="max-w-xs" min-width="min-w-0">
                  <template #trigger>
                    <BaseButton
                      variant="ghost"
                      icon-only
                      size="sm"
                      :aria-label="`Archivar carpeta ${folder.name}`"
                      class="opacity-70 hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                      data-testid="folder-archive"
                      @click="$emit('archive', folder)"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                      </svg>
                    </BaseButton>
                  </template>
                  Archivar carpeta
                </BaseTooltip>

                <!-- Eliminar sólo se ofrece cuando de verdad se puede: el
                     backend responde 409 con cualquier contenido, archivado
                     incluido, así que el conteo tiene que mirarlo todo. -->
                <BaseTooltip position="top" width="max-w-xs" min-width="min-w-0">
                  <template #trigger>
                    <BaseButton
                      variant="danger-ghost"
                      icon-only
                      size="sm"
                      :disabled="hasContent(folder)"
                      :aria-label="`Eliminar carpeta ${folder.name}`"
                      class="opacity-70 hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                      data-testid="folder-delete"
                      @click="$emit('delete', folder)"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </BaseButton>
                  </template>
                  {{ deleteTooltip(folder) }}
                </BaseTooltip>
              </div>
            </div>
          </li>
        </template>
      </draggable>
    </ul>

    <div class="p-3 border-t border-border-muted flex-shrink-0">
      <BaseButton variant="secondary" size="md" class="w-full" @click="$emit('manage')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nueva carpeta
      </BaseButton>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import FolderArchivedBadge from '~/components/panel/documents/FolderArchivedBadge.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import { folderRowSummary, scopedDocumentCount } from '~/utils/documentStatus';

const props = defineProps({
  folders: { type: Array, default: () => [] },
  activeId: { type: [String, Number], default: 'all' },
  archiveScope: { type: String, default: 'active' },
  totalCount: { type: Number, default: 0 },
  archivedCount: { type: Number, default: 0 },
  unfiledCount: { type: Number, default: 0 },
  isDragging: { type: Boolean, default: false },
  draggingFolderId: { type: [String, Number], default: null },
  // La búsqueda recorre los dos estados, así que el interruptor queda inerte
  // mientras hay consulta — misma regla que el control de la barra, porque dos
  // mandos del mismo eje que se comportan distinto vuelven a mentir.
  scopeLocked: { type: Boolean, default: false },
});

const emit = defineEmits([
  'select', 'manage', 'folder-drop', 'delete', 'archive', 'view-archived',
  'toggle-archived',
]);

const folderStore = useDocumentFolderStore();
const dragOverId = ref(null);
const localFolders = ref([]);
const isFolderDragging = ref(false);

watch(() => props.folders, (v) => {
  localFolders.value = [...v];
}, { immediate: true });

const ACTIVE_CLASS = 'bg-primary-soft text-text-brand font-medium';
const INACTIVE_CLASS = 'text-text-default hover:bg-surface-muted';

function entryClass(id) {
  return props.activeId === id ? ACTIVE_CLASS : INACTIVE_CLASS;
}

// El resaltado de la fila de carpeta vive en el div contenedor (comparte la
// caja con los íconos de acción), así que la marca semántica va en el botón:
// es el único gancho estable para «dónde dice el panel que estoy».
function ariaCurrent(id) {
  return props.activeId === id ? 'page' : undefined;
}

function hasContent(folder) {
  return folderStore.totalContentCount(folder) > 0;
}

function deleteTooltip(folder) {
  if (!hasContent(folder)) return 'Eliminar carpeta';
  return `No se puede eliminar: contiene ${folderRowSummary(folder, 'all')}. `
    + 'Archívala en su lugar.';
}

// El interruptor sólo está encendido en el scope archivado puro. Con 'all' la
// lista mezcla los dos estados, y encenderlo ahí diría que se está viendo sólo
// el archivo; ese caso lo declara el rótulo de la cabecera del listado.
const archivedMode = computed(() => props.archiveScope === 'archived');

function dropZoneClass(id) {
  // Acepta documentos (props.isDragging) o carpetas en arrastre para anidar.
  const anyDrag = props.isDragging || props.draggingFolderId != null;
  if (!anyDrag || isFolderDragging.value) return '';
  if (dragOverId.value === id) {
    return 'ring-2 ring-emerald-400 bg-primary-soft !text-text-brand dark:!text-emerald-300';
  }
  return 'ring-1 ring-dashed ring-border-default';
}

function onDrop(folderId) {
  dragOverId.value = null;
  emit('folder-drop', folderId);
}

function onFolderDragOver(folderId) {
  if (!isFolderDragging.value) dragOverId.value = folderId;
}

function onFolderDrop(folderId) {
  if (!isFolderDragging.value) onDrop(folderId);
}

async function handleFolderReorder() {
  isFolderDragging.value = false;
  const newIds = localFolders.value.map((f) => f.id);
  const unchanged = newIds.every((id, i) => id === props.folders[i]?.id);
  if (unchanged) return;
  const result = await folderStore.reorderFolders(newIds);
  if (!result.success) {
    await folderStore.fetchFolders();
  }
}
</script>
