<template>
  <div>
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors">
        ← Volver a documentos
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-2">
        {{ documentStore.currentDocument?.title || 'Editar Documento' }}
      </h1>
    </div>

    <!-- Loading -->
    <div v-if="documentStore.isLoading" class="text-center py-12 text-gray-400 dark:text-gray-500 text-sm">
      Cargando...
    </div>

    <!-- Not found -->
    <div v-else-if="loadError" class="text-center py-16">
      <p class="text-gray-500 dark:text-gray-400 text-sm">No se pudo cargar el documento.</p>
      <NuxtLink
        :to="localePath('/panel/documents')"
        class="inline-flex items-center gap-1 mt-3 text-sm text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
      >
        ← Volver a la lista
      </NuxtLink>
    </div>

    <!-- Edit form -->
    <form v-else-if="documentStore.currentDocument" class="max-w-3xl space-y-6" @submit.prevent="handleSave">
      <!-- Metadata card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 dark:bg-gray-800 dark:border-gray-700">
        <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">Metadatos</h3>
        <div class="space-y-4">
          <!-- Title -->
          <div>
            <label for="edit-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titulo</label>
            <input
              id="edit-title"
              v-model="form.title"
              type="text"
              required
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
            />
          </div>

          <!-- Client name -->
          <div>
            <label for="edit-client" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del cliente</label>
            <input
              id="edit-client"
              v-model="form.client_name"
              type="text"
              placeholder="Empresa S.A."
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
            />
          </div>

          <!-- Language + Cover toggle + Status -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma</label>
              <select
                v-model="form.language"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                <option value="es">Espanol</option>
                <option value="en">English</option>
              </select>
            </div>
            <div class="flex flex-col justify-end">
              <label class="flex items-center gap-3 cursor-pointer py-2.5 px-1 select-none">
                <span class="relative flex-shrink-0">
                  <input
                    v-model="withCovers"
                    type="checkbox"
                    class="sr-only peer"
                  />
                  <span
                    class="block w-10 h-6 rounded-full transition-colors duration-200
                           bg-gray-200 peer-checked:bg-emerald-500
                           dark:bg-gray-600 dark:peer-checked:bg-emerald-500"
                  ></span>
                  <span
                    class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200
                           peer-checked:translate-x-4"
                  ></span>
                </span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Portada y contraportada</span>
              </label>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estado</label>
              <select
                v-model="form.status"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                       dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
              >
                <option value="draft">Borrador</option>
                <option value="published">Publicado</option>
                <option value="archived">Archivado</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Content card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 dark:bg-gray-800 dark:border-gray-700">
        <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Contenido Markdown</h3>
        <textarea
          v-model="form.content_markdown"
          rows="20"
          placeholder="# Contenido del documento..."
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono leading-relaxed
                 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y
                 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
        ></textarea>
      </div>

      <!-- Errors -->
      <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl dark:bg-red-900/20 dark:text-red-400">
        {{ errorMsg }}
      </div>

      <!-- Success -->
      <div v-if="saveSuccess" class="text-sm text-emerald-600 bg-emerald-50 px-4 py-3 rounded-xl dark:bg-emerald-900/20 dark:text-emerald-400">
        Documento guardado correctamente.
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          :disabled="documentStore.isUpdating"
          class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                 hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
        >
          {{ documentStore.isUpdating ? 'Guardando...' : 'Guardar' }}
        </button>
        <button
          type="button"
          :disabled="isDownloading"
          class="px-5 sm:px-6 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-xl font-medium text-sm
                 hover:bg-gray-50 hover:border-gray-300 transition-colors
                 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 disabled:opacity-50"
          @click="handleDownloadPdf"
        >
          {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
        </button>
        <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
          Cancelar
        </NuxtLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue';

const localePath = useLocalePath();
const route = useRoute();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const errorMsg = ref('');
const saveSuccess = ref(false);
const loadError = ref(false);
const isDownloading = ref(false);

const form = reactive({
  title: '',
  client_name: '',
  language: 'es',
  cover_type: 'generic',
  status: 'draft',
  content_markdown: '',
});

/** Toggle: true = cover_type 'generic', false = cover_type 'none'. */
const withCovers = computed({
  get: () => form.cover_type !== 'none',
  set: (val) => { form.cover_type = val ? 'generic' : 'none'; },
});

onMounted(async () => {
  const id = route.params.id;
  const result = await documentStore.fetchDocument(id);
  if (result.success && result.data) {
    form.title = result.data.title || '';
    form.client_name = result.data.client_name || '';
    form.language = result.data.language || 'es';
    form.cover_type = result.data.cover_type || 'generic';
    form.status = result.data.status || 'draft';
    form.content_markdown = result.data.content_markdown || '';
  } else {
    loadError.value = true;
  }
});

function formatError(errors) {
  if (errors && typeof errors === 'object') {
    return Object.entries(errors)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ');
  }
  return 'Error al guardar el documento.';
}

async function handleSave() {
  errorMsg.value = '';
  saveSuccess.value = false;

  const payload = {
    title: form.title.trim(),
    client_name: form.client_name.trim(),
    language: form.language,
    cover_type: form.cover_type,
    status: form.status,
    content_markdown: form.content_markdown,
  };

  const result = await documentStore.updateDocument(route.params.id, payload);
  if (result.success) {
    saveSuccess.value = true;
    setTimeout(() => { saveSuccess.value = false; }, 3000);
  } else {
    errorMsg.value = formatError(result.errors);
  }
}

async function handleDownloadPdf() {
  isDownloading.value = true;
  await documentStore.downloadPdf(route.params.id, form.title || 'document');
  isDownloading.value = false;
}
</script>
