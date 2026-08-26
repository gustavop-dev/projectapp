<script setup>
import {
  formatDocumentDate, folderRowSummary,
  archivedAgeLabel,
} from '~/utils/documentStatus'
import { computed, ref } from 'vue'
import { formatDateTime } from '~/utils/formatDate'
import { isPlainActivation } from '~/utils/rowNavigation'
import BaseButton from '~/components/base/BaseButton.vue'
import FolderArchivedBadge from '~/components/panel/documents/FolderArchivedBadge.vue'
import DocumentStateList from '~/components/panel/documents/DocumentStateList.vue'
import BaseOverflowText from '~/components/base/BaseOverflowText.vue'
import BaseResizeHandle from '~/components/base/BaseResizeHandle.vue'
import { usePanelViewportProfile } from '~/composables/usePanelViewportProfile'
import { useResizableTableColumns } from '~/composables/useResizableTableColumns'

const props = defineProps({
  documents: { type: Array, default: () => [] },
  subfolders: { type: Array, default: () => [] },
  editToFor: { type: Function, default: () => null },
  // Dirección de una subcarpeta (`?folder=`). Devuelve null cuando entrar no es
  // navegar por URL — en plena búsqueda, por ejemplo — y ahí el nombre deja de
  // fingir que es un enlace.
  folderToFor: { type: Function, default: () => null },
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

const DOCUMENT_TABLE_WIDTH_KEY = 'projectapp-table-widths:documents-list'
const tableContainerRef = ref(null)
const { profile: viewportProfile } = usePanelViewportProfile()

// Workflow and actions stay readable. The remaining flexible columns give
// space back in the business order requested by the Documents UX.
const widthColumns = computed(() => [
  {
    key: 'title',
    columnWidth: { min: 240, default: 320, max: 520, resizable: true },
  },
  {
    key: 'client',
    columnWidth: { min: 128, default: 176, max: 240, shrinkPriority: 2, fillPriority: 2 },
  },
  {
    key: 'project',
    columnWidth: { min: 112, default: 160, max: 224, shrinkPriority: 1, fillPriority: 1 },
  },
  {
    key: 'states',
    columnWidth: { min: 224, default: 224, max: 224, fixed: true },
  },
  {
    key: 'date',
    columnWidth: { min: 112, default: 128, max: 640, shrinkPriority: 3, fillPriority: 3 },
  },
  {
    key: 'actions',
    columnWidth: { min: 80, default: 80, max: 80, fixed: true },
  },
])

const visibleWidthKeys = computed(() => (
  ['desktop', 'wide'].includes(viewportProfile.value)
    ? widthColumns.value.map((column) => column.key)
    : ['title', 'date', 'actions']
))

const {
  columnStyle,
  draggingKey: resizingColumn,
  onPointerEnd: endColumnResize,
  onPointerMove: moveColumnResize,
  onPointerStart: startColumnResize,
  preferredWidth,
  reset: resetColumnWidth,
  resizeTo: resizeColumnTo,
  tableStyle: documentTableStyle,
} = useResizableTableColumns({
  columns: widthColumns,
  containerRef: tableContainerRef,
  storageKey: DOCUMENT_TABLE_WIDTH_KEY,
  visibleKeys: visibleWidthKeys,
})

function archivedContentCount(folder) {
  return (folder.archived_document_count || 0) + (folder.archived_children_count || 0)
}

/**
 * El nombre de la carpeta es un enlace por los gestos del navegador —
 * ctrl+clic, rueda, «copiar dirección» —, pero el clic simple se lo queda la
 * página: entrar a una carpeta pasa por el store, que además tiene su propio
 * camino cuando hay una búsqueda en curso.
 */
function onFolderLink(event, sub) {
  if (!isPlainActivation(event)) return
  event.preventDefault()
  emit('select-folder', sub.id)
}
</script>

<template>
  <div
    ref="tableContainerRef"
    class="overflow-x-auto rounded-xl border border-border-muted bg-surface shadow-sm"
    :class="resizingColumn ? 'select-none' : ''"
  >
    <table class="w-full" :style="documentTableStyle">
      <caption class="sr-only">Documentos y subcarpetas de la carpeta actual</caption>
      <thead>
        <tr class="border-b border-border-muted text-left">
          <th
            class="relative px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider"
            :style="columnStyle('title')"
          >
            Título
            <BaseResizeHandle
              :value="preferredWidth('title')"
              :min="240"
              :max="520"
              label="Ajustar el ancho de la columna Título"
              test-id="documents-title-resize-handle"
              class="absolute -right-2 top-0 z-20 h-full w-4"
              indicator-class="h-7 w-0.5"
              @pointer-start="startColumnResize('title', $event)"
              @pointer-move="moveColumnResize('title', $event)"
              @pointer-end="endColumnResize('title')"
              @resize="resizeColumnTo('title', $event)"
              @reset="resetColumnWidth('title')"
            />
          </th>
          <th :style="columnStyle('client')" class="hidden px-6 py-3 text-xs font-medium uppercase tracking-wider text-text-muted panel-desktop:table-cell">Cliente</th>
          <th :style="columnStyle('project')" class="hidden px-6 py-3 text-xs font-medium uppercase tracking-wider text-text-muted panel-desktop:table-cell">Proyecto</th>
          <th :style="columnStyle('states')" class="hidden px-6 py-3 text-xs font-medium uppercase tracking-wider text-text-muted panel-desktop:table-cell">Estados</th>
          <th :style="columnStyle('date')" class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">{{ dateHeader }}</th>
          <th :style="columnStyle('actions')" class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Acciones</th>
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
              <BaseRowLink
                :to="folderToFor(sub)"
                :data-testid="`folder-open-${sub.id}`"
                class="text-sm font-medium text-text-default truncate"
                @click="onFolderLink($event, sub)"
              >{{ sub.name }}</BaseRowLink>
              <FolderArchivedBadge
                v-if="!sub.is_archived && archivedContentCount(sub)"
                :count="archivedContentCount(sub)"
                :folder-name="sub.name"
                @view="emit('view-archived-folder', sub)"
              />
            </div>
          </td>
          <td class="px-6 py-4 text-sm text-text-subtle" colspan="4">
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
        <!-- design-tokens: allow-clickable-row — BaseOverflowText encapsula el BaseRowLink real. -->
        <tr
          v-for="doc in documents"
          :key="doc.id"
          class="hover:bg-surface-muted transition-colors cursor-grab active:cursor-grabbing select-none"
          :class="[
            { 'opacity-50': draggingDocId === doc.id },
            { 'bg-primary-soft transition-colors duration-1000': doc.id === newlyCreatedId }
          ]"
          :draggable="!doc.is_archived"
          :data-testid="`document-row-${doc.id}`"
          @click="emit('open', doc, $event)"
          @auxclick.middle="emit('open', doc, $event)"
          @dragstart="emit('doc-dragstart', $event, doc)"
          @dragend="emit('doc-dragend')"
        >
          <!-- `relative` es el marco contra el que se estira el enlace del
               título: así toda la celda es el enlace, no sólo las letras. -->
          <td class="relative px-6 py-4">
            <div class="flex items-center gap-2">
              <BaseOverflowText
                :to="editToFor(doc)"
                :text="doc.title"
                :lines="2"
                stretch
                :test-id="`document-open-${doc.id}`"
                class="min-w-0 flex-1"
                content-classes="text-sm font-medium leading-snug text-text-default hover:text-text-brand transition-colors"
              />
              <!-- Por encima del área estirada para no perder su tooltip. -->
              <span
                v-if="doc.folder_name"
                class="relative z-10 inline-flex items-center px-2 py-0.5 rounded text-2xs font-medium bg-surface-raised text-text-muted flex-shrink-0"
                :title="`Carpeta: ${doc.folder_name}`"
              >
                📁 {{ doc.folder_name }}
              </span>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-text-muted panel-desktop:hidden">
              <span v-if="doc.client_display_name || doc.client_name">
                {{ doc.client_display_name || doc.client_name }}
              </span>
              <span v-if="doc.project_name">{{ doc.project_name }}</span>
              <BaseBadge v-if="doc.is_archived" variant="neutral" size="sm">Archivado</BaseBadge>
              <DocumentStateList v-else :episodes="doc.active_states" :max-visible="2" />
            </div>
          </td>
          <td class="hidden px-6 py-4 text-sm panel-desktop:table-cell" :data-testid="`doc-client-cell-${doc.id}`">
            <span v-if="doc.client_display_name" class="text-text-default">{{ doc.client_display_name }}</span>
            <!-- Nombre libre heredado, sin cliente vinculado: en itálica para
                 que se note que aún no es una relación. -->
            <span
              v-else-if="doc.client_name"
              class="italic text-text-subtle"
              title="Nombre libre, sin cliente vinculado"
            >{{ doc.client_name }}</span>
            <span v-else class="text-text-subtle">—</span>
          </td>
          <td class="hidden px-6 py-4 text-sm panel-desktop:table-cell" :data-testid="`doc-project-cell-${doc.id}`">
            <span v-if="doc.project_name" class="text-text-default">{{ doc.project_name }}</span>
            <span v-else class="text-text-subtle">—</span>
          </td>
          <td class="hidden px-6 py-4 panel-desktop:table-cell">
            <BaseBadge
              v-if="doc.is_archived"
              variant="neutral"
              size="sm"
              data-testid="doc-archived-badge"
            >
              Archivado
            </BaseBadge>
            <DocumentStateList v-else :episodes="doc.active_states" :max-visible="3" />
          </td>
          <td class="px-6 py-4 text-sm text-text-muted tabular-nums">
            <template v-if="doc.is_archived">
              <span data-testid="doc-archived-at">{{ formatDateTime(doc.archived_at) }}</span>
              <span class="block text-xs text-text-subtle">{{ archivedAgeLabel(doc.archived_at) }}</span>
            </template>
            <template v-else>{{ formatDocumentDate(doc.created_at) }}</template>
          </td>
          <td class="px-6 py-4" @click.stop>
            <BaseActionButton
              action="more"
              class="p-2.5 -m-1 rounded-lg hover:bg-surface-raised transition-colors text-text-subtle hover:text-text-default
                     outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/40"
              :label="`Acciones de ${doc.title}`"
              @click="emit('action', doc)"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
