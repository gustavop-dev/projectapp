<template>
  <div class="border-t border-border-default pt-5 space-y-4" data-testid="linktree-template-editor">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-text-default">Plantilla HTML</h3>
        <p class="text-sm text-text-subtle mt-1">Sube tu diseño y úsalo con los datos de esta tarjeta.</p>
      </div>
      <BaseBadge :variant="store.activeVersionId ? 'success' : 'neutral'">{{ store.activeVersionId ? 'Plantilla publicada' : 'Tema básico' }}</BaseBadge>
    </div>
    <BaseAlert v-if="hasUnsavedChanges" variant="warning">Guarda los cambios del perfil antes de validar o publicar una plantilla.</BaseAlert>
    <p v-if="store.activeVersionId" class="text-sm text-text-subtle">La publicación conserva sus datos e imágenes. Después de editar el perfil, vuelve a validar y publicar para actualizarla.</p>
    <BaseAlert v-if="error" variant="danger" data-testid="template-request-error">{{ error }}</BaseAlert>
    <BaseAlert v-if="success" variant="success" role="status">{{ success }}</BaseAlert>
    <BaseButton v-if="loadFailed" variant="secondary" @click="load">Reintentar carga</BaseButton>
    <div class="flex flex-wrap gap-2">
      <input ref="fileInput" type="file" multiple accept=".zip,.html,.css,.json,.png,.webp,.svg,.jpg,.jpeg" class="sr-only" aria-label="Archivos de plantilla" data-testid="template-file-input" @change="selectFiles" />
      <input ref="folderInput" type="file" webkitdirectory multiple class="sr-only" aria-label="Carpeta de plantilla" @change="selectFiles" />
      <BaseButton variant="secondary" :disabled="locked" :disabled-reason="lockReason" data-testid="template-upload-select" @click="fileInput?.click()">Subir plantilla</BaseButton>
      <BaseButton variant="ghost" :disabled="locked" :disabled-reason="lockReason" @click="folderInput?.click()">Elegir carpeta</BaseButton>
    </div>
    <p class="text-xs text-text-subtle">ZIP o archivos: template.html y manifest.json; template.css e imágenes opcionales. Máximo 4 MB por paquete y 800 KB por imagen.</p>
    <ul v-if="files.length" class="space-y-2" aria-label="Archivos seleccionados">
      <li v-for="(entry, index) in files" :key="entry.path" class="flex items-center justify-between gap-2 text-sm text-text-default">
        <span class="min-w-0 break-all">{{ entry.path }}</span>
        <BaseButton variant="ghost" size="sm" :aria-label="`Quitar ${entry.path}`" :disabled="store.busy" disabled-reason="Espera a que termine la carga" @click="files.splice(index, 1)">Quitar</BaseButton>
      </li>
    </ul>
    <BaseButton v-if="files.length" variant="primary" :loading="store.busy" :disabled="locked" :disabled-reason="lockReason" data-testid="template-upload-validate" @click="upload">Subir y validar</BaseButton>

    <div v-if="store.templates.length" class="space-y-2">
      <BaseFormField label="Plantillas disponibles" for="lt-template-library">
        <BaseSelect id="lt-template-library" v-model="templateId" :options="templateOptions" placeholder="Selecciona una plantilla" data-testid="template-library-select" />
      </BaseFormField>
      <div class="flex flex-wrap gap-2">
        <BaseButton variant="secondary" :disabled="locked || !templateId" :disabled-reason="!templateId ? 'Selecciona una plantilla' : lockReason" @click="applyTemplate">Usar y validar</BaseButton>
        <BaseButton v-if="chosenTemplate?.can_share" variant="ghost" :disabled="store.busy" disabled-reason="Espera a que termine la operación" data-testid="template-share" @click="share">{{ chosenTemplate.is_shared ? 'Dejar de compartir' : 'Compartir con el cliente' }}</BaseButton>
      </div>
      <p class="text-xs text-text-subtle">Las plantillas compartidas están disponibles en los proyectos del mismo cliente. Cada tarjeta usa sus propios datos e imágenes.</p>
    </div>

    <div v-if="selected" class="space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <h4 class="font-semibold text-text-default">{{ selected.name }}</h4>
        <BaseBadge :variant="selected.status === 'valid' ? 'success' : selected.status === 'invalid' ? 'danger' : 'neutral'">{{ statusLabel }}</BaseBadge>
      </div>
      <p v-if="pending" role="status" class="text-sm text-text-subtle" data-testid="template-validating">Comprobando contraste, enlaces y movimiento en 320, 375 y 430 px… Puedes continuar trabajando mientras termina.</p>
      <p v-if="selected.status === 'valid'" class="text-sm text-text-default" data-testid="template-valid">La plantilla pasó la validación. Revisa las tres capturas antes de publicar.</p>
      <ul v-if="issues.length" class="space-y-2" aria-label="Resultado de validación" data-testid="template-issues">
        <li v-for="(item, index) in issues" :key="index" class="rounded-lg border border-border-default p-3 text-sm" :class="item.severity === 'error' ? 'text-danger-strong' : 'text-text-default'">
          <strong>{{ item.severity === 'error' ? 'Error' : 'Aviso' }}:</strong> {{ item.message }}
          <span v-if="item.file" class="block text-xs text-text-subtle">{{ item.file }}{{ item.line ? ` · línea ${item.line}` : '' }}{{ item.node ? ` · elemento ${item.node}` : '' }}{{ item.width ? ` · ${item.width} px` : '' }}</span>
        </li>
      </ul>
      <div class="flex flex-wrap gap-2">
        <BaseButton variant="primary" :disabled="locked || selected.status !== 'valid' || selected.active || uploadIssues.length > 0" :disabled-reason="publishReason" :loading="store.busy" data-testid="template-publish" @click="publish">{{ selected.active ? 'Publicada' : 'Publicar' }}</BaseButton>
        <BaseButton variant="secondary" :disabled="locked" :disabled-reason="lockReason" data-testid="template-revalidate" @click="revalidate">Validar con datos actuales</BaseButton>
      </div>
      <div v-if="selected.editable_assets?.length" class="space-y-3">
        <h4 class="font-semibold text-text-default">Imágenes de la plantilla</h4>
        <div v-for="asset in selected.editable_assets" :key="asset.key" class="flex flex-wrap items-center gap-3 rounded-lg border border-border-default p-3">
          <img :src="asset.url" :alt="asset.key" class="h-16 w-16 object-contain rounded" />
          <span class="text-sm text-text-default break-all">{{ asset.key }}</span>
          <input :ref="assetInputRef(asset.key)" type="file" accept=".png,.webp,.svg,.jpg,.jpeg" class="sr-only bg-input-bg" :aria-label="`Cambiar ${asset.key}`" :data-testid="`template-asset-${asset.key}`" @change="replaceAsset(asset.key, $event)" />
          <BaseButton variant="secondary" size="sm" :disabled="locked" :disabled-reason="lockReason" @click="assetInputs[asset.key]?.click()">Cambiar</BaseButton>
          <BaseButton v-if="asset.overridden" variant="ghost" size="sm" :disabled="locked" :disabled-reason="lockReason" @click="resetAsset(asset.key)">Restablecer</BaseButton>
        </div>
      </div>
      <div class="space-y-3">
        <h4 class="font-semibold text-text-default">Vista previa</h4>
        <div class="flex flex-wrap gap-2" aria-label="Ancho de vista previa">
          <BaseButton v-for="width in widths" :key="width" :variant="previewWidth === width ? 'primary' : 'secondary'" size="sm" :aria-pressed="previewWidth === width" @click="previewWidth = width">{{ width }} px</BaseButton>
        </div>
        <div class="overflow-x-auto rounded-lg border border-border-default bg-surface-muted p-2" data-testid="template-preview-container">
          <iframe :key="`${selected.id}-${previewWidth}`" :src="selected.preview_url" sandbox="" :title="`Plantilla a ${previewWidth} px`" :width="previewWidth" height="600" class="block border-0 mx-auto bg-surface" data-testid="template-sandbox-preview" />
        </div>
        <div v-if="Object.keys(selected.screenshots || {}).length" class="grid grid-cols-1 sm:grid-cols-3 gap-3" data-testid="template-screenshots">
          <figure v-for="width in widths" :key="width" class="min-w-0">
            <img v-if="selected.screenshots[width]" :src="selected.screenshots[width]" :alt="`Captura validada a ${width} px`" class="w-full rounded border border-border-default" loading="lazy" />
            <figcaption class="text-xs text-text-subtle mt-1">{{ width }} px</figcaption>
          </figure>
        </div>
      </div>
    </div>
    <ul v-else-if="issues.length" class="space-y-2 text-sm text-danger-strong" aria-label="Errores de carga" data-testid="template-upload-errors">
      <li v-for="(item, index) in issues" :key="index">{{ item.message }} <span v-if="item.file">({{ item.file }}:{{ item.line || 1 }})</span></li>
    </ul>

    <div v-if="store.versions.length" class="space-y-2 border-t border-border-default pt-4">
      <h4 class="font-semibold text-text-default">Versiones</h4>
      <BaseFormField label="Historial de plantillas" for="lt-template-version">
        <BaseSelect id="lt-template-version" v-model="selectedId" :options="versionOptions" data-testid="template-version-select" />
      </BaseFormField>
      <BaseButton v-if="selected?.published_at && !selected.active" variant="secondary" :disabled="locked" :disabled-reason="lockReason" data-testid="template-restore" @click="revalidate">Restaurar esta plantilla y validar</BaseButton>
      <BaseButton v-if="store.nextOffset !== null" variant="ghost" :loading="store.busy" @click="loadMore">Ver versiones anteriores</BaseButton>
    </div>
    <BaseButton v-if="store.activeVersionId" variant="danger-ghost" :disabled="store.busy" disabled-reason="Espera a que termine la operación" data-testid="template-reset" @click="reset">Restablecer tema básico</BaseButton>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useLinktreeTemplatesStore } from '~/stores/linktree-templates';

const props = defineProps({ treeId: { type: String, required: true }, hasUnsavedChanges: { type: Boolean, default: false } });
const store = useLinktreeTemplatesStore();
const files = ref([]);
const fileInput = ref(null);
const folderInput = ref(null);
const assetInputs = {};
const selectedId = ref('');
const templateId = ref('');
const error = ref('');
const success = ref('');
const uploadIssues = ref([]);
const loadFailed = ref(false);
const widths = [320, 375, 430];
const previewWidth = ref(320);
let timer;
let disposed = false;
const selected = computed(() => store.versions.find((v) => v.id === selectedId.value));
const chosenTemplate = computed(() => store.templates.find((t) => t.id === templateId.value));
const pending = computed(() => store.versions.some((v) => v.status === 'pending'));
const locked = computed(() => store.busy || pending.value || props.hasUnsavedChanges);
const lockReason = computed(() => props.hasUnsavedChanges ? 'Guarda primero los cambios del perfil' : pending.value ? 'Espera a que termine la validación' : 'Espera a que termine la operación');
const publishReason = computed(() => locked.value ? lockReason.value : selected.value?.active ? 'Esta versión ya está publicada' : 'Corrige los errores y vuelve a validar');
const issues = computed(() => [...uploadIssues.value, ...(selected.value?.issues || [])]);
const statusLabel = computed(() => ({ pending: 'Validando', valid: 'Lista para publicar', invalid: 'Requiere correcciones' }[selected.value?.status]));
const templateOptions = computed(() => store.templates.map((t) => ({ value: t.id, label: `${t.name}${t.is_shared ? ' · Compartida' : ''}` })));
const versionOptions = computed(() => store.versions.map((v) => ({ value: v.id, label: `${v.name} · ${new Date(v.created_at).toLocaleString()}${v.active ? ' · Publicada' : ''}` })));

function schedule() {
  clearTimeout(timer);
  if (!disposed && pending.value) timer = setTimeout(load, 3000);
}
async function load() {
  try {
    await store.load(props.treeId);
    if (loadFailed.value) error.value = '';
    loadFailed.value = false;
    if (!store.versions.some((v) => v.id === selectedId.value)) selectedId.value = store.versions[0]?.id || '';
    if (!templateId.value) templateId.value = store.templates[0]?.id || '';
    schedule();
  } catch {
    loadFailed.value = true;
    error.value = 'No se pudo cargar la biblioteca de plantillas.';
  }
}
async function perform(suffix, payload, method = 'POST', message = '') {
  error.value = ''; success.value = ''; uploadIssues.value = [];
  try {
    const data = await store.mutate(props.treeId, suffix, payload, method);
    if (data.id && data.status) selectedId.value = data.id;
    if (data.template_id) templateId.value = data.template_id;
    success.value = message;
    schedule();
    return true;
  } catch (failure) {
    if (failure.mutationCompleted) {
      error.value = 'La operación se guardó, pero no se pudo actualizar la biblioteca. Reintenta la carga.';
      loadFailed.value = true;
      return false;
    }
    const data = failure.response?.data;
    uploadIssues.value = data?.issues || [];
    if (!uploadIssues.value.length) error.value = data?.detail || 'No se pudo completar la operación. Inténtalo de nuevo.';
    return false;
  }
}
function assetInputRef(key) { return (element) => { assetInputs[key] = element; }; }
function selectFiles(event) {
  const selectedFiles = [...(event.target.files || [])];
  if (selectedFiles.some((file) => file.name.toLowerCase().endsWith('.zip'))) files.value = [];
  else files.value = files.value.filter((entry) => !entry.path.endsWith('.zip'));
  for (const file of selectedFiles) {
    const path = file.webkitRelativePath || (/^(template\.html|template\.css|manifest\.json)$/i.test(file.name) || file.name.endsWith('.zip') ? file.name : `assets/${file.name}`);
    files.value = files.value.filter((entry) => entry.path !== path);
    files.value.push({ path, file });
  }
  event.target.value = '';
}
async function upload() {
  if (locked.value) return;
  const form = new FormData();
  for (const entry of files.value) form.append(entry.path.endsWith('.zip') ? 'package' : entry.path, entry.file);
  if (await perform('', form)) files.value = [];
}
function applyTemplate() { return perform('', { template_id: templateId.value }); }
function publish() { return perform(`${selectedId.value}/publish/`, {}, 'POST', 'Plantilla publicada. La URL de la tarjeta se conserva.'); }
function revalidate() { return perform('', { version_id: selectedId.value }); }
function reset() { return perform('reset/', {}, 'POST', 'El tema básico vuelve a estar publicado. Conservamos el historial de plantillas.'); }
function share() { return perform(`library/${templateId.value}/share/`, { is_shared: !chosenTemplate.value.is_shared }, 'POST', chosenTemplate.value.is_shared ? 'Plantilla privada.' : 'Plantilla compartida con los proyectos de este cliente.'); }
function resetAsset(key) { return perform(`${selectedId.value}/assets/${key}/`, {}, 'DELETE'); }
function replaceAsset(key, event) {
  const file = event.target.files?.[0];
  event.target.value = '';
  if (!file || locked.value) return;
  const form = new FormData(); form.append('image', file);
  return perform(`${selectedId.value}/assets/${key}/`, form);
}
async function loadMore() {
  try { await store.load(props.treeId, store.nextOffset); } catch { error.value = 'No se pudieron cargar las versiones anteriores.'; }
}
onMounted(load);
onUnmounted(() => { disposed = true; clearTimeout(timer); });
</script>
