<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Documentos</h1>
      <NuxtLink
        :to="localePath('/panel/documents/create')"
        class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
               font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm
               dark:bg-emerald-700 dark:hover:bg-emerald-600"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Documento
      </NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="documentStore.isLoading" class="text-center py-12 text-gray-400 dark:text-gray-500 text-sm">
      Cargando...
    </div>

    <!-- Empty state -->
    <div v-else-if="documents.length === 0" class="text-center py-16 dark:text-gray-400">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p class="text-gray-500 dark:text-gray-400 text-sm">No hay documentos todavia.</p>
      <NuxtLink
        :to="localePath('/panel/documents/create')"
        class="inline-flex items-center gap-1 mt-3 text-sm text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
      >
        Crear el primero →
      </NuxtLink>
    </div>

    <!-- Desktop table -->
    <div v-if="!documentStore.isLoading && documents.length > 0" class="hidden sm:block bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto dark:bg-gray-800 dark:border-gray-700">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100 dark:border-gray-700 text-left">
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Titulo</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Creado</th>
            <th class="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
          <tr
            v-for="doc in documents"
            :key="doc.id"
            class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
            @click="navigateTo(localePath(`/panel/documents/${doc.id}/edit`))"
          >
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ doc.title }}</div>
              <div v-if="doc.client_name" class="text-xs text-gray-400 mt-0.5">{{ doc.client_name }}</div>
            </td>
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="statusBadgeClass(doc.status)"
              >
                {{ statusLabel(doc.status) }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
              {{ formatDate(doc.created_at) }}
            </td>
            <td class="px-6 py-4" @click.stop>
              <div class="flex items-center gap-2">
                <NuxtLink
                  :to="localePath(`/panel/documents/${doc.id}/edit`)"
                  class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400"
                  title="Editar"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </NuxtLink>
                <button
                  type="button"
                  class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                  title="Descargar PDF"
                  @click="handleDownloadPdf(doc)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-gray-400 hover:text-purple-600 dark:hover:text-purple-400"
                  title="Duplicar"
                  @click="handleDuplicate(doc.id)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                  title="Eliminar"
                  @click="handleDelete(doc)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile cards -->
    <div v-if="!documentStore.isLoading && documents.length > 0" class="sm:hidden space-y-3">
      <div
        v-for="doc in documents"
        :key="`mobile-${doc.id}`"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 dark:bg-gray-800 dark:border-gray-700"
        @click="navigateTo(localePath(`/panel/documents/${doc.id}/edit`))"
      >
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1 min-w-0">
            <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{{ doc.title }}</h3>
            <p v-if="doc.client_name" class="text-xs text-gray-400 mt-0.5">{{ doc.client_name }}</p>
          </div>
          <span
            class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ml-2 flex-shrink-0"
            :class="statusBadgeClass(doc.status)"
          >
            {{ statusLabel(doc.status) }}
          </span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-400">{{ formatDate(doc.created_at) }}</span>
          <div class="flex items-center gap-1" @click.stop>
            <button
              type="button"
              class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-gray-400 hover:text-blue-600"
              title="Descargar PDF"
              @click="handleDownloadPdf(doc)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              type="button"
              class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-gray-400 hover:text-purple-600"
              title="Duplicar"
              @click="handleDuplicate(doc.id)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            <button
              type="button"
              class="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors text-gray-400 hover:text-red-600"
              title="Eliminar"
              @click="handleDelete(doc)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <Transition name="fade-modal">
        <div
          v-if="deleteConfirm"
          class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          @click.self="deleteConfirm = null"
        >
          <div class="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 text-center dark:bg-gray-800">
            <div class="text-4xl mb-3">🗑️</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">Eliminar documento</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
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
                class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
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
import { computed, onMounted, ref } from 'vue';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const documents = computed(() => documentStore.documents);
const deleteConfirm = ref(null);

onMounted(async () => {
  await documentStore.fetchDocuments();
});

function statusBadgeClass(status) {
  const map = {
    draft: 'bg-gray-100 text-gray-700 dark:bg-gray-600 dark:text-gray-200',
    published: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
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
    await documentStore.fetchDocuments();
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
