<template>
  <div>
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

    <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-text-default">LinkedIn</h1>
        <p class="text-sm text-text-muted mt-1">
          Crea, programa y publica posts en tu perfil de LinkedIn.
        </p>
      </div>
      <BaseButton variant="primary" @click="openCreate">Nuevo post</BaseButton>
    </header>

    <!-- Connection card -->
    <section class="bg-surface border border-border-default rounded-xl p-5 mb-6">
      <div v-if="!connection.connected" class="flex flex-col sm:flex-row sm:items-center gap-3">
        <span class="text-sm text-text-muted">LinkedIn no conectado.</span>
        <button
          type="button"
          class="px-4 py-2 bg-[#0A66C2] text-white text-sm rounded-lg hover:bg-[#004182] transition-colors inline-flex items-center gap-2 w-fit"
          @click="connectLinkedIn"
        >
          Conectar LinkedIn
        </button>
      </div>
      <div v-else class="space-y-1">
        <p class="text-sm text-text-default">
          Conectado como <strong>{{ connection.profile_name }}</strong>
          <button
            type="button"
            class="ml-3 text-xs text-text-brand hover:underline"
            @click="connectLinkedIn"
          >
            Reconectar
          </button>
        </p>
        <p
          v-if="connection.expires_at"
          class="text-xs"
          :class="expiresSoon ? 'text-danger-strong' : 'text-text-subtle'"
        >
          <template v-if="expiresSoon">⚠ </template>La conexión expira el {{ expiryDate }}
        </p>
      </div>
      <p v-if="actionMsg" class="text-sm text-text-brand mt-2">{{ actionMsg }}</p>
      <p v-if="actionError" class="text-sm text-danger-strong mt-2">{{ actionError }}</p>
    </section>

    <!-- Posts list -->
    <section>
      <p v-if="!loaded" class="text-sm text-text-muted">Cargando posts…</p>

      <div
        v-else-if="!posts.length"
        class="bg-surface border border-border-default rounded-xl p-8 text-center"
      >
        <p class="text-sm text-text-muted">
          Aún no hay posts de LinkedIn. Crea el primero con "Nuevo post".
        </p>
      </div>

      <!-- Desktop table -->
      <div
        v-else-if="!isMobile"
        class="bg-surface border border-border-default rounded-xl overflow-x-auto"
      >
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border-default text-left text-xs uppercase tracking-wide text-text-subtle">
              <th class="px-4 py-3 font-medium">Texto</th>
              <th class="px-4 py-3 font-medium">Estado</th>
              <th class="px-4 py-3 font-medium">Programado</th>
              <th class="px-4 py-3 font-medium">Publicado</th>
              <th class="px-4 py-3 font-medium text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="post in posts"
              :key="post.id"
              class="border-b border-border-default last:border-b-0 align-top"
            >
              <td class="px-4 py-3 text-text-default max-w-md">
                <p class="line-clamp-2">{{ post.commentary }}</p>
                <p
                  v-if="post.status === 'failed' && post.error_message"
                  class="text-xs text-danger-strong mt-1 truncate"
                  :title="post.error_message"
                >
                  {{ post.error_message }}
                </p>
              </td>
              <td class="px-4 py-3">
                <span
                  class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="statusClass(post.status)"
                >
                  {{ statusLabel(post.status) }}
                </span>
              </td>
              <td class="px-4 py-3 text-text-muted whitespace-nowrap">
                {{ post.scheduled_at ? formatDateTime(post.scheduled_at) : '—' }}
              </td>
              <td class="px-4 py-3 text-text-muted whitespace-nowrap">
                <a
                  v-if="post.status === 'published' && post.linkedin_post_id"
                  :href="linkedinPostUrl(post)"
                  target="_blank"
                  rel="noopener"
                  class="text-text-brand hover:underline"
                >
                  {{ formatDateTime(post.published_at) }}
                </a>
                <template v-else>—</template>
              </td>
              <td class="px-4 py-3 text-right whitespace-nowrap space-x-2">
                <button
                  v-if="post.status !== 'published'"
                  type="button"
                  class="text-xs text-text-brand hover:underline"
                  @click="openEdit(post)"
                >
                  Editar
                </button>
                <button
                  v-if="post.status !== 'published'"
                  type="button"
                  class="text-xs text-text-brand hover:underline"
                  :disabled="publishingId === post.id"
                  @click="askPublish(post)"
                >
                  {{ publishingId === post.id ? 'Publicando…' : 'Publicar ahora' }}
                </button>
                <button
                  type="button"
                  class="text-xs text-danger-strong hover:underline"
                  @click="askDelete(post)"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile cards -->
      <div v-else class="space-y-3">
        <article
          v-for="post in posts"
          :key="post.id"
          class="bg-surface border border-border-default rounded-xl p-4 space-y-2"
        >
          <div class="flex items-start justify-between gap-2">
            <span
              class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
              :class="statusClass(post.status)"
            >
              {{ statusLabel(post.status) }}
            </span>
            <a
              v-if="post.status === 'published' && post.linkedin_post_id"
              :href="linkedinPostUrl(post)"
              target="_blank"
              rel="noopener"
              class="text-xs text-text-brand hover:underline"
            >
              Ver en LinkedIn
            </a>
          </div>
          <p class="text-sm text-text-default line-clamp-3">{{ post.commentary }}</p>
          <p v-if="post.scheduled_at" class="text-xs text-text-subtle">
            Programado: {{ formatDateTime(post.scheduled_at) }}
          </p>
          <p
            v-if="post.status === 'failed' && post.error_message"
            class="text-xs text-danger-strong truncate"
            :title="post.error_message"
          >
            {{ post.error_message }}
          </p>
          <div class="flex gap-4 pt-1">
            <button
              v-if="post.status !== 'published'"
              type="button"
              class="text-xs text-text-brand hover:underline"
              @click="openEdit(post)"
            >
              Editar
            </button>
            <button
              v-if="post.status !== 'published'"
              type="button"
              class="text-xs text-text-brand hover:underline"
              :disabled="publishingId === post.id"
              @click="askPublish(post)"
            >
              {{ publishingId === post.id ? 'Publicando…' : 'Publicar ahora' }}
            </button>
            <button
              type="button"
              class="text-xs text-danger-strong hover:underline"
              @click="askDelete(post)"
            >
              Eliminar
            </button>
          </div>
        </article>
      </div>
    </section>

    <!-- Create / edit modal -->
    <BaseModal v-model="showModal" size="lg" padding="md">
      <h2 class="text-lg font-semibold text-text-default mb-4">
        {{ editingPost ? 'Editar post' : 'Nuevo post' }}
      </h2>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Texto del post</label>
          <textarea
            v-model="form.commentary"
            rows="6"
            maxlength="3000"
            class="w-full px-4 py-3 rounded-xl border border-input-border bg-input-bg text-input-text placeholder-input-placeholder text-sm leading-relaxed focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring transition-all resize-y"
            placeholder="Escribe el contenido para LinkedIn (máx 3000 caracteres)"
          />
          <p class="text-xs text-text-subtle mt-1">{{ form.commentary.length }} / 3000</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Imagen (opcional)</label>
          <input
            type="file"
            accept="image/*"
            class="block w-full text-sm text-text-muted file:mr-3 file:px-3 file:py-2 file:rounded-lg file:border-0 file:bg-surface-raised file:text-text-default file:text-sm file:cursor-pointer"
            @change="onFileChange"
          />
          <img
            v-if="imagePreview"
            :src="imagePreview"
            alt="Imagen del post"
            class="mt-2 max-h-40 rounded-lg border border-border-default"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Programar publicación (opcional)</label>
          <input
            v-model="form.scheduledLocal"
            type="datetime-local"
            class="px-4 py-2 rounded-xl border border-input-border bg-input-bg text-input-text text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring transition-all"
          />
          <p class="text-xs text-text-subtle mt-1">
            Déjalo vacío para guardar como borrador y publicar manualmente.
          </p>
        </div>

        <p v-if="formError" class="text-sm text-danger-strong">{{ formError }}</p>

        <div class="flex flex-wrap justify-end gap-3 pt-2">
          <BaseButton variant="ghost" @click="showModal = false">Cancelar</BaseButton>
          <BaseButton
            v-if="editingPost"
            variant="secondary"
            :loading="publishingId === editingPost.id"
            @click="askPublish(editingPost, true)"
          >
            Publicar ahora
          </BaseButton>
          <BaseButton variant="primary" :loading="saving" @click="savePost">
            {{ form.scheduledLocal ? 'Programar' : 'Guardar' }}
          </BaseButton>
        </div>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { useLinkedInStore } from '~/stores/linkedin';
import { useIsMobile } from '~/composables/useIsMobile';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import { formatDate, formatDateTime } from '~/utils/formatDate';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = useLinkedInStore();
const { isMobile } = useIsMobile();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const loaded = ref(false);
const posts = computed(() => store.posts);
const connection = computed(() => store.connectionStatus);

const showModal = ref(false);
const editingPost = ref(null);
const form = reactive({ commentary: '', scheduledLocal: '' });
const imageFile = ref(null);
const imagePreview = ref('');
const formError = ref('');
const saving = ref(false);
const publishingId = ref(null);
const actionMsg = ref('');
const actionError = ref('');

async function loadData() {
  await Promise.all([store.fetchLinkedInStatus(), store.fetchPosts()]);
  loaded.value = true;
}

usePanelRefresh(loadData);

onMounted(async () => {
  window.addEventListener('message', handleLinkedInMessage);
  await loadData();
});

onUnmounted(() => {
  window.removeEventListener('message', handleLinkedInMessage);
});

function handleLinkedInMessage(event) {
  // Only trust messages from our own origin (the /auth/linkedin/callback popup)
  if (event.origin !== window.location.origin) return;
  if (event.data?.type === 'linkedin-connected') {
    store.connectionStatus = event.data.data || { connected: true };
    flashMessage('LinkedIn conectado correctamente.');
    store.fetchLinkedInStatus();
  }
}

async function connectLinkedIn() {
  const result = await store.fetchLinkedInAuthUrl();
  if (result.success && result.data?.authorization_url) {
    window.open(result.data.authorization_url, '_blank', 'width=600,height=700');
  } else {
    actionError.value = 'No se pudo obtener la URL de autorización.';
  }
}

// ── Expiry helpers ──

const expiryDate = computed(() => formatDate(connection.value.expires_at, { fallback: '' }));

const expiresSoon = computed(() => {
  if (!connection.value.expires_at) return false;
  const msLeft = new Date(connection.value.expires_at).getTime() - Date.now();
  return msLeft < 7 * 24 * 60 * 60 * 1000;
});

// ── Modal / form ──

function resetForm() {
  form.commentary = '';
  form.scheduledLocal = '';
  imageFile.value = null;
  imagePreview.value = '';
  formError.value = '';
}

function openCreate() {
  resetForm();
  editingPost.value = null;
  showModal.value = true;
}

function openEdit(post) {
  resetForm();
  editingPost.value = post;
  form.commentary = post.commentary;
  form.scheduledLocal = post.scheduled_at ? isoToLocalInput(post.scheduled_at) : '';
  imagePreview.value = post.image || '';
  showModal.value = true;
}

function onFileChange(event) {
  const file = event.target.files?.[0];
  imageFile.value = file || null;
  imagePreview.value = file ? URL.createObjectURL(file) : (editingPost.value?.image || '');
}

function isoToLocalInput(iso) {
  const d = new Date(iso);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

function buildFormData() {
  const data = new FormData();
  data.append('commentary', form.commentary);
  data.append('scheduled_at', form.scheduledLocal ? new Date(form.scheduledLocal).toISOString() : '');
  if (imageFile.value) data.append('image', imageFile.value);
  return data;
}

function extractError(error) {
  if (!error) return 'Ocurrió un error. Intenta de nuevo.';
  if (typeof error === 'string') return error;
  if (error.error) return error.error;
  const firstKey = Object.keys(error)[0];
  const value = error[firstKey];
  return Array.isArray(value) ? value[0] : String(value);
}

async function savePost() {
  formError.value = '';
  if (!form.commentary.trim()) {
    formError.value = 'El texto del post es obligatorio.';
    return;
  }
  saving.value = true;
  const payload = buildFormData();
  const result = editingPost.value
    ? await store.updatePost(editingPost.value.id, payload)
    : await store.createPost(payload);
  saving.value = false;

  if (!result.success) {
    formError.value = extractError(result.error);
    return;
  }
  showModal.value = false;
  flashMessage(form.scheduledLocal ? 'Post programado.' : 'Post guardado.');
  await store.fetchPosts();
}

// ── Publish / delete ──

function askPublish(post, fromModal = false) {
  requestConfirm({
    title: 'Publicar en LinkedIn',
    message: 'El post se publicará inmediatamente en tu perfil de LinkedIn. ¿Continuar?',
    confirmText: 'Publicar',
    variant: 'warning',
    onConfirm: () => publishNow(post, fromModal),
  });
}

async function publishNow(post, fromModal = false) {
  actionError.value = '';
  publishingId.value = post.id;
  const result = await store.publishPost(post.id);
  publishingId.value = null;

  if (result.success) {
    if (fromModal) showModal.value = false;
    flashMessage('Publicado en LinkedIn correctamente.');
  } else {
    const msg = extractError(result.error);
    if (fromModal) {
      formError.value = msg;
    } else {
      actionError.value = msg;
    }
  }
  await store.fetchPosts();
}

function askDelete(post) {
  requestConfirm({
    title: 'Eliminar post',
    message: 'Se eliminará el registro local del post. Esta acción no borra nada en LinkedIn. ¿Continuar?',
    confirmText: 'Eliminar',
    variant: 'danger',
    onConfirm: () => removePost(post),
  });
}

async function removePost(post) {
  const result = await store.deletePost(post.id);
  if (result.success) {
    flashMessage('Post eliminado.');
  } else {
    actionError.value = extractError(result.error);
  }
  await store.fetchPosts();
}

// ── Display helpers ──

let msgTimeout = null;
function flashMessage(text) {
  actionMsg.value = text;
  clearTimeout(msgTimeout);
  msgTimeout = setTimeout(() => { actionMsg.value = ''; }, 5000);
}

function statusLabel(status) {
  return {
    draft: 'Borrador',
    scheduled: 'Programado',
    published: 'Publicado',
    failed: 'Fallido',
  }[status] || status;
}

function statusClass(status) {
  return {
    draft: 'bg-surface-muted text-text-muted',
    scheduled: 'bg-warning-soft text-warning-strong',
    published: 'bg-primary-soft text-text-brand',
    failed: 'bg-danger-soft text-danger-strong',
  }[status] || 'bg-surface-muted text-text-muted';
}

function linkedinPostUrl(post) {
  return `https://www.linkedin.com/feed/update/${post.linkedin_post_id}/`;
}
</script>
