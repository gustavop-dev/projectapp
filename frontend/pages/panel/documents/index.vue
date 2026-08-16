<template>
  <div class="flex flex-col min-h-full">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4" data-enter>
      <div>
        <h1 class="text-2xl font-light text-text-default">Documentos</h1>
        <p class="text-sm text-text-subtle mt-1">Crea, organiza y comparte documentos con tu marca.</p>
      </div>
      <BaseButton as="NuxtLink" :to="createLink" variant="primary" class="shadow-sm">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Documento
      </BaseButton>
    </div>

    <!-- Toolbar: search + list/gallery toggle -->
    <DocumentsToolbar
      v-model:search="searchQuery"
      v-model:view-mode="viewMode"
      :scope="documentStore.archiveScope"
      :scope-locked="isSearching"
      class="mb-5"
      data-enter
      style="--enter-delay: 60ms"
      @update:scope="handleScopeChange"
    >
      <template v-if="isArchived && !isSearching" #actions>
        <BaseSegmented
          :model-value="archivedOrder"
          :options="ARCHIVED_ORDER_OPTIONS"
          size="sm"
          aria-label="Orden por fecha de archivado"
          @update:model-value="handleArchivedOrderChange"
        />
      </template>
    </DocumentsToolbar>

    <div class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6 items-stretch flex-1">
      <FolderSidebar
        data-enter
        style="--enter-delay: 120ms"
        :folders="sidebarFolders"
        :active-id="documentStore.activeFolderId"
        :archive-scope="documentStore.archiveScope"
        :total-count="sidebarTotalCount"
        :archived-count="documentStore.counts.documents.archived"
        :unfiled-count="sidebarUnfiledCount"
        :scope-locked="isSearching"
        :is-dragging="!!draggingDoc"
        :dragging-folder-id="draggingFolder?.id ?? null"
        @select="handleSelectFolder"
        @manage="openFolderManager"
        @folder-drop="handleDropOnFolder"
        @delete="handleDeleteFolder"
        @archive="handleArchiveFolder"
        @view-archived="handleViewArchivedFolder"
        @toggle-archived="handleToggleArchivedMode"
      />

      <section
        class="min-w-0 flex flex-col transition-colors"
        :class="isArchived ? 'rounded-xl bg-warning-soft p-3' : ''"
        data-enter
        style="--enter-delay: 180ms"
      >
        <!--
          Rótulo del ámbito, siempre visible mientras no sea el de reposo.
          Sin él, «Todos» con el modo encendido listaba archivados sin que nada
          en la vista lo dijera: se leían como documentos perdidos, y la única
          forma de recuperar la vista normal era editar la URL a mano.
        -->
        <div
          v-if="scopeNotice"
          class="mb-4 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg px-3 py-2 text-sm"
          :class="scopeNotice.tone"
          data-testid="doc-scope-banner"
        >
          <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          <span class="font-medium">{{ scopeNotice.label }}</span>
          <span class="text-text-muted">{{ scopeNotice.detail }}</span>
        </div>

        <FolderBreadcrumb
          v-if="showBreadcrumb"
          :active-id="documentStore.activeFolderId"
          :dragging-folder-id="draggingFolder?.id ?? null"
          :root-label="isArchived ? 'Archivados' : 'Todos'"
          :root-value="isArchived ? 'root' : 'all'"
          @select="handleSelectFolder"
          @nest="handleNestFolder"
        />

        <!-- La búsqueda ignora carpeta y estado: decirlo evita la lectura de
             que el filtro visible está acotando los resultados. -->
        <BaseAlert v-if="isSearching" variant="info" class="mb-4">
          Buscando «{{ searchQuery.trim() }}» en todo el gestor, activos y archivados.
        </BaseAlert>

        <!-- Parado DENTRO de una carpeta archivada: restaurar la carpeta
             completa vive aquí — las filas del listado solo restauran hijas.
             No depende del modo: apagarlo estando dentro deja al usuario en la
             misma carpeta (req 19), y ahí la salida tiene que seguir a la vista. -->
        <BaseAlert
          v-if="currentFolder?.is_archived"
          variant="info"
          class="mb-4"
          data-testid="current-folder-archived-alert"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <span>Estás dentro de una carpeta archivada.</span>
            <BaseButton
              variant="secondary"
              size="sm"
              :loading="folderStore.isUpdating"
              data-testid="doc-restore-current-folder"
              @click="handleUnarchiveFolder(currentFolder, { follow: true })"
            >
              Restaurar esta carpeta
            </BaseButton>
          </div>
        </BaseAlert>

        <!-- Tag filter chips -->
        <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-3 mb-4  " data-testid="doc-tag-filters">
          <TagFilterChips
            :tags="tagStore.tags"
            :active-ids="documentStore.activeTagIds"
            @toggle="handleToggleTag"
            @clear="handleClearTagFilters"
            @manage="showTagManager = true"
          />
        </div>

        <!-- Filtros de asociación (ocultos en búsqueda: la búsqueda es global
             y estos ejes no la acotan) -->
        <div
          v-if="!isSearching"
          class="bg-surface rounded-xl shadow-sm border border-border-muted p-3 mb-4"
          data-testid="doc-association-filters"
        >
          <DocumentsAssociationFilters
            :client="documentStore.activeClientId"
            :project="documentStore.activeProjectId"
            :client-label="associationClientLabel"
            @update:client="handleClientFilter"
            @update:project="handleProjectFilter"
          />
        </div>

        <!-- Loading -->
        <DocumentListSkeleton v-if="isListLoading" :mode="viewMode" />

        <!-- Load error (persistent: a toast would get lost) -->
        <BaseAlert
          v-else-if="loadError"
          variant="danger"
          title="No se pudieron cargar los documentos"
        >
          <p>{{ loadError }}</p>
          <div class="mt-3">
            <BaseButton variant="secondary" size="sm" @click="loadDocuments">Reintentar</BaseButton>
          </div>
        </BaseAlert>

        <!-- Empty states, one per context -->
        <BaseEmptyState
          v-else-if="!hasContent && searchQuery"
          title="Sin resultados"
          :description="`No se encontraron documentos para &quot;${searchQuery}&quot;.`"
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </template>
          <template #actions>
            <BaseButton variant="secondary" size="sm" @click="searchQuery = ''">Limpiar búsqueda</BaseButton>
          </template>
        </BaseEmptyState>
        <BaseEmptyState
          v-else-if="!hasContent && documentStore.activeTagIds.length > 0"
          title="Ningún documento coincide"
          description="Ningún documento tiene todas las etiquetas seleccionadas."
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </template>
          <template #actions>
            <BaseButton variant="secondary" size="sm" @click="handleClearTagFilters">Quitar filtros</BaseButton>
          </template>
        </BaseEmptyState>
        <!-- Una carpeta sin nada archivado tiene que decirlo por su nombre: el
             vacío genérico se leía como que la carpeta no existía en este modo. -->
        <BaseEmptyState
          v-else-if="!hasContent && isArchived && currentFolder"
          :title="`«${currentFolder.name}» no tiene nada archivado`"
          description="La carpeta sigue ahí y puede tener documentos activos. Apaga el modo archivado para verlos."
          data-testid="folder-archived-empty"
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          </template>
          <template #actions>
            <BaseButton variant="secondary" size="sm" @click="handleToggleArchivedMode(false)">
              Ver su contenido activo
            </BaseButton>
          </template>
        </BaseEmptyState>
        <BaseEmptyState
          v-else-if="!hasContent && isArchived"
          title="No hay nada archivado"
          description="Lo que archives saldrá de la vista principal y de los contadores, pero seguirá aquí."
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          </template>
          <template #actions>
            <BaseButton variant="secondary" size="sm" @click="handleBackToActive">
              Volver a los activos
            </BaseButton>
          </template>
        </BaseEmptyState>
        <!-- Con el modo apagado dentro de una carpeta archivada: ofrecer «crea un
             documento aquí» sería mandar al usuario a un 400, porque el backend
             no admite contenido activo bajo una carpeta archivada. -->
        <BaseEmptyState
          v-else-if="!hasContent && currentFolder?.is_archived"
          title="Esta carpeta está archivada"
          description="Su contenido salió de la vista principal. Restáurala para volver a trabajar aquí, o enciende el modo archivado para ver lo que guarda."
          data-testid="folder-archived-inactive-empty"
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          </template>
          <template #actions>
            <BaseButton variant="secondary" size="sm" @click="handleToggleArchivedMode(true)">
              Ver lo que guarda
            </BaseButton>
          </template>
        </BaseEmptyState>
        <BaseEmptyState
          v-else-if="!hasContent && documentStore.activeFolderId !== 'all'"
          title="Esta carpeta está vacía"
          description="Crea un documento aquí o arrastra uno desde otra carpeta."
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
            </svg>
          </template>
          <template #actions>
            <BaseButton as="NuxtLink" :to="createLink" variant="secondary" size="sm">Crear documento aquí</BaseButton>
          </template>
        </BaseEmptyState>
        <BaseEmptyState
          v-else-if="!hasContent"
          title="No hay documentos todavía"
          description="Crea tu primer documento desde markdown y descárgalo como PDF con tu marca."
        >
          <template #icon>
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </template>
          <template #actions>
            <BaseButton as="NuxtLink" :to="localePath('/panel/documents/create')" variant="primary" size="sm">
              Crear el primero
            </BaseButton>
          </template>
        </BaseEmptyState>

        <!-- Collection: table (list mode, desktop) / card grid -->
        <Transition v-else-if="hasContent" name="view-swap" mode="out-in">
          <div :key="viewMode">
          <DocumentsTable
            v-if="viewMode === 'list'"
            class="hidden sm:block"
            :documents="pagedDocuments"
            :subfolders="currentSubfolders"
            :edit-to-for="editToFor"
            :dragging-doc-id="draggingDoc?.id ?? null"
            :drag-over-folder-id="dragOverFolderId"
            :newly-created-id="newlyCreatedId"
            :scope="documentStore.archiveScope"
            :folder-summary="subfolderSummary"
            :updating="folderStore.isUpdating || documentStore.isUpdating"
            @open="openDocument"
            @action="actionDoc = $event"
            @unarchive-folder="handleUnarchiveFolder"
            @view-archived-folder="handleViewArchivedFolder"
            @select-folder="handleSelectFolder"
            @doc-dragstart="handleDragStart"
            @doc-dragend="handleDragEnd"
            @folder-dragstart="handleFolderDragStart"
            @folder-dragend="handleFolderDragEnd"
            @folder-dragover="onFolderRowDragOver"
            @folder-dragleave="dragOverFolderId = null"
            @drop-on-folder="handleDropOnFolder"
          />
          <!-- The grid IS the mobile view; on >=sm it appears in gallery mode -->
          <DocumentsGrid
            :class="viewMode === 'list' ? 'sm:hidden' : ''"
            :documents="pagedDocuments"
            :subfolders="currentSubfolders"
            :edit-to-for="editToFor"
            :dragging-doc-id="draggingDoc?.id ?? null"
            :drag-over-folder-id="dragOverFolderId"
            :newly-created-id="newlyCreatedId"
            :scope="documentStore.archiveScope"
            :folder-summary="subfolderSummary"
            :updating="folderStore.isUpdating || documentStore.isUpdating"
            @open="openDocument"
            @action="actionDoc = $event"
            @unarchive-folder="handleUnarchiveFolder"
            @view-archived-folder="handleViewArchivedFolder"
            @select-folder="handleSelectFolder"
            @doc-dragstart="handleDragStart"
            @doc-dragend="handleDragEnd"
            @folder-dragstart="handleFolderDragStart"
            @folder-dragend="handleFolderDragEnd"
            @folder-dragover="onFolderRowDragOver"
            @folder-dragleave="dragOverFolderId = null"
            @drop-on-folder="handleDropOnFolder"
          />
          </div>
        </Transition>

        <!-- Pagination -->
        <BasePagination
          v-if="!isListLoading && !loadError && filteredDocuments.length > 0"
          :current-page="docPage"
          :total-pages="docTotalPages"
          :total-items="docTotalItems"
          :range-from="docRangeFrom"
          :range-to="docRangeTo"
          class="mt-4"
          @prev="docPrev"
          @next="docNext"
          @go="docGoTo"
        />

      </section>
    </div>

    <FolderManagerModal
      v-model="showFolderManager"
      :initial-parent="typeof documentStore.activeFolderId === 'number' ? documentStore.activeFolderId : null"
      @changed="handleFoldersChanged"
      @archived="handleFolderArchived"
    />
    <DeleteFolderModal
      v-model="showDeleteFolderModal"
      :folder="deletingFolder"
      @deleted="handleFolderDeleted"
      @archived="handleFolderArchived"
    />
    <TagManagerModal v-model="showTagManager" @changed="handleTagsChanged" />
    <MoveFolderModal v-model="showMoveModal" :document="movingDoc" @changed="handleMoved" />
    <RenameDocumentModal v-model="showRenameModal" :document="renamingDoc" @changed="handleRenamed" />
    <SendDocumentEmailModal v-model="showEmailModal" :document="emailingDoc" />
    <DocumentActionsSheet
      v-model="showActionsSheet"
      :document="actionDoc"
      :archived="!!actionDoc?.is_archived"
      :edit-to="editToFor(actionDoc)"
      @archive="handleArchiveDoc(actionDoc)"
      @unarchive="handleUnarchiveDoc(actionDoc)"
      @edit="handleEditDoc(actionDoc)"
      @rename="handleRenameDoc(actionDoc)"
      @move="handleMoveDoc(actionDoc)"
      @download-pdf="(tpl) => handleDownloadPdf(actionDoc, tpl)"
      @copy-markdown="handleCopyMarkdown(actionDoc.id)"
      @duplicate="handleDuplicate(actionDoc.id)"
      @send-email="handleSendEmail(actionDoc)"
      @delete="handleDelete(actionDoc)"
    />

    <!-- Delete confirmation modal -->
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      :require-type-text="confirmState.requireTypeText"
      :secondary-text="confirmState.secondaryText"
      :secondary-variant="confirmState.secondaryVariant"
      :secondary-hint="confirmState.secondaryHint"
      :loading="confirmState.busy"
      @confirm="handleConfirmed"
      @secondary="handleSecondaryAction"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import FolderSidebar from '~/components/panel/documents/FolderSidebar.vue';
import FolderBreadcrumb from '~/components/panel/documents/FolderBreadcrumb.vue';
import TagFilterChips from '~/components/panel/documents/TagFilterChips.vue';
import DocumentsAssociationFilters from '~/components/panel/documents/DocumentsAssociationFilters.vue';
import FolderManagerModal from '~/components/panel/documents/FolderManagerModal.vue';
import DeleteFolderModal from '~/components/panel/documents/DeleteFolderModal.vue';
import TagManagerModal from '~/components/panel/documents/TagManagerModal.vue';
import MoveFolderModal from '~/components/panel/documents/MoveFolderModal.vue';
import RenameDocumentModal from '~/components/panel/documents/RenameDocumentModal.vue';
import SendDocumentEmailModal from '~/components/panel/documents/SendDocumentEmailModal.vue';
import DocumentActionsSheet from '~/components/panel/documents/DocumentActionsSheet.vue';
import DocumentListSkeleton from '~/components/panel/documents/DocumentListSkeleton.vue';
import DocumentsToolbar from '~/components/panel/documents/DocumentsToolbar.vue';
import DocumentsTable from '~/components/panel/documents/DocumentsTable.vue';
import DocumentsGrid from '~/components/panel/documents/DocumentsGrid.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePagination } from '~/composables/usePagination';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { isRootInScope, treeScopeFor } from '~/utils/archiveScope';
import { folderSummaryFrom, scopedCounts } from '~/utils/documentStatus';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useDocumentViewMode } from '~/composables/useDocumentViewMode';
import { useDocumentFilterQuery } from '~/composables/useDocumentFilterQuery';
import { useReducedMotion } from '~/composables/useReducedMotion';
import { useRowNavigation } from '~/composables/useRowNavigation';

const localePath = useLocalePath();
const { openRow } = useRowNavigation();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();

const notify = usePanelNotify();
const {
  confirmState, requestConfirm,
  handleConfirmed, handleSecondaryAction, handleCancelled,
} = useConfirmModal();
const { viewMode } = useDocumentViewMode();
const { reducedMotion } = useReducedMotion();

const searchQuery = ref('');
const newlyCreatedId = ref(null);
let newlyCreatedTimer = null;
// El estado es un eje propio: `activeFolderId` dice DÓNDE ('all' | 'root' |
// 'none' | id) y `archiveScope` dice EN QUÉ ESTADO. Antes compartían campo, y
// por eso no se podía entrar a una carpeta archivada ni filtrar dentro de ella.
const isArchived = computed(() => documentStore.archiveScope === 'archived');
const isSearching = computed(() => searchQuery.value.trim().length > 0);
const archivedOrder = computed(() => documentStore.archivedOrder);
const ARCHIVED_ORDER_OPTIONS = [
  { value: 'recent', label: 'Recientes', testId: 'archived-order-recent' },
  { value: 'oldest', label: 'Más antiguos', testId: 'archived-order-oldest' },
];

const showBreadcrumb = computed(
  () => !isSearching.value
    && documentStore.activeFolderId !== 'all'
    && !(documentStore.activeFolderId === 'root' && !isArchived.value),
);

const currentFolder = computed(() => (
  typeof documentStore.activeFolderId === 'number'
    ? folderStore.folderById(documentStore.activeFolderId)
    : null
));

// ── El panel lateral sigue al modo ───────────────────────────────────────────
// Antes listaba siempre el árbol activo con contadores de activos, incluso con
// el archivo encendido: una carpeta archivada entera no aparecía por ningún
// lado y «Todos» decía un número mientras el listado mostraba otro.
//
// `treeScopeFor` es la MISMA regla con que el rollup decide por qué carpetas
// puede bajar. Importarla en los dos sitios es lo que garantiza que la suma de
// las filas más «Sin carpeta» dé exactamente «Todos»: las raíces que se listan
// y los subárboles que se suman son la misma partición del árbol.
const treeScope = computed(() => treeScopeFor(documentStore.archiveScope));

const sidebarFolders = computed(() => folderStore.scopedRootFolders(treeScope.value));

// Los tres modos, no dos: con 'all' el listado mezcla los dos estados y las
// filas de carpeta ya sumaban ambos, así que un total de sólo activos decía
// menos que la suma de sus propias carpetas.
const sidebarTotalCount = computed(() => {
  const { active, archived } = documentStore.counts.documents;
  if (documentStore.archiveScope === 'archived') return archived;
  if (documentStore.archiveScope === 'all') return active + archived;
  return active;
});

const sidebarUnfiledCount = computed(() => {
  const { unfiled_active: unfiledActive, unfiled_archived: unfiledArchived } = documentStore.counts.documents;
  if (documentStore.archiveScope === 'archived') return unfiledArchived;
  if (documentStore.archiveScope === 'all') return unfiledActive + unfiledArchived;
  return unfiledActive;
});

// El ámbito en palabras. 'active' es el estado de reposo y no lleva rótulo:
// anunciar lo normal entrena a ignorar el aviso que sí importa.
const SCOPE_NOTICES = {
  archived: {
    label: 'Modo archivado',
    detail: 'Estás viendo lo archivado; los contadores del panel cuentan archivados.',
    // Sólido sobre el panel teñido: repetir el tinte lo volvería invisible.
    tone: 'bg-surface text-text-default',
  },
  all: {
    label: 'Activos y archivados',
    detail: 'La lista mezcla los dos estados; cada fila declara el suyo.',
    tone: 'bg-info-soft text-text-default',
  },
};

const scopeNotice = computed(() => SCOPE_NOTICES[documentStore.archiveScope] || null);

const filteredDocuments = computed(() => {
  if (isSearching.value) return documentStore.searchResults;
  if (documentStore.activeFolderId !== 'root') return documentStore.documents;
  // En la cima del árbol sólo se listan los documentos que no cuelgan de una
  // carpeta visible: los demás se ven entrando a su carpeta.
  return documentStore.documents.filter(
    (d) => isRootInScope(d.folder, folderStore.folderById, documentStore.archiveScope),
  );
});

// Filas de carpeta del listado: las raíces del scope en la cima, las hijas
// dentro de una carpeta, y las coincidencias mientras se busca.
const currentSubfolders = computed(() => {
  if (isSearching.value) return searchFolders.value;
  const id = documentStore.activeFolderId;
  if (id === 'root') return folderStore.scopedRootFolders(documentStore.archiveScope);
  if (typeof id !== 'number') return [];
  return folderStore.childrenOf(id, documentStore.archiveScope);
});

const hasContent = computed(
  () => filteredDocuments.value.length > 0 || currentSubfolders.value.length > 0,
);

/**
 * Inventario de una fila de subcarpeta del listado.
 *
 * Es el mismo defecto del panel lateral un clic más adentro: entrar a «Familia»
 * y ver sus tres subcarpetas diciendo «Vacía» cuando entre las tres guardan 12.
 * Los documentos se cuentan del subárbol; las subcarpetas siguen siendo las
 * directas, que es lo que la fila promete si se hace clic.
 */
function subfolderSummary(folder, scope) {
  const { docs } = folderStore.rollupOf(folder, scope);
  return folderSummaryFrom({ docs, subs: scopedCounts(folder, scope).subs });
}

const {
  currentPage: docPage,
  pageSize: docPageSize,
  totalPages: docTotalPages,
  totalItems: docTotalItems,
  rangeFrom: docRangeFrom,
  rangeTo: docRangeTo,
  paginatedItems: pagedDocuments,
  goTo: docGoTo,
  next: docNext,
  prev: docPrev,
  reset: docResetPage,
} = usePagination(filteredDocuments, { pageSize: viewMode.value === 'grid' ? 12 : 10 });

// 12 divides evenly into the 2/3/4-column grid; 10 matches the table rhythm.
watch(viewMode, (mode) => {
  docPageSize.value = mode === 'grid' ? 12 : 10;
  docResetPage();
});

watch(searchQuery, () => docResetPage());
watch(archivedOrder, () => docResetPage());
watch(() => documentStore.activeFolderId, () => docResetPage());
watch(() => documentStore.archiveScope, () => docResetPage());
watch(() => documentStore.activeTagIds, () => docResetPage(), { deep: true });

// ── Búsqueda global ──────────────────────────────────────────────────────────
// Recorre todo el gestor y los dos estados: buscar sirve para encontrar algo
// cuya ubicación no se recuerda, y acotarlo a la vista era justo lo que impedía
// dar con lo archivado.
const searchFolders = ref([]);
const scopeBeforeSearch = ref(null);
const scopeTouchedDuringSearch = ref(false);
let searchTimer = null;

async function runSearch(term) {
  const [docs, folders] = await Promise.all([
    documentStore.searchDocuments(term),
    folderStore.searchFolders(term),
  ]);
  searchFolders.value = folders.data || [];
  if (!docs.success) {
    notify.error({ title: 'No se pudo completar la búsqueda', detail: docs.message });
  }
}

watch(searchQuery, (value) => {
  const term = value.trim();
  clearTimeout(searchTimer);
  if (!term) {
    searchFolders.value = [];
    documentStore.isSearchLoading = false;
    // Al limpiar se devuelve el control a donde estaba, salvo que el usuario lo
    // haya movido él mismo mientras buscaba: ahí manda su elección.
    if (scopeBeforeSearch.value && !scopeTouchedDuringSearch.value) {
      documentStore.setFilters({ scope: scopeBeforeSearch.value });
    }
    scopeBeforeSearch.value = null;
    scopeTouchedDuringSearch.value = false;
    return;
  }
  if (!scopeBeforeSearch.value) {
    scopeBeforeSearch.value = documentStore.archiveScope;
    scopeTouchedDuringSearch.value = false;
    // El control se mueve a la vista: la búsqueda ensancha el eje, y dejarlo en
    // «Solo activos» mientras devuelve archivados sería una interfaz mentirosa.
    if (documentStore.archiveScope !== 'all') documentStore.archiveScope = 'all';
  }
  // Los resultados de la búsqueda anterior no sobreviven al debounce: verlos
  // mientras se escribe otro término los hace pasar por resultados nuevos.
  documentStore.searchResults = [];
  searchFolders.value = [];
  documentStore.isSearchLoading = true;
  searchTimer = setTimeout(() => runSearch(term), 300);
});

/**
 * Sale de la búsqueda y navega en un solo gesto.
 *
 * El watcher de `searchQuery` restaura el scope previo al limpiar (flush pre,
 * corre DESPUÉS de este handler): anular `scopeBeforeSearch` antes de vaciar el
 * término convierte esa rama en no-op y el destino de la navegación sobrevive.
 * Nunca "reordenar" las líneas como fix — es exactamente lo que fallaba.
 */
function exitSearchAndNavigate({ folder, scope } = {}) {
  clearTimeout(searchTimer);
  const targetScope = scope
    ?? ((scopeTouchedDuringSearch.value || !scopeBeforeSearch.value)
      ? documentStore.archiveScope
      : scopeBeforeSearch.value);
  scopeBeforeSearch.value = null;
  scopeTouchedDuringSearch.value = false;
  searchFolders.value = [];
  documentStore.isSearchLoading = false;
  searchQuery.value = '';
  return documentStore.setFilters({ folder, scope: targetScope });
}

onBeforeUnmount(() => {
  clearTimeout(searchTimer);
  clearTimeout(newlyCreatedTimer);
});

const showFolderManager = ref(false);
const showTagManager = ref(false);
const deletingFolder = ref(null);
const movingDoc = ref(null);
const renamingDoc = ref(null);
const emailingDoc = ref(null);
const actionDoc = ref(null);
const draggingDoc = ref(null);
const draggingFolder = ref(null);
const dragOverFolderId = ref(null);
const showMoveModal = computed({
  get: () => !!movingDoc.value,
  set: (v) => { if (!v) movingDoc.value = null; },
});
const showRenameModal = computed({
  get: () => !!renamingDoc.value,
  set: (v) => { if (!v) renamingDoc.value = null; },
});
const showEmailModal = computed({
  get: () => !!emailingDoc.value,
  set: (v) => { if (!v) emailingDoc.value = null; },
});
const showActionsSheet = computed({
  get: () => !!actionDoc.value,
  set: (v) => { if (!v) actionDoc.value = null; },
});
const showDeleteFolderModal = computed({
  get: () => !!deletingFolder.value,
  set: (v) => { if (!v) deletingFolder.value = null; },
});

const createLink = computed(() => {
  const folder = documentStore.activeFolderId;
  if (folder && folder !== 'all' && folder !== 'none') {
    return localePath(`/panel/documents/create?folder=${folder}`);
  }
  return localePath('/panel/documents/create');
});

// La búsqueda comparte el skeleton de la lista: sin esto no tenía ningún
// indicador de carga y los 300 ms de debounce parecían un buscador roto.
const isListLoading = computed(
  () => documentStore.isLoading || documentStore.isSearchLoading,
);

const loadError = ref(null);

/**
 * Única ruta de refresco de la vista.
 *
 * Antes cada handler decidía qué refetchear, y por eso los contadores del panel
 * lateral quedaban desactualizados según por dónde se hubiera archivado. Con un
 * solo camino, ningún handler puede olvidarse de una de las tres piezas.
 */
async function refreshView({ tags = false } = {}) {
  loadError.value = null;
  const [docsResult] = await Promise.all([
    documentStore.fetchDocuments({ scope: documentStore.archiveScope }),
    folderStore.fetchFolders(),
    documentStore.fetchCounts(),
    tags ? tagStore.fetchTags() : Promise.resolve(),
  ]);
  if (docsResult && !docsResult.success) {
    loadError.value = docsResult.message || 'No se pudieron cargar los documentos.';
  }
  if (isSearching.value) await runSearch(searchQuery.value.trim());
}

function loadDocuments() {
  return refreshView({ tags: true });
}

// Carpeta y scope viven en la URL (?folder=&scope=): F5 y los deep links
// reconstruyen la vista. El query se aplica ANTES del primer fetch.
const filterQuery = useDocumentFilterQuery(documentStore, {
  isSearching,
  // Atrás/adelante cambian carpeta y estado, no el árbol ni los contadores:
  // basta con volver a pedir la lista, igual que al navegar por el panel.
  onNavigate: () => documentStore.fetchDocuments({ scope: documentStore.archiveScope }),
});

onMounted(async () => {
  filterQuery.applyQueryToStore();
  await loadDocuments();
  // La carpeta del deep link ya no existe: se cae a Todos y se refetchea.
  if (filterQuery.validateFolder(folderStore)) {
    await documentStore.fetchDocuments({ scope: documentStore.archiveScope });
  }
});
usePanelRefresh(loadDocuments);

function handleSelectFolder(id) {
  if (isSearching.value) {
    // Elegir una carpeta en plena búsqueda es navegación: se sale de la
    // búsqueda hacia esa carpeta. Antes el filtro cambiaba por debajo y la
    // vista seguía mostrando los resultados, como si el clic no hiciera nada.
    exitSearchAndNavigate({ folder: id });
    return;
  }
  // Navegar entre carpetas NO toca el estado: el control de la barra dice qué
  // se está viendo y cambiarlo por debajo lo volvería mentiroso.
  documentStore.setFilters({ folder: id });
}

/** Devuelve los dos ejes a su posición de reposo. */
function handleBackToActive() {
  documentStore.setFilters({ folder: 'all', scope: 'active' });
}

/**
 * Enciende y apaga el modo archivado.
 *
 * Cambiar de ámbito no mueve al usuario de sitio: dentro de una carpeta se
 * queda en ella y sólo cambia lo que se lista. Las dos vistas de cima sí se
 * traducen una en otra, porque no son la misma en cada ámbito: «Todos» es la
 * lista plana de activos y el archivo se recorre como árbol desde su raíz, que
 * es lo que conserva las carpetas como contenedores en vez de aplanarlas junto
 * a sus documentos.
 */
function handleToggleArchivedMode(on) {
  const folderId = documentStore.activeFolderId;
  let folder;
  if (on && folderId === 'all') folder = 'root';
  if (!on && folderId === 'root') folder = 'all';
  documentStore.setFilters({ folder, scope: on ? 'archived' : 'active' });
}

/** Entra a la carpeta en su scope archivado — el destino de la insignia. */
function handleViewArchivedFolder(folder) {
  if (!folder) return;
  exitSearchAndNavigate({ folder: folder.id, scope: 'archived' });
}

function handleScopeChange(scope) {
  if (isSearching.value) scopeTouchedDuringSearch.value = true;
  documentStore.setFilters({ scope });
}

function handleArchivedOrderChange(order) {
  documentStore.setFilters({ order });
}

async function handleArchiveDoc(doc) {
  if (!doc) return;
  const result = await documentStore.archiveDocument(doc.id);
  if (result.success) {
    notify.success({ title: 'Documento archivado' });
    await refreshView();
  } else {
    notify.error({ title: 'No se pudo archivar el documento', detail: result.message });
  }
}

async function handleUnarchiveDoc(doc) {
  if (!doc) return;
  const result = await documentStore.unarchiveDocument(doc.id);
  if (result.success) {
    notify.success({
      title: 'Documento restaurado',
      detail: restoredChainDetail(result),
    });
    await refreshView();
  } else {
    notify.error({ title: 'No se pudo restaurar el documento', detail: result.message });
  }
}

/**
 * Explica la carpeta que volvió con el elemento.
 *
 * Restaurar reabre la cadena contenedora, y sin decirlo el usuario ve reaparecer
 * una carpeta que él había archivado sin entender por qué.
 */
function restoredChainDetail(result) {
  if (result.movedToRoot) {
    return 'No se pudo reconstruir su carpeta, así que quedó en «Sin carpeta».';
  }
  const chain = result.restoredChain || [];
  if (!chain.length) return undefined;
  const names = chain.map((f) => `«${f.name}»`).join(' › ');
  return `Se restauró también ${names} para que tenga dónde volver.`;
}

async function handleUnarchiveFolder(folder, { follow = false } = {}) {
  if (!folder) return;
  const result = await folderStore.unarchiveFolder(folder.id);
  if (result.success) {
    // Se reporta el conteo que devuelve la API, nunca "todo su contenido":
    // lo archivado a mano se queda archivado a propósito.
    const restored = result.restoredDocuments;
    const chainDetail = restoredChainDetail(result);
    const details = [
      restored ? `Se restauraron ${restored} documento(s) que archivó esta carpeta.` : null,
      chainDetail,
    ].filter(Boolean);
    notify.success({
      title: 'Carpeta restaurada',
      detail: details.length ? details.join(' ') : undefined,
    });
    // Seguir la restauración: la carpeta vuelve a los activos y la vista va
    // con ella, en vez de quedarse mirando su hueco en Archivados.
    if (follow) documentStore.archiveScope = 'active';
    await refreshView();
  } else {
    notify.error({
      title: 'No se pudo restaurar la carpeta',
      detail: result.message,
    });
  }
}

function handleArchiveFolder(folder) {
  if (!folder) return;
  requestConfirm({
    title: `Archivar "${folder.name}"`,
    // El aviso tiene que nombrar lo que la cascada se va a llevar, que es todo
    // el subárbol y no sólo lo que cuelga directo: archivar Vastago avisaba
    // «1 documento» antes de arrastrar 36.
    message: `Se archivará junto con su contenido (${folderSummaryFrom(folderStore.cascadeContentOf(folder))}). `
      + 'Sale de la vista y de los contadores, pero podrás restaurarla cuando quieras.',
    variant: 'warning',
    confirmText: 'Archivar',
    waitForConfirm: true,
    onConfirm: async () => {
      const result = await folderStore.archiveFolder(folder.id);
      if (!result.success) {
        notify.error({ title: 'No se pudo archivar la carpeta', detail: result.message });
        return;
      }
      notify.success({
        title: 'Carpeta archivada',
        detail: result.archivedDocuments
          ? `Se archivaron también ${result.archivedDocuments} documento(s).`
          : undefined,
      });
      exitFolderIfViewing(folder);
      await refreshView();
    },
  });
}

/**
 * ¿La vista actual está parada en esta carpeta o en una descendiente?
 *
 * El check de identidad se quedaba corto: archivar un ancestro desde el
 * sidebar dejaba al usuario dentro de una descendiente recién archivada,
 * viendo un empty state falso en una carpeta fantasma.
 */
function isViewingFolderOrDescendant(folderId) {
  const active = documentStore.activeFolderId;
  if (typeof active !== 'number') return false;
  return active === folderId || folderStore.descendantIdsOf(folderId).has(active);
}

/** Destino al retirarse de una carpeta que dejó de existir: su padre, o Todos. */
function folderExitTarget(folder) {
  return folder?.parent ?? 'all';
}

/**
 * Retira la vista ANTES del refreshView del caller: la escritura directa no
 * dispara fetch propio, así el refresco llega ya apuntando al destino y no
 * parpadea un empty state falso de la carpeta que acaba de irse.
 */
function exitFolderIfViewing(folder) {
  if (folder && isViewingFolderOrDescendant(folder.id)) {
    documentStore.activeFolderId = folderExitTarget(folder);
  }
}

function handleToggleTag(id) {
  documentStore.toggleTagFilter(id);
}

function handleClearTagFilters() {
  documentStore.setFilters({ tags: [] });
}

function handleClientFilter(value) {
  documentStore.setFilters({ client: value });
}

function handleProjectFilter(value) {
  documentStore.setFilters({ project: value });
}

// Label para rehidratar el autocomplete en un deep link (?client=<id>): se
// resuelve de las filas ya cargadas para no gastar un fetch extra; sin filas
// el fallback numérico al menos dice QUÉ filtro está puesto.
const associationClientLabel = computed(() => {
  const id = documentStore.activeClientId;
  if (typeof id !== 'number') return '';
  const row = documentStore.documents.find((d) => d.client === id);
  return row?.client_display_name || `Cliente #${id}`;
});

function openFolderManager() {
  showFolderManager.value = true;
}

function handleDeleteFolder(folder) {
  if (!folder) return;
  deletingFolder.value = folder;
}

async function handleFolderArchived({ folder, documents } = {}) {
  notify.success({
    title: 'Carpeta archivada',
    detail: documents
      ? `Se archivaron también ${documents} documento(s).`
      : undefined,
  });
  exitFolderIfViewing(folder);
  await refreshView();
}

async function handleFolderDeleted(folder) {
  notify.success({ title: 'Carpeta eliminada' });
  // La carpeta borrada era el filtro activo: no queda vista que mostrar.
  exitFolderIfViewing(folder);
  await refreshView();
}

function handleFoldersChanged() {
  return refreshView();
}

function handleTagsChanged() {
  return refreshView({ tags: true });
}

function handleMoveDoc(doc) {
  movingDoc.value = doc;
}

function handleMoved() {
  return refreshView();
}

// Fuente única de la dirección: la lee el <a> del título de cada fila/tarjeta
// y la lee el atajo de clic, así que no pueden apuntar a lugares distintos.
function editToFor(doc) {
  return doc ? localePath(`/panel/documents/${doc.id}/edit`) : null;
}

function handleEditDoc(doc) {
  openRow(editToFor(doc));
}

// El evento decide: clic simple navega acá, ctrl/cmd o rueda abren pestaña
// nueva, y un clic nacido en un control de la fila no navega en absoluto.
function openDocument(doc, event) {
  openRow(editToFor(doc), event);
}

function handleRenameDoc(doc) {
  renamingDoc.value = doc;
}

function handleRenamed() {
  return refreshView();
}

function handleSendEmail(doc) {
  emailingDoc.value = doc;
}

function handleDragStart(event, doc) {
  draggingDoc.value = doc;
  // Sin setData, Firefox no inicia el drag nativo (no dispara dragover/drop).
  event.dataTransfer.setData('text/plain', `doc:${doc.id}`);
  event.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd() {
  draggingDoc.value = null;
}

function handleFolderDragStart(event, folder) {
  draggingFolder.value = folder;
  event.dataTransfer.setData('text/plain', `folder:${folder.id}`);
  event.dataTransfer.effectAllowed = 'move';
}

function handleFolderDragEnd() {
  draggingFolder.value = null;
  dragOverFolderId.value = null;
}

// ¿La carpeta en arrastre puede soltarse sobre este destino sin crear un ciclo?
function canDropFolderOn(destId) {
  const folder = draggingFolder.value;
  if (!folder) return false;
  if (destId === folder.id) return false;
  if (destId != null && folderStore.descendantIdsOf(folder.id).has(destId)) return false;
  // Soltar algo activo dentro de una carpeta archivada lo dejaría sin ubicación
  // alcanzable; el backend además lo rechaza con 400.
  if (destId != null && folderStore.folderById(destId)?.is_archived) return false;
  return true;
}

function onFolderRowDragOver(event, folderId) {
  if (draggingDoc.value || canDropFolderOn(folderId)) {
    event.preventDefault();
    dragOverFolderId.value = folderId;
  }
}

// Reasigna el padre de una carpeta (drag-to-nest). destId null = carpeta raíz.
async function reparentFolder(folder, destId) {
  if (!folder) return;
  if (destId === folder.id) return;
  if (destId != null && folderStore.descendantIdsOf(folder.id).has(destId)) return;
  if ((folder.parent ?? null) === (destId ?? null)) return;
  const result = await folderStore.updateFolder(folder.id, { parent: destId });
  if (result.success) {
    await refreshView();
  } else {
    notify.error({ title: 'No se pudo mover la carpeta' });
  }
}

function handleNestFolder({ destId, draggedFolderId }) {
  draggingFolder.value = null;
  dragOverFolderId.value = null;
  return reparentFolder(folderStore.folderById(draggedFolderId), destId);
}

async function handleDropOnFolder(folderId) {
  dragOverFolderId.value = null;
  const folder = draggingFolder.value;
  if (folder) {
    draggingFolder.value = null;
    await reparentFolder(folder, folderId);
    return;
  }
  if (!draggingDoc.value) return;
  const doc = draggingDoc.value;
  draggingDoc.value = null;
  if (doc.folder === folderId) return;
  const result = await documentStore.updateDocument(doc.id, { folder_id: folderId });
  if (result.success) {
    const folderName = folderStore.folderById(folderId)?.name;
    notify.success({ title: folderName ? `Documento movido a "${folderName}"` : 'Documento movido' });
  } else {
    notify.error({ title: 'No se pudo mover el documento', detail: result.message });
  }
  await refreshView();
}

async function handleDownloadPdf(doc, template = null) {
  const result = await documentStore.downloadPdf(doc.id, doc.title || 'document', template);
  if (!result.success) {
    notify.error({ title: 'No se pudo descargar el PDF', detail: result.message });
  }
}

async function handleDuplicate(id) {
  const result = await documentStore.duplicateDocument(id);
  if (!result.success) {
    notify.error({ title: 'No se pudo duplicar el documento', detail: result.message });
    return;
  }
  notify.success({ title: 'Documento duplicado' });
  clearTimeout(newlyCreatedTimer);
  await refreshView();
  docResetPage();
  newlyCreatedId.value = result.data.id;
  newlyCreatedTimer = setTimeout(() => { newlyCreatedId.value = null; }, 2500);
  // The duplicate lands at the top of the list; bring it into view.
  window.scrollTo({ top: 0, behavior: reducedMotion.value ? 'auto' : 'smooth' });
}

async function handleCopyMarkdown(id) {
  const result = await documentStore.getDocumentMarkdown(id);
  if (!result.success) {
    notify.error({ title: 'No se pudo obtener el markdown', detail: result.message });
    return;
  }
  try {
    await navigator.clipboard.writeText(result.markdown);
    notify.success('Markdown copiado al portapapeles');
  } catch {
    notify.error({
      title: 'No se pudo copiar al portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}

function handleDelete(doc) {
  if (!doc) return;
  // Ya archivado: no hay salida alternativa que ofrecer.
  const alreadyArchived = !!doc.is_archived;
  requestConfirm({
    title: 'Eliminar documento',
    message: `Se eliminará permanentemente "${doc.title}". Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    requireTypeText: 'DELETE',
    secondaryText: alreadyArchived ? '' : 'Archivar en su lugar',
    secondaryHint: alreadyArchived
      ? ''
      : 'Archivar lo saca de la lista y de los contadores, pero lo conserva: podrás consultarlo o restaurarlo desde Archivados.',
    onSecondary: () => handleArchiveDoc(doc),
    waitForConfirm: true,
    onConfirm: async () => {
      const result = await documentStore.deleteDocument(doc.id);
      if (result.success) {
        notify.success({ title: 'Documento eliminado' });
      } else {
        notify.error({ title: 'No se pudo eliminar el documento', detail: result.message });
      }
      // También al eliminar: los contadores de carpeta salen del backend y sin
      // esto la fila desaparece pero el número de al lado se queda viejo.
      await refreshView();
    },
  });
}
</script>

<style scoped>
/* Staggered fade-up entrance, CSS-driven like the accounting dashboard:
 * the list loads async, so the animation must not depend on JS timing. */
@keyframes documents-enter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
}
[data-enter] {
  animation: documents-enter 0.45s ease-out both;
  animation-delay: var(--enter-delay, 0ms);
}

/* List <-> gallery swap: quick fade + settle, out-in so layouts never overlap. */
.view-swap-enter-active,
.view-swap-leave-active {
  transition: opacity 150ms cubic-bezier(0.22, 1, 0.36, 1),
              transform 150ms cubic-bezier(0.22, 1, 0.36, 1);
}
.view-swap-enter-from,
.view-swap-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  [data-enter] {
    animation: none;
  }
  .view-swap-enter-active,
  .view-swap-leave-active {
    transition: none;
  }
}
</style>
