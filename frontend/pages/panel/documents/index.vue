<template>
  <div class="flex flex-col min-h-full">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
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
      class="mb-5"
    />

    <div class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6 items-stretch flex-1">
      <FolderSidebar
        :folders="folderStore.rootFolders"
        :active-id="documentStore.activeFolderId"
        :total-count="documentStore.documents.length + otherFoldersCount"
        :is-dragging="!!draggingDoc"
        :dragging-folder-id="draggingFolder?.id ?? null"
        @select="handleSelectFolder"
        @create="openFolderManager"
        @manage="openFolderManager"
        @folder-drop="handleDropOnFolder"
      />

      <section class="min-w-0 flex flex-col">
        <FolderBreadcrumb
          v-if="documentStore.activeFolderId !== 'all'"
          :active-id="documentStore.activeFolderId"
          :dragging-folder-id="draggingFolder?.id ?? null"
          @select="handleSelectFolder"
          @nest="handleNestFolder"
        />

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

        <!-- Loading -->
        <DocumentListSkeleton v-if="documentStore.isLoading" :mode="viewMode" />

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
        <template v-else-if="hasContent">
          <DocumentsTable
            v-if="viewMode === 'list'"
            class="hidden sm:block"
            :documents="pagedDocuments"
            :subfolders="currentSubfolders"
            :dragging-doc-id="draggingDoc?.id ?? null"
            :drag-over-folder-id="dragOverFolderId"
            :newly-created-id="newlyCreatedId"
            @open="openDocument"
            @action="actionDoc = $event"
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
            @open="openDocument"
            @action="actionDoc = $event"
            @select-folder="handleSelectFolder"
            @doc-dragstart="handleDragStart"
            @doc-dragend="handleDragEnd"
            @folder-dragstart="handleFolderDragStart"
            @folder-dragend="handleFolderDragEnd"
            @folder-dragover="onFolderRowDragOver"
            @folder-dragleave="dragOverFolderId = null"
            @drop-on-folder="handleDropOnFolder"
          />
        </template>

        <!-- Pagination -->
        <BasePagination
          v-if="!documentStore.isLoading && !loadError && filteredDocuments.length > 0"
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
    />
    <TagManagerModal v-model="showTagManager" @changed="handleTagsChanged" />
    <MoveFolderModal v-model="showMoveModal" :document="movingDoc" @changed="handleMoved" />
    <RenameDocumentModal v-model="showRenameModal" :document="renamingDoc" @changed="handleRenamed" />
    <SendDocumentEmailModal v-model="showEmailModal" :document="emailingDoc" />
    <DocumentActionsSheet
      v-model="showActionsSheet"
      :document="actionDoc"
      @edit="handleEditDoc(actionDoc)"
      @rename="handleRenameDoc(actionDoc)"
      @move="handleMoveDoc(actionDoc)"
      @download-pdf="handleDownloadPdf(actionDoc)"
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
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import FolderSidebar from '~/components/panel/documents/FolderSidebar.vue';
import FolderBreadcrumb from '~/components/panel/documents/FolderBreadcrumb.vue';
import TagFilterChips from '~/components/panel/documents/TagFilterChips.vue';
import FolderManagerModal from '~/components/panel/documents/FolderManagerModal.vue';
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
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useDocumentViewMode } from '~/composables/useDocumentViewMode';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();

const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();
const { viewMode } = useDocumentViewMode();

const searchQuery = ref('');
const newlyCreatedId = ref(null);
let newlyCreatedTimer = null;
const filteredDocuments = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return documentStore.documents;
  return documentStore.documents.filter(
    (d) => d.title?.toLowerCase().includes(q) || d.client_name?.toLowerCase().includes(q),
  );
});

// Subcarpetas de la carpeta activa — solo cuando se navega dentro de una
// carpeta concreta y no hay búsqueda activa (la búsqueda aplica a documentos).
const currentSubfolders = computed(() => {
  const id = documentStore.activeFolderId;
  if (typeof id !== 'number') return [];
  if (searchQuery.value.trim()) return [];
  return folderStore.childrenOf(id);
});

const hasContent = computed(
  () => filteredDocuments.value.length > 0 || currentSubfolders.value.length > 0,
);

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
watch(() => documentStore.activeFolderId, () => docResetPage());
watch(() => documentStore.activeTagIds, () => docResetPage(), { deep: true });

const showFolderManager = ref(false);
const showTagManager = ref(false);
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

const createLink = computed(() => {
  const folder = documentStore.activeFolderId;
  if (folder && folder !== 'all' && folder !== 'none') {
    return localePath(`/panel/documents/create?folder=${folder}`);
  }
  return localePath('/panel/documents/create');
});

const otherFoldersCount = computed(() => {
  return folderStore.folders.reduce((sum, f) => sum + (f.document_count || 0), 0);
});

const loadError = ref(null);

async function loadDocuments() {
  loadError.value = null;
  const [docsResult] = await Promise.all([
    documentStore.fetchDocuments(),
    folderStore.fetchFolders(),
    tagStore.fetchTags(),
  ]);
  if (docsResult && !docsResult.success) {
    loadError.value = docsResult.message || 'No se pudieron cargar los documentos.';
  }
}

onMounted(loadDocuments);
usePanelRefresh(loadDocuments);

function handleSelectFolder(id) {
  documentStore.setFilters({ folder: id });
}

function handleToggleTag(id) {
  documentStore.toggleTagFilter(id);
}

function handleClearTagFilters() {
  documentStore.setFilters({ tags: [] });
}

function openFolderManager() {
  showFolderManager.value = true;
}

async function handleFoldersChanged() {
  await Promise.all([
    documentStore.fetchDocuments(),
    folderStore.fetchFolders(),
  ]);
}

async function handleTagsChanged() {
  await documentStore.fetchDocuments();
}

function handleMoveDoc(doc) {
  movingDoc.value = doc;
}

async function handleMoved() {
  await Promise.all([
    documentStore.fetchDocuments(),
    folderStore.fetchFolders(),
  ]);
}

function handleEditDoc(doc) {
  if (!doc) return;
  navigateTo(localePath(`/panel/documents/${doc.id}/edit`));
}

function openDocument(doc) {
  handleEditDoc(doc);
}

function editToFor(doc) {
  return localePath(`/panel/documents/${doc.id}/edit`);
}

function handleRenameDoc(doc) {
  renamingDoc.value = doc;
}

async function handleRenamed() {
  await documentStore.fetchDocuments();
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
    await Promise.all([documentStore.fetchDocuments(), folderStore.fetchFolders()]);
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
  if (doc.folder_id === folderId) return;
  const result = await documentStore.updateDocument(doc.id, { folder_id: folderId });
  if (result.success) {
    const folderName = folderStore.folderById(folderId)?.name;
    notify.success({ title: folderName ? `Documento movido a "${folderName}"` : 'Documento movido' });
  } else {
    notify.error({ title: 'No se pudo mover el documento', detail: result.message });
  }
  await Promise.all([documentStore.fetchDocuments(), folderStore.fetchFolders()]);
}

async function handleDownloadPdf(doc) {
  const result = await documentStore.downloadPdf(doc.id, doc.title || 'document');
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
  await documentStore.fetchDocuments();
  newlyCreatedId.value = result.data.id;
  newlyCreatedTimer = setTimeout(() => { newlyCreatedId.value = null; }, 2500);
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
  requestConfirm({
    title: 'Eliminar documento',
    message: `Se eliminará permanentemente "${doc.title}". Esta acción no se puede deshacer.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await documentStore.deleteDocument(doc.id);
      if (result.success) {
        notify.success({ title: 'Documento eliminado' });
      } else {
        notify.error({ title: 'No se pudo eliminar el documento', detail: result.message });
      }
    },
  });
}
</script>
