<template>
  <div class="w-full">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div>
        <NuxtLink
          :to="localePath('/panel/documents')"
          class="inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-default transition-colors"
          aria-label="Volver a documentos"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Volver a documentos
        </NuxtLink>
        <h1 class="text-2xl font-light text-text-default mt-2">Nuevo Documento</h1>
        <p class="text-sm text-text-muted mt-1">Crea un documento a partir de Markdown (pegado o subido).</p>
      </div>
      <div class="hidden lg:flex items-center gap-3">
        <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-text-muted hover:text-text-default">
          Cancelar
        </NuxtLink>
        <BaseButton variant="primary" size="md" type="submit" form="doc-create-form" :disabled="!canSubmit" :title="canSubmit ? '' : 'Falta título o contenido'">
          {{ documentStore.isUpdating ? 'Creando...' : 'Crear Documento' }}
        </BaseButton>
      </div>
    </div>

    <form
      id="doc-create-form"
      class="grid grid-cols-1 lg:grid-cols-[20rem_minmax(0,1fr)] xl:grid-cols-[24rem_minmax(0,1fr)] gap-6"
      @submit.prevent="handleSubmit"
    >
      <aside
        class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 sm:p-6
               lg:sticky lg:top-6 lg:self-start lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto"
      >
        <div class="space-y-6">
          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Identificación</h2>
            <div>
              <label for="doc-title" class="block text-sm font-medium text-text-default mb-1">Título *</label>
              <input
                id="doc-title"
                v-model="form.title"
                type="text"
                required
                placeholder="Mi Documento"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default placeholder:text-text-subtle
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Cliente</label>
              <ClientAutocomplete
                v-model="form.client"
                :initial-label="clientDisplayName"
                test-id="doc-client-autocomplete"
                @select="onClientSelect"
                @create-new="onCreateNewClient"
              />
              <p
                v-if="suggestedFromFolder"
                class="text-xs text-text-subtle mt-1"
                data-testid="doc-client-suggested-hint"
              >
                Sugerido por la carpeta — puedes cambiarlo o quitarlo.
              </p>
              <p v-else class="text-xs text-text-subtle mt-1">
                Opcional. Las plantillas y notas pueden no tener dueño.
              </p>
            </div>

            <!-- Inline client creation: the clients module without leaving the form -->
            <div
              v-if="inlineClientOpen"
              class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-3"
              data-testid="doc-inline-client"
            >
              <p class="text-sm font-medium text-text-default">Crear cliente nuevo</p>
              <ClientFormFields
                v-model="inlineClient"
                testid-prefix="doc-inline-client"
                dense
              />
              <div class="flex justify-end gap-2">
                <BaseButton type="button" variant="secondary" size="sm" @click="inlineClientOpen = false">
                  Cancelar
                </BaseButton>
                <BaseButton
                  type="button"
                  variant="primary"
                  size="sm"
                  :disabled="creatingClient"
                  data-testid="doc-inline-client-save"
                  @click="createInlineClient"
                >
                  {{ creatingClient ? 'Creando...' : 'Crear cliente' }}
                </BaseButton>
              </div>
            </div>

            <ProjectSelect
              v-model="form.project"
              :client-profile-id="form.client"
              :client-label="clientDisplayName"
              :allow-no-client="true"
              :auto-select-single="true"
              testid="doc-project-select"
              @select="onProjectSelect"
            />
          </div>

          <hr class="border-border-muted" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Organización</h2>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Carpeta</label>
              <select
                v-model="form.folder_id"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              >
                <option :value="null">Sin carpeta</option>
                <option v-for="folder in folderStore.activeFolders" :key="folder.id" :value="folder.id">
                  {{ folder.name }}
                </option>
              </select>
            </div>
            <TagSelector v-model="form.tag_ids" :tags="tagStore.tags" />
          </div>

          <hr class="border-border-muted" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Opciones de exportación</h2>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Idioma</label>
              <select
                v-model="form.language"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              >
                <option value="es">Español</option>
                <option value="en">English</option>
              </select>
            </div>
            <div class="space-y-1">
              <label
                v-for="option in coverOptions"
                :key="option.key"
                class="flex items-center gap-3 cursor-pointer py-1.5 px-1 select-none"
              >
                <BaseToggle v-model="form[option.key]" />
                <span class="text-sm font-medium text-text-default">{{ option.label }}</span>
              </label>
            </div>
          </div>
        </div>
      </aside>

      <section
        class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 sm:p-6
               flex flex-col min-w-0"
      >
        <div class="flex gap-1 mb-5 bg-surface-raised rounded-xl p-1 w-full sm:w-fit">
          <button
            v-for="tab in modeTabs"
            :key="tab.id"
            type="button"
            :class="[
              'inline-flex items-center justify-center gap-2 flex-1 sm:flex-none sm:min-w-[11rem] px-4 py-2 text-sm rounded-lg transition-all',
              mode === tab.id
                ? 'bg-surface shadow-sm font-medium text-text-default ring-1 ring-focus-ring/20'
                : 'text-text-muted hover:text-text-default'
            ]"
            @click="mode = tab.id"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="tab.iconPath" />
            </svg>
            {{ tab.label }}
          </button>
        </div>

        <div v-if="mode === 'paste'" class="flex-1 flex flex-col min-h-0">
          <div class="flex items-center justify-between mb-2 gap-3 flex-wrap">
            <label for="doc-markdown" class="block text-sm font-medium text-text-default">Contenido Markdown *</label>
            <div class="flex items-center gap-3">
              <span v-if="form.content_markdown" class="text-xs text-text-subtle tabular-nums">
                {{ form.content_markdown.length.toLocaleString() }} caracteres
              </span>
              <BaseSegmented
                v-model="form.template_style"
                size="sm"
                :options="templateStyleOptions"
                aria-label="Estilo de plantilla"
              />
              <button
                type="button"
                class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
                :class="showPreview
                  ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                  : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
                @click="showPreview = !showPreview"
              >
                <svg v-if="showPreview" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                </svg>
                {{ showPreview ? 'Ocultar vista previa' : 'Vista previa' }}
              </button>
            </div>
          </div>
          <div :class="showPreview ? 'grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0' : 'flex-1 min-h-0 flex'">
            <textarea
              id="doc-markdown"
              v-model="form.content_markdown"
              placeholder="# Mi Documento&#10;&#10;Escribe o pega tu contenido en formato Markdown..."
              class="w-full px-4 py-3 border border-border-default rounded-xl text-sm font-mono leading-relaxed bg-surface text-text-default placeholder:text-text-subtle
                     focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-none
                     min-h-[24rem] lg:h-[calc(100vh-20rem)]"
            ></textarea>
            <div
              v-if="showPreview"
              class="border border-border-default rounded-xl bg-surface overflow-y-auto
                     min-h-[24rem] lg:h-[calc(100vh-20rem)]"
            >
              <div class="sticky top-0 px-3 py-2 border-b border-border-default bg-surface-raised rounded-t-xl z-10">
                <span class="text-xs font-medium text-text-muted uppercase tracking-wide">Vista previa</span>
              </div>
              <DocumentMarkdownBody
                v-if="form.content_markdown.trim()"
                :markdown="form.content_markdown"
                :theme="form.template_style"
                class="px-5 py-4"
              />
              <div
                v-else
                class="flex items-center justify-center h-64 text-sm text-text-subtle"
              >
                Escribe markdown para ver la vista previa...
              </div>
            </div>
          </div>
        </div>

        <div v-if="mode === 'upload'" class="flex-1 flex flex-col">
          <label class="block text-sm font-medium text-text-default mb-2">Archivo Markdown (.md)</label>
          <div
            :class="[
              'border-2 border-dashed rounded-xl p-8 sm:p-10 text-center transition-colors',
              isDragging
                ? 'border-emerald-500 bg-primary-soft'
                : 'border-border-default hover:border-border-default'
            ]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <svg class="w-10 h-10 mx-auto text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="mt-3 text-sm text-text-muted">
              Arrastra un archivo <code class="text-xs px-1 py-0.5 bg-surface-raised rounded">.md</code> aquí
            </p>
            <p class="text-xs text-text-subtle mt-1">o</p>
            <label
              class="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-medium
                     hover:bg-primary cursor-pointer transition-colors shadow-sm"
            >
              Seleccionar archivo
              <input type="file" accept=".md,.markdown,.txt" class="hidden" @change="handleFileUpload" />
            </label>
            <p v-if="uploadedFileName" class="mt-4 text-xs text-text-muted">
              <span class="font-medium">Archivo:</span> {{ uploadedFileName }}
            </p>
          </div>
          <textarea
            v-model="form.content_markdown"
            rows="12"
            readonly
            placeholder="El contenido del archivo aparecerá aquí..."
            class="w-full mt-4 px-4 py-3 border border-border-default rounded-xl text-sm font-mono leading-relaxed
                   bg-surface-raised text-text-muted placeholder:text-text-subtle outline-none resize-y"
          ></textarea>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-4 lg:hidden">
          <BaseButton variant="primary" size="md" type="submit" class="sm:px-6" :disabled="!canSubmit">
            {{ documentStore.isUpdating ? 'Creando...' : 'Crear Documento' }}
          </BaseButton>
          <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-text-muted hover:text-text-default">
            Cancelar
          </NuxtLink>
        </div>
      </section>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue';
import TagSelector from '~/components/panel/documents/TagSelector.vue';
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectSelect from '~/components/accounting/ProjectSelect.vue';
import ClientFormFields from '~/components/clients/ClientFormFields.vue';
import { clientFormPayload, emptyClientForm } from '~/utils/billingCode';
import { useProposalClientsStore } from '~/stores/proposal_clients';
import { useClientProjectCascade } from '~/composables/useClientProjectCascade';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelNotify } from '~/composables/usePanelNotify';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();
const clientsStore = useProposalClientsStore();
const notify = usePanelNotify();
const mode = ref('paste');
const uploadedFileName = ref('');
const showPreview = ref(true);
const isDragging = ref(false);
const route = useRoute();

const clientDisplayName = ref('');
// Una decisión del operador (elegir, crear o limpiar cliente) apaga la
// sugerencia por carpeta para siempre en este form.
const clientTouched = ref(false);
const suggestedFromFolder = ref(false);
const inlineClientOpen = ref(false);
const inlineClient = ref(emptyClientForm());
const creatingClient = ref(false);

const form = reactive({
  title: '',
  client: null,
  project: null,
  language: 'es',
  include_portada: true,
  include_subportada: true,
  include_contraportada: true,
  content_markdown: '',
  folder_id: null,
  tag_ids: [],
  template_style: 'professional',
});

usePanelRefresh(() => Promise.all([folderStore.fetchFolders(), tagStore.fetchTags()]));

onMounted(async () => {
  await Promise.all([folderStore.fetchFolders(), tagStore.fetchTags()]);
  const preselectFolder = route.query.folder;
  if (preselectFolder && preselectFolder !== 'all' && preselectFolder !== 'none') {
    const numeric = Number(preselectFolder);
    if (!Number.isNaN(numeric)) form.folder_id = numeric;
  }
});

const canSubmit = computed(
  () => !documentStore.isUpdating && form.title.trim() && form.content_markdown.trim(),
);

// Elegir cliente o proyecto es una decisión del operador: retira la
// sugerencia de la carpeta y evita que vuelva a proponerse.
const { onClientSelect, onProjectSelect } = useClientProjectCascade(
  form,
  clientDisplayName,
  {
    onOperatorChoice() {
      clientTouched.value = true;
      suggestedFromFolder.value = false;
    },
  },
);

function onCreateNewClient(typedName) {
  inlineClientOpen.value = true;
  inlineClient.value = { ...emptyClientForm(), name: typedName || '' };
}

async function createInlineClient() {
  creatingClient.value = true;
  const result = await clientsStore.createClient(clientFormPayload(inlineClient.value));
  creatingClient.value = false;
  if (result.success && result.data?.id) {
    inlineClientOpen.value = false;
    onClientSelect(result.data);
  }
}

function clearSuggestedClient() {
  form.client = null;
  clientDisplayName.value = '';
  form.project = null;
  suggestedFromFolder.value = false;
}

// La carpeta ya está diciendo de quién es: al fijarla (incluido ?folder= de
// la URL) se propone su cliente mayoritario. Sólo prellenado — nunca pisa una
// decisión del operador, y cambiar de carpeta re-propone o retira lo sugerido.
watch(() => form.folder_id, async (folderId) => {
  if (clientTouched.value) return;
  if (form.client && !suggestedFromFolder.value) return;
  if (!Number.isInteger(folderId)) {
    if (suggestedFromFolder.value) clearSuggestedClient();
    return;
  }
  const result = await documentStore.fetchFolderClientSuggestion(folderId);
  if (clientTouched.value) return;
  if (result.success && result.data?.client) {
    form.client = result.data.client;
    clientDisplayName.value = result.data.client_display_name || '';
    suggestedFromFolder.value = true;
  } else if (suggestedFromFolder.value) {
    clearSuggestedClient();
  }
});

const coverOptions = [
  { key: 'include_portada', label: 'Incluir portada' },
  { key: 'include_subportada', label: 'Incluir subportada' },
  { key: 'include_contraportada', label: 'Incluir contraportada' },
];

const templateStyleOptions = [
  { value: 'friendly', label: 'Amigable', testId: 'doc-style-friendly' },
  { value: 'professional', label: 'Profesional', testId: 'doc-style-professional' },
];

const modeTabs = [
  {
    id: 'paste',
    label: 'Pegar Markdown',
    iconPath: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
  },
  {
    id: 'upload',
    label: 'Cargar Archivo',
    iconPath: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12',
  },
];

function readMarkdownFile(file) {
  if (!file) return;
  uploadedFileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    form.content_markdown = e.target?.result || '';
  };
  reader.readAsText(file);
}

function handleFileUpload(event) {
  readMarkdownFile(event.target.files?.[0]);
}

function handleDragLeave(event) {
  // dragleave also fires when the cursor enters a child; ignore those so the highlight doesn't flicker.
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragging.value = false;
  }
}

function handleDrop(event) {
  isDragging.value = false;
  readMarkdownFile(event.dataTransfer?.files?.[0]);
}

async function handleSubmit() {
  const payload = {
    title: form.title.trim(),
    // Siempre presentes, null incluido: es lo que permite guardar sin dueño.
    client: form.client ?? null,
    project: form.project ?? null,
    language: form.language,
    include_portada: form.include_portada,
    include_subportada: form.include_subportada,
    include_contraportada: form.include_contraportada,
    markdown: form.content_markdown,
    folder_id: form.folder_id,
    tag_ids: form.tag_ids,
    template_style: form.template_style,
  };

  const result = await documentStore.createFromMarkdown(payload);
  if (result.success) {
    notify.success({ title: 'Documento creado' });
    navigateTo(localePath(`/panel/documents/${result.data.id}/edit`));
  } else {
    const fieldDetail = result.fieldErrors
      ? Object.entries(result.fieldErrors).map(([k, v]) => `${k}: ${v}`).join(' · ')
      : '';
    notify.error({
      title: 'No se pudo crear el documento',
      detail: fieldDetail || result.message,
    });
  }
}
</script>

