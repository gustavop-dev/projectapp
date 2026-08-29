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
        disabled-reason="La búsqueda recorre activos y archivados."
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
          :class="[entryClass('all'), touchMode ? 'min-h-11' : '']"
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
          :class="[entryClass('none'), dropZoneClass('none'), touchMode ? 'min-h-11' : '']"
          :aria-current="ariaCurrent('none')"
          @click="$emit('select', 'none')"
          @dragover.prevent="dragOverId = 'none'"
          @dragleave="dragOverId = null"
          @drop.prevent="onDrop(null)"
        >
          <span>Sin carpeta</span>
          <BaseActionIcon v-if="isDragging" action="move" class="text-text-subtle" />
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
              :class="[entryClass(folder.id), dropZoneClass(folder)]"
              @dragover.prevent="onFolderDragOver(folder)"
              @dragleave="dragOverId = null"
              @drop.prevent="onFolderDrop(folder)"
            >
              <!--
                Comparte padding, radio y tamaño con Todos/Sin carpeta para que
                la columna entera lea sobre un único eje.

                Dos cifras: las subcarpetas que verás al entrar (directas) y los
                documentos que la carpeta guarda EN TOTAL, contando lo que vive
                en sus subcarpetas. Un contador directo de documentos decía cero
                de una carpeta llena y mandaba a buscar al lugar equivocado.
                Los íconos van `aria-hidden` y el rótulo del botón lleva el
                inventario en palabras: dos números pelados no dicen nada leídos.
              -->
              <!-- design-tokens: allow-raw-button — selectable list row, not an action -->
              <button
                type="button"
                class="flex-1 min-w-0 flex items-center gap-1 px-3 py-2 text-sm text-left"
                :class="touchMode ? 'min-h-11' : ''"
                :aria-current="ariaCurrent(folder.id)"
                :aria-label="rowLabel(folder)"
                @click="$emit('select', folder.id)"
              >
                <!-- El cliente va debajo del nombre y sólo si la carpeta lo
                     tiene: es la línea que dice de quién es sin abrirla.
                     `block` y no `flex`, y con piso de ancho: sumar el ícono de
                     editar dejó la fila sin holgura y el nombre se encogía
                     hasta desaparecer. Con `min-w-16` siempre se lee algo, y lo
                     que sobra trunca — el `title` lo recupera. -->
                <span class="flex-1 min-w-16 block">
                  <span class="block truncate" :title="folder.name">{{ folder.name }}</span>
                  <span
                    v-if="folder.client_display_name"
                    class="block truncate text-2xs text-text-subtle"
                    :data-testid="`folder-client-${folder.id}`"
                    :title="folder.client_display_name"
                  >{{ folder.client_display_name }}</span>
                </span>
                <!-- Directa a propósito, a diferencia del contador de al lado:
                     la insignia promete «clic para verlos» y ese clic entra a
                     ESTA carpeta, cuyo listado no es recursivo. -->
                <FolderArchivedBadge
                  v-if="folderStore.archivedContentCount(folder)"
                  :count="folderStore.archivedContentCount(folder)"
                  :folder-name="folder.name"
                  @view="$emit('view-archived', folder)"
                />
                <template v-if="!isDragging || dragOverId !== folder.id">
                  <span
                    v-if="rowCounts(folder).subs"
                    class="flex items-center gap-0.5 text-xs text-text-subtle flex-shrink-0"
                    data-testid="folder-subfolder-count"
                  >
                    <!-- panel-action-icons: allow-status-glyph — identifies the adjacent subfolder count. -->
                    <FolderIcon class="h-3 w-3" aria-hidden="true" />
                    {{ rowCounts(folder).subs }}
                  </span>
                  <span
                    class="flex items-center gap-0.5 text-xs text-text-subtle flex-shrink-0"
                    data-testid="folder-document-count"
                  >
                    <!-- panel-action-icons: allow-status-glyph — identifies the adjacent document count. -->
                    <DocumentTextIcon class="h-3 w-3" aria-hidden="true" />
                    {{ rowCounts(folder).docs }}
                  </span>
                </template>
                <BaseActionIcon v-else action="move" class="text-success-strong" />
              </button>

              <!-- Clúster derecho: reordenar (hover) + archivar + eliminar. -->
              <div v-if="!folder.is_system_managed" class="flex items-center flex-shrink-0 pr-1.5">
                <div
                  class="folder-drag-handle touch-reveal touch-drag-handle flex cursor-grab items-center justify-center text-text-subtle transition-opacity active:cursor-grabbing dark:text-text-muted"
                  :class="[
                    touchMode ? 'w-8 min-h-11 opacity-100' : 'w-5 opacity-0 group-hover:opacity-100',
                    { invisible: isDragging },
                  ]"
                  title="Arrastrar para reordenar"
                >
                  <BaseActionIcon action="sort" />
                </div>

                <!-- Editar vive acá por lo mismo que archivar y eliminar: es
                     igual de frecuente, y hasta ahora era la única de las tres
                     que había que ir a buscar al modal de NUEVA carpeta. -->
                <BaseTooltip position="top" width="max-w-xs" min-width="min-w-0">
                  <template #trigger>
                    <BaseButton
                      variant="ghost"
                      icon-only
                      size="sm"
                      :aria-label="`Editar carpeta ${folder.name}`"
                      :class="['opacity-70 hover:opacity-100 focus-visible:opacity-100 transition-opacity', touchMode ? 'min-h-11 min-w-11' : '']"
                      data-testid="folder-edit"
                      @click="$emit('edit', folder)"
                    >
                      <BaseActionIcon action="edit" />
                    </BaseButton>
                  </template>
                  Editar carpeta
                </BaseTooltip>

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
                      :class="['opacity-70 hover:opacity-100 focus-visible:opacity-100 transition-opacity', touchMode ? 'min-h-11 min-w-11' : '']"
                      data-testid="folder-archive"
                      @click="$emit('archive', folder)"
                    >
                      <BaseActionIcon action="archive" />
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
                      :disabled-reason="deleteTooltip(folder)"
                      :aria-label="`Eliminar carpeta ${folder.name}`"
                      :class="['opacity-70 hover:opacity-100 focus-visible:opacity-100 transition-opacity', touchMode ? 'min-h-11 min-w-11' : '']"
                      data-testid="folder-delete"
                      @click="$emit('delete', folder)"
                    >
                      <BaseActionIcon action="delete" />
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
        <BaseActionIcon action="create" />
        Nueva carpeta
      </BaseButton>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { DocumentTextIcon, FolderIcon } from '@heroicons/vue/24/outline';
import draggable from 'vuedraggable';
import FolderArchivedBadge from '~/components/panel/documents/FolderArchivedBadge.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import { folderRowLabel, folderRowSummary, scopedCounts } from '~/utils/documentStatus';

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
  touchMode: { type: Boolean, default: false },
});

const emit = defineEmits([
  'select', 'manage', 'folder-drop', 'edit', 'delete', 'archive', 'view-archived',
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

/**
 * Las dos cifras de la fila: subcarpetas DIRECTAS y documentos del subárbol.
 *
 * Las subcarpetas se quedan directas porque responden «qué voy a ver si entro»,
 * y entrar lista `childrenOf(id, scope)` — un total recursivo prometería filas
 * que ese clic no muestra.
 */
function rowCounts(folder) {
  return {
    subs: scopedCounts(folder, props.archiveScope).subs,
    docs: folderStore.recursiveDocumentCount(folder, props.archiveScope),
  };
}

function rowLabel(folder) {
  return folderRowLabel(folder.name, rowCounts(folder));
}

// Ojo: `hasContent` y `deleteTooltip` se quedan con el conteo DIRECTO a
// propósito. Espejan el 409 de `delete_document_folder`, que cuenta
// `folder.documents` y `folder.children` de un salto y sin excluir archivados;
// un tooltip recursivo diría «contiene 12 documentos» donde el servidor
// responde «tiene 1 subcarpeta». No unificar con el contador de la fila.
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

function dropZoneClass(folder) {
  if (folder?.is_system_managed) return '';
  const id = folder?.id ?? folder;
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

function onFolderDragOver(folder) {
  if (!folder.is_system_managed && !isFolderDragging.value) {
    dragOverId.value = folder.id;
  }
}

function onFolderDrop(folder) {
  if (!folder.is_system_managed && !isFolderDragging.value) onDrop(folder.id);
}

async function handleFolderReorder() {
  isFolderDragging.value = false;
  const newIds = localFolders.value
    .filter((folder) => !folder.is_system_managed)
    .map((folder) => folder.id);
  const previousIds = props.folders
    .filter((folder) => !folder.is_system_managed)
    .map((folder) => folder.id);
  const unchanged = newIds.every((id, i) => id === previousIds[i]);
  if (unchanged) return;
  const result = await folderStore.reorderFolders(newIds);
  if (!result.success) {
    await folderStore.fetchFolders();
  }
}
</script>
