<script setup>
import { tagBadgeClass, tagDotClass } from '~/utils/documentTagColors.js'
import {
  statusBadgeClass, statusLabel, formatDocumentDate, folderRowSummary,
  archivedAgeLabel,
} from '~/utils/documentStatus'
import { computed } from 'vue'
import { formatDateTime } from '~/utils/formatDate'
import FolderArchivedBadge from '~/components/panel/documents/FolderArchivedBadge.vue'

const props = defineProps({
  documents: { type: Array, default: () => [] },
  subfolders: { type: Array, default: () => [] },
  editToFor: { type: Function, default: () => null },
  draggingDocId: { type: [Number, String], default: null },
  dragOverFolderId: { type: [Number, String], default: null },
  newlyCreatedId: { type: [Number, String], default: null },
  // El scope sólo decide el encabezado de columna. Todo lo demás (insignia,
  // fecha, arrastre) lo decide `is_archived` de cada fila: con `scope='all'` y
  // con la búsqueda global la lista es mixta.
  scope: { type: String, default: 'active' },
  // Mutación en vuelo: los botones de restaurar giran y quedan inertes.
  updating: { type: Boolean, default: false },
  // Inventario de una fila de subcarpeta. Llega como función y no se consulta
  // el store acá porque este componente es presentacional: sus specs lo montan
  // sin Pinia. El default conserva el conteo directo de siempre; la página lo
  // reemplaza por el que suma el subárbol.
  folderSummary: { type: Function, default: folderRowSummary },
})

const emit = defineEmits([
  'open', 'action', 'select-folder', 'unarchive-folder', 'view-archived-folder',
  'doc-dragstart', 'doc-dragend',
  'folder-dragstart', 'folder-dragend', 'folder-dragover', 'folder-dragleave',
  'drop-on-folder',
])

const dateHeader = computed(() => {
  if (props.scope === 'archived') return 'Archivado'
  return props.scope === 'all' ? 'Fecha' : 'Creado'
})

function archivedContentCount(folder) {
  return (folder.archived_document_count || 0) + (folder.archived_children_count || 0)
}
</script>

<template>
  <div class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-x-auto">
    <table class="w-full">
      <caption class="sr-only">Documentos y subcarpetas de la carpeta actual</caption>
      <thead>
        <tr class="border-b border-border-muted text-left">
          <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Título</th>
          <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Etiquetas</th>
          <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Estado</th>
          <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">{{ dateHeader }}</th>
          <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Acciones</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border-muted">
        <!-- Filas de subcarpeta — fijas arriba, fuera de la paginación -->
        <tr
          v-for="sub in subfolders"
          :key="`folder-${sub.id}`"
          class="transition-colors select-none hover:bg-surface-muted cursor-pointer"
          :class="{ 'ring-2 ring-inset ring-success-strong': dragOverFolderId === sub.id }"
          :draggable="!sub.is_archived"
          @click="emit('select-folder', sub.id)"
          @dragstart="emit('folder-dragstart', $event, sub)"
          @dragend="emit('folder-dragend')"
          @dragover="emit('folder-dragover', $event, sub.id)"
          @dragleave="emit('folder-dragleave')"
          @drop.prevent="emit('drop-on-folder', sub.id)"
        >
          <td class="px-6 py-4">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-amber-500 dark:text-amber-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
              </svg>
              <span class="text-sm font-medium text-text-default truncate">{{ sub.name }}</span>
              <FolderArchivedBadge
                v-if="!sub.is_archived && archivedContentCount(sub)"
                :count="archivedContentCount(sub)"
                :folder-name="sub.name"
                @view="emit('view-archived-folder', sub)"
              />
            </div>
          </td>
          <td class="px-6 py-4 text-sm text-text-subtle" colspan="3">
            {{ folderSummary(sub, sub.is_archived ? 'archived' : 'active') }}
          </td>
          <td class="px-6 py-4" @click.stop>
            <BaseButton
              v-if="sub.is_archived"
              variant="secondary"
              size="sm"
              :loading="updating"
              :disabled="updating"
              data-testid="folder-unarchive"
              @click="emit('unarchive-folder', sub)"
            >
              Restaurar
            </BaseButton>
            <svg v-else class="w-4 h-4 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </td>
        </tr>
        <tr
          v-for="doc in documents"
          :key="doc.id"
          class="hover:bg-surface-muted transition-colors cursor-grab active:cursor-grabbing select-none"
          :class="[
            { 'opacity-50': draggingDocId === doc.id },
            { 'bg-primary-soft transition-colors duration-1000': doc.id === newlyCreatedId }
          ]"
          :draggable="!doc.is_archived"
          @click="emit('open', doc)"
          @dragstart="emit('doc-dragstart', $event, doc)"
          @dragend="emit('doc-dragend')"
        >
          <td class="px-6 py-4">
            <div class="flex items-center gap-2">
              <component
                :is="editToFor(doc) ? 'NuxtLink' : 'span'"
                :to="editToFor(doc) || undefined"
                class="text-sm font-medium text-text-default truncate
                       outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40 rounded"
                @click.stop
              >
                {{ doc.title }}
              </component>
              <span
                v-if="doc.folder_name"
                class="inline-flex items-center px-2 py-0.5 rounded text-2xs font-medium bg-surface-raised text-text-muted flex-shrink-0"
                :title="`Carpeta: ${doc.folder_name}`"
              >
                📁 {{ doc.folder_name }}
              </span>
            </div>
            <div v-if="doc.client_name" class="text-xs text-text-subtle mt-0.5">{{ doc.client_name }}</div>
          </td>
          <td class="px-6 py-4">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="tag in doc.tag_details"
                :key="tag.id"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-medium"
                :class="tagBadgeClass(tag.color)"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="tagDotClass(tag.color)"></span>
                {{ tag.name }}
              </span>
              <span v-if="!doc.tag_details || doc.tag_details.length === 0" class="text-xs text-text-subtle">—</span>
            </div>
          </td>
          <td class="px-6 py-4">
            <span
              v-if="doc.is_archived"
              class="inline-flex items-center rounded-full bg-surface-raised px-2 py-0.5 text-[10px] font-semibold uppercase text-text-muted dark:text-text-subtle"
              data-testid="doc-archived-badge"
            >
              Archivado
            </span>
            <span
              v-else
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              :class="statusBadgeClass(doc.status)"
            >
              {{ statusLabel(doc.status) }}
            </span>
          </td>
          <td class="px-6 py-4 text-sm text-text-muted tabular-nums">
            <template v-if="doc.is_archived">
              <span data-testid="doc-archived-at">{{ formatDateTime(doc.archived_at) }}</span>
              <span class="block text-xs text-text-subtle">{{ archivedAgeLabel(doc.archived_at) }}</span>
            </template>
            <template v-else>{{ formatDocumentDate(doc.created_at) }}</template>
          </td>
          <td class="px-6 py-4" @click.stop>
            <button
              type="button"
              class="p-2.5 -m-1 rounded-lg hover:bg-surface-raised transition-colors text-text-subtle hover:text-text-default
                     outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40"
              title="Acciones"
              :aria-label="`Acciones de ${doc.title}`"
              @click="emit('action', doc)"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="5" r="1.6" />
                <circle cx="12" cy="12" r="1.6" />
                <circle cx="12" cy="19" r="1.6" />
              </svg>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
