<script setup>
import DocumentCard from '~/components/panel/documents/DocumentCard.vue'
import FolderArchivedBadge from '~/components/panel/documents/FolderArchivedBadge.vue'
import { folderRowSummary } from '~/utils/documentStatus'
import { isPlainActivation } from '~/utils/rowNavigation'

defineProps({
  documents: { type: Array, default: () => [] },
  subfolders: { type: Array, default: () => [] },
  editToFor: { type: Function, default: () => null },
  // Igual que en la tabla: dirección de la subcarpeta, o null cuando entrar no
  // es navegar por URL.
  folderToFor: { type: Function, default: () => null },
  draggingDocId: { type: [Number, String], default: null },
  dragOverFolderId: { type: [Number, String], default: null },
  newlyCreatedId: { type: [Number, String], default: null },
  // Igual que en la tabla: el scope no decide nada por fila, sólo acompaña.
  scope: { type: String, default: 'active' },
  // Mutación en vuelo: los botones de restaurar giran y quedan inertes.
  updating: { type: Boolean, default: false },
  // Igual que en la tabla: función, no store — el componente es presentacional.
  folderSummary: { type: Function, default: folderRowSummary },
})

const emit = defineEmits([
  'open', 'action', 'select-folder', 'unarchive-folder', 'view-archived-folder',
  'doc-dragstart', 'doc-dragend',
  'folder-dragstart', 'folder-dragend', 'folder-dragover', 'folder-dragleave',
  'drop-on-folder',
])

/** Igual que en la tabla: el enlace se queda los gestos, la página el clic simple. */
function onFolderLink(event, sub) {
  if (!isPlainActivation(event)) return
  event.preventDefault()
  emit('select-folder', sub.id)
}

function archivedContentCount(folder) {
  return (folder.archived_document_count || 0) + (folder.archived_children_count || 0)
}
</script>

<template>
  <TransitionGroup
    tag="div"
    name="doc-grid"
    class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4"
    data-testid="documents-grid"
  >
    <!-- Subfolder cards first, outside pagination (same rule as the table) -->
    <div
      v-for="sub in subfolders"
      :key="`folder-${sub.id}`"
      class="flex flex-col items-center justify-center gap-2 min-h-44 p-4 rounded-xl
             border-2 border-dashed border-border-default bg-surface cursor-pointer select-none
             text-center outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40
             motion-safe:transition-transform motion-safe:duration-fast motion-safe:ease-out-soft"
      :class="{
        'ring-2 ring-success-strong border-success-strong/60 motion-safe:scale-[1.02]':
          dragOverFolderId === sub.id,
      }"
      :draggable="!sub.is_archived && !sub.is_system_managed"
      :data-testid="`folder-card-${sub.id}`"
      @click="emit('select-folder', sub.id)"
      @dragstart="emit('folder-dragstart', $event, sub)"
      @dragend="emit('folder-dragend')"
      @dragover="emit('folder-dragover', $event, sub.id)"
      @dragleave="emit('folder-dragleave')"
      @drop.prevent="emit('drop-on-folder', sub.id)"
    >
      <svg class="w-10 h-10 text-amber-500 dark:text-amber-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
      </svg>
      <!-- El enlace del nombre reemplaza al role="button"/tabindex del contenedor:
           es alcanzable con tabulador, se activa con enter, se anuncia como
           enlace y no duplica la parada de tabulación. -->
      <BaseRowLink
        :to="folderToFor(sub)"
        :data-testid="`folder-open-${sub.id}`"
        class="text-sm font-medium text-text-default truncate max-w-full"
        :title="sub.name"
        @click="onFolderLink($event, sub)"
      >{{ sub.name }}</BaseRowLink>
      <span class="text-xs text-text-subtle">
        {{ folderSummary(sub, sub.is_archived ? 'archived' : 'active') }}
      </span>
      <FolderArchivedBadge
        v-if="!sub.is_archived && archivedContentCount(sub)"
        :count="archivedContentCount(sub)"
        :folder-name="sub.name"
        @view="emit('view-archived-folder', sub)"
      />
      <BaseButton
        v-if="sub.is_archived"
        variant="secondary"
        size="sm"
        :loading="updating"
        :disabled="updating"
        data-testid="folder-unarchive"
        @click.stop="emit('unarchive-folder', sub)"
      >
        Restaurar
      </BaseButton>
    </div>

    <DocumentCard
      v-for="doc in documents"
      :key="doc.id"
      :document="doc"
      :edit-to="editToFor(doc)"
      :dragging="draggingDocId === doc.id"
      :newly-created="newlyCreatedId === doc.id"
      :archived="!!doc.is_archived"
      @open="(event) => emit('open', doc, event)"
      @action="emit('action', doc)"
      @dragstart="emit('doc-dragstart', $event, doc)"
      @dragend="emit('doc-dragend')"
    />
  </TransitionGroup>
</template>

<style scoped>
/* Collection changes (filter/folder/page/drop): items fade up in and the
 * survivors glide to their new cell. Leave is a quick fade in place — an
 * absolutely-positioned leave would lose its grid cell sizing. */
@media (prefers-reduced-motion: no-preference) {
  .doc-grid-enter-active {
    transition: opacity 250ms cubic-bezier(0.22, 1, 0.36, 1),
                transform 250ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .doc-grid-enter-from {
    opacity: 0;
    transform: translateY(8px);
  }
  .doc-grid-leave-active {
    transition: opacity 150ms ease-out;
  }
  .doc-grid-leave-to {
    opacity: 0;
  }
  .doc-grid-move {
    transition: transform 250ms cubic-bezier(0.22, 1, 0.36, 1);
  }
}
</style>
