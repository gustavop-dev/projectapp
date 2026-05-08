<template>
  <div class="flex flex-col min-h-full">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <h1 class="text-2xl font-light text-text-default">Documentos</h1>
      <NuxtLink
        :to="createLink"
        class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl
               font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm
               dark:bg-primary-strong dark:hover:bg-primary"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Documento
      </NuxtLink>
    </div>

    <!-- Search bar -->
    <div class="relative mb-5">
      <svg class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Buscar por título o cliente..."
        class="w-full pl-10 pr-10 py-2.5 bg-surface border border-border-default rounded-xl text-sm text-text-default placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none shadow-sm transition-colors"
      />
      <button
        v-if="searchQuery"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded-full text-text-subtle hover:text-text-muted hover:bg-surface-raised transition-colors"
        @click="searchQuery = ''"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6 items-stretch flex-1">
      <FolderSidebar
        :folders="folderStore.folders"
        :active-id="documentStore.activeFolderId"
        :total-count="documentStore.documents.length + otherFoldersCount"
        :is-dragging="!!draggingDoc"
        @select="handleSelectFolder"
        @create="openFolderManager"
        @manage="openFolderManager"
        @folder-drop="handleDropOnFolder"
      />

      <section class="min-w-0 flex flex-col">
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
        <div v-if="documentStore.isLoading" class="text-center py-12 text-text-subtle text-sm">
          Cargando...
        </div>

        <div v-else-if="filteredDocuments.length === 0" class="text-center py-16 dark:text-text-subtle">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-surface-raised  flex items-center justify-center">
            <svg v-if="searchQuery" class="w-8 h-8 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <svg v-else class="w-8 h-8 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <template v-if="searchQuery">
            <p class="text-text-muted text-sm">
              No se encontraron documentos para "<span class="font-medium">{{ searchQuery }}</span>".
            </p>
            <button
              type="button"
              class="mt-3 text-sm text-text-brand hover:text-text-brand "
              @click="searchQuery = ''"
            >
              Limpiar búsqueda
            </button>
          </template>
          <template v-else>
            <p class="text-text-muted text-sm">No hay documentos todavia.</p>
            <NuxtLink
              :to="localePath('/panel/documents/create')"
              class="inline-flex items-center gap-1 mt-3 text-sm text-text-brand hover:text-text-brand "
            >
              Crear el primero →
            </NuxtLink>
          </template>
        </div>

        <!-- Desktop table -->
        <div v-if="!documentStore.isLoading && filteredDocuments.length > 0" class="hidden sm:block bg-surface rounded-xl shadow-sm border border-border-muted overflow-x-auto  ">
          <table class="w-full">
            <thead>
              <tr class="border-b border-border-muted text-left">
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Titulo</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Etiquetas</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Estado</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Creado</th>
                <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
              <tr
                v-for="doc in pagedDocuments"
                :key="doc.id"
                class="hover:bg-surface-muted dark:hover:bg-gray-700/50 transition-colors cursor-grab active:cursor-grabbing select-none"
                :class="[
                  { 'opacity-50': draggingDoc?.id === doc.id },
                  { 'bg-primary-soft transition-colors duration-1000': doc.id === newlyCreatedId }
                ]"
                draggable="true"
                @click="navigateTo(localePath(`/panel/documents/${doc.id}/edit`))"
                @dragstart="handleDragStart($event, doc)"
                @dragend="handleDragEnd"
              >
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-text-default truncate">{{ doc.title }}</span>
                    <span
                      v-if="doc.folder_name"
                      class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-surface-raised text-text-muted   flex-shrink-0"
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
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
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
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="statusBadgeClass(doc.status)"
                  >
                    {{ statusLabel(doc.status) }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-text-muted">
                  {{ formatDate(doc.created_at) }}
                </td>
                <td class="px-6 py-4" @click.stop>
                  <!-- md+ icons inline -->
                  <div class="hidden md:flex items-center gap-1">
                    <NuxtLink
                      :to="localePath(`/panel/documents/${doc.id}/edit`)"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-text-brand"
                      title="Editar contenido"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </NuxtLink>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-amber-600 dark:hover:text-amber-400"
                      title="Renombrar"
                      @click="handleRenameDoc(doc)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-violet-600 dark:hover:text-violet-400"
                      title="Mover a carpeta"
                      @click="handleMoveDoc(doc)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7zm13 1l3 3-3 3" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-text-brand"
                      title="Enviar por correo"
                      @click="handleSendEmail(doc)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-blue-600 dark:hover:text-blue-400"
                      title="Descargar PDF"
                      @click="handleDownloadPdf(doc)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-teal-600 dark:hover:text-teal-400"
                      :class="{ 'text-teal-600 dark:text-teal-400': copiedMarkdownId === doc.id }"
                      title="Copiar markdown"
                      @click="handleCopyMarkdown(doc.id)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-purple-600 dark:hover:text-purple-400"
                      title="Duplicar"
                      @click="handleDuplicate(doc.id)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors text-text-subtle hover:text-red-600 dark:hover:text-red-400"
                      title="Eliminar"
                      @click="handleDelete(doc)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                  <!-- <md kebab -->
                  <button
                    type="button"
                    class="md:hidden p-1.5 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-text-default"
                    title="Más acciones"
                    @click="actionDoc = doc"
                  >
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
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

        <!-- Mobile cards -->
        <div v-if="!documentStore.isLoading && filteredDocuments.length > 0" class="sm:hidden space-y-3">
          <div
            v-for="doc in pagedDocuments"
            :key="`mobile-${doc.id}`"
            class="bg-surface rounded-xl shadow-sm border border-border-muted p-4  "
            :class="{ 'bg-primary-soft transition-colors duration-1000': doc.id === newlyCreatedId }"
            @click="navigateTo(localePath(`/panel/documents/${doc.id}/edit`))"
          >
            <div class="flex items-start justify-between mb-2">
              <div class="flex-1 min-w-0">
                <h3 class="text-sm font-medium text-text-default truncate">{{ doc.title }}</h3>
                <p v-if="doc.client_name" class="text-xs text-text-subtle mt-0.5">{{ doc.client_name }}</p>
              </div>
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ml-2 flex-shrink-0"
                :class="statusBadgeClass(doc.status)"
              >
                {{ statusLabel(doc.status) }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-text-subtle">{{ formatDate(doc.created_at) }}</span>
              <div class="flex items-center" @click.stop>
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-surface-raised dark:hover:bg-gray-600 transition-colors text-text-subtle hover:text-text-default"
                  title="Más acciones"
                  @click="actionDoc = doc"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <circle cx="12" cy="5" r="1.6" />
                    <circle cx="12" cy="12" r="1.6" />
                    <circle cx="12" cy="19" r="1.6" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <BasePagination
          v-if="!documentStore.isLoading && filteredDocuments.length > 0"
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

    <FolderManagerModal v-model="showFolderManager" @changed="handleFoldersChanged" />
    <TagManagerModal v-model="showTagManager" @changed="handleTagsChanged" />
    <MoveFolderModal v-model="showMoveModal" :document="movingDoc" @changed="handleMoved" />
    <RenameDocumentModal v-model="showRenameModal" :document="renamingDoc" @changed="handleRenamed" />
    <SendDocumentEmailModal v-model="showEmailModal" :document="emailingDoc" />
    <DocumentActionsSheet
      v-model="showActionsSheet"
      :document="actionDoc"
      @rename="handleRenameDoc(actionDoc)"
      @move="handleMoveDoc(actionDoc)"
      @download-pdf="handleDownloadPdf(actionDoc)"
      @copy-markdown="handleCopyMarkdown(actionDoc.id)"
      @duplicate="handleDuplicate(actionDoc.id)"
      @send-email="handleSendEmail(actionDoc)"
      @delete="handleDelete(actionDoc)"
    />

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="deleteConfirm"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="deleteConfirm = null"
        >
          <div class="bg-surface rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center ">
            <div class="text-4xl mb-3">🗑️</div>
            <h3 class="text-lg font-bold text-text-default mb-2">Eliminar documento</h3>
            <p class="text-sm text-text-muted mb-6">
              Se eliminara permanentemente "{{ deleteConfirm.title }}". Esta accion no se puede deshacer.
            </p>
            <div class="flex gap-3 justify-center">
              <button
                class="px-6 py-2.5 bg-red-600 text-white rounded-xl font-medium text-sm hover:bg-red-700 transition-colors disabled:opacity-50"
                :disabled="documentStore.isUpdating"
                @click="confirmDelete"
              >
                {{ documentStore.isUpdating ? 'Eliminando...' : 'Eliminar' }}
              </button>
              <button
                class="px-6 py-2.5 bg-surface-raised text-text-muted rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors   dark:hover:bg-gray-600"
                @click="deleteConfirm = null"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import FolderSidebar from '~/components/panel/documents/FolderSidebar.vue';
import TagFilterChips from '~/components/panel/documents/TagFilterChips.vue';
import FolderManagerModal from '~/components/panel/documents/FolderManagerModal.vue';
import TagManagerModal from '~/components/panel/documents/TagManagerModal.vue';
import MoveFolderModal from '~/components/panel/documents/MoveFolderModal.vue';
import RenameDocumentModal from '~/components/panel/documents/RenameDocumentModal.vue';
import SendDocumentEmailModal from '~/components/panel/documents/SendDocumentEmailModal.vue';
import DocumentActionsSheet from '~/components/panel/documents/DocumentActionsSheet.vue';
import { tagBadgeClass, tagDotClass } from '~/utils/documentTagColors.js';
import BasePagination from '~/components/base/BasePagination.vue';
import { usePagination } from '~/composables/usePagination';
import { usePanelRefresh } from '~/composables/usePanelRefresh';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();

const searchQuery = ref('');
const newlyCreatedId = ref(null);
const copiedMarkdownId = ref(null);
let newlyCreatedTimer = null;
let copiedMarkdownTimer = null;
const filteredDocuments = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return documentStore.documents;
  return documentStore.documents.filter(
    (d) => d.title?.toLowerCase().includes(q) || d.client_name?.toLowerCase().includes(q),
  );
});

const {
  currentPage: docPage,
  totalPages: docTotalPages,
  totalItems: docTotalItems,
  rangeFrom: docRangeFrom,
  rangeTo: docRangeTo,
  paginatedItems: pagedDocuments,
  goTo: docGoTo,
  next: docNext,
  prev: docPrev,
  reset: docResetPage,
} = usePagination(filteredDocuments, { pageSize: 10 });

watch(searchQuery, () => docResetPage());
watch(() => documentStore.activeFolderId, () => docResetPage());
watch(() => documentStore.activeTagIds, () => docResetPage(), { deep: true });

const deleteConfirm = ref(null);
const showFolderManager = ref(false);
const showTagManager = ref(false);
const movingDoc = ref(null);
const renamingDoc = ref(null);
const emailingDoc = ref(null);
const actionDoc = ref(null);
const draggingDoc = ref(null);
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

async function loadDocuments() {
  await Promise.all([
    documentStore.fetchDocuments(),
    folderStore.fetchFolders(),
    tagStore.fetchTags(),
  ]);
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
  event.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd() {
  draggingDoc.value = null;
}

async function handleDropOnFolder(folderId) {
  if (!draggingDoc.value) return;
  const doc = draggingDoc.value;
  draggingDoc.value = null;
  if (doc.folder_id === folderId) return;
  await documentStore.updateDocument(doc.id, { folder_id: folderId });
  await Promise.all([documentStore.fetchDocuments(), folderStore.fetchFolders()]);
}

function statusBadgeClass(status) {
  const map = {
    draft: 'bg-surface-raised text-text-default ',
    published: 'bg-primary-soft text-text-brand ',
    archived: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  };
  return map[status] || map.draft;
}

function statusLabel(status) {
  const map = { draft: 'Borrador', published: 'Publicado', archived: 'Archivado' };
  return map[status] || status;
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' });
}

async function handleDownloadPdf(doc) {
  await documentStore.downloadPdf(doc.id, doc.title || 'document');
}

async function handleDuplicate(id) {
  const result = await documentStore.duplicateDocument(id);
  if (result.success) {
    clearTimeout(newlyCreatedTimer);
    await documentStore.fetchDocuments();
    newlyCreatedId.value = result.data.id;
    newlyCreatedTimer = setTimeout(() => { newlyCreatedId.value = null; }, 2500);
  }
}

async function handleCopyMarkdown(id) {
  const result = await documentStore.getDocumentMarkdown(id);
  if (!result.success) return;
  try {
    await navigator.clipboard.writeText(result.markdown);
    clearTimeout(copiedMarkdownTimer);
    copiedMarkdownId.value = id;
    copiedMarkdownTimer = setTimeout(() => { copiedMarkdownId.value = null; }, 1500);
  } catch {
    // clipboard unavailable or denied — no false feedback
  }
}

function handleDelete(doc) {
  deleteConfirm.value = doc;
}

async function confirmDelete() {
  if (!deleteConfirm.value) return;
  const result = await documentStore.deleteDocument(deleteConfirm.value.id);
  if (result.success) {
    deleteConfirm.value = null;
  }
}
</script>
