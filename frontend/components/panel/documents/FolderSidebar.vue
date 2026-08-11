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

    <ul class="p-2 space-y-1 flex-1 overflow-y-auto" role="list">
      <li>
        <!-- design-tokens: allow-raw-button — selectable list row, not an action -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all"
          :class="entryClass('all')"
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
          @click="$emit('select', 'none')"
          @dragover.prevent="dragOverId = 'none'"
          @dragleave="dragOverId = null"
          @drop.prevent="onDrop(null)"
        >
          <span>Sin carpeta</span>
          <svg v-if="isDragging" class="w-3 h-3 text-text-subtle flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
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
                <span v-if="!isDragging || dragOverId !== folder.id" class="text-xs text-text-subtle flex-shrink-0">{{ folder.document_count }}</span>
                <svg v-else class="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <!-- Clúster derecho: reordenar (hover) + eliminar (siempre visible). -->
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

                <!-- Un solo icono, dos desenlaces: el modal decide eliminar vs
                     archivar con el inventario a la vista. Antes esto se
                     bloqueaba con un tooltip cuando la carpeta tenía contenido,
                     pero ahora sí hay algo que se puede hacer con ella. -->
                <BaseButton
                  variant="danger-ghost"
                  icon-only
                  size="sm"
                  :aria-label="`Eliminar carpeta ${folder.name}`"
                  title="Eliminar carpeta"
                  class="opacity-70 hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                  data-testid="folder-delete"
                  @click="$emit('delete', folder)"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </BaseButton>
              </div>
            </div>
          </li>
        </template>
      </draggable>

      <!--
        Archivados: tercera pseudo-entrada, junto a Todos y Sin carpeta.
        A propósito NO es drop target: soltar algo encima sería un archivado
        implícito, y archivar debe ser siempre un gesto explícito.
      -->
      <li class="my-1 border-t border-border-muted"></li>
      <li>
        <!-- design-tokens: allow-raw-button — selectable list row, not an action -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all"
          :class="entryClass('archived')"
          data-testid="folder-archived-entry"
          @click="$emit('select', 'archived')"
        >
          <span class="flex items-center gap-2">
            <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            Archivados
          </span>
          <span class="text-xs text-text-subtle">{{ archivedCount }}</span>
        </button>
      </li>
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
import { ref, watch } from 'vue';
import draggable from 'vuedraggable';

const props = defineProps({
  folders: { type: Array, default: () => [] },
  activeId: { type: [String, Number], default: 'all' },
  totalCount: { type: Number, default: 0 },
  archivedCount: { type: Number, default: 0 },
  isDragging: { type: Boolean, default: false },
  draggingFolderId: { type: [String, Number], default: null },
});

const emit = defineEmits(['select', 'manage', 'folder-drop', 'delete']);

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
