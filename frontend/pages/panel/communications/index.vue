<template>
  <div :class="PAGE_MAX_WIDTH" data-testid="communications-page">
    <header class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-2xl font-light text-text-default">Comunicaciones</h1>
        <p class="mt-1 max-w-3xl text-sm text-text-subtle">
          Registro por cliente de lo que se envió y lo que respondió, con fechas y documentos enlazados.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="communications-new-thread"
        @click="openThreadModal"
      >
        <BaseActionIcon action="create" />
        Nuevo hilo
      </BaseButton>
    </header>

    <BaseAlert variant="info" class="mb-5" data-testid="communications-channel-scope">
      En esta fase el panel conserva el registro. Copia el texto a WhatsApp o a tu correo y luego marca
      la comunicación como enviada; el envío automático se incorporará en una fase posterior.
    </BaseAlert>

    <section class="mb-5 grid gap-3 rounded-xl border border-border-muted bg-surface p-4 md:grid-cols-4">
      <BaseInput
        v-model="filters.q"
        placeholder="Buscar cliente, asunto o texto..."
        aria-label="Buscar comunicaciones"
        data-testid="communications-search"
        @keyup.enter="applyFilters"
      />
      <BaseSelect
        v-model="filters.status"
        :options="THREAD_STATUS_OPTIONS"
        aria-label="Estado del hilo"
        data-testid="communications-status-filter"
        @update:model-value="applyFilters"
      />
      <BaseSelect
        v-model="filters.channel"
        :options="CHANNEL_FILTER_OPTIONS"
        aria-label="Canal"
        data-testid="communications-channel-filter"
        @update:model-value="applyFilters"
      />
      <div class="flex gap-2">
        <BaseSelect
          v-model="filters.direction"
          :options="DIRECTION_FILTER_OPTIONS"
          class="min-w-0 flex-1"
          aria-label="Dirección"
          data-testid="communications-direction-filter"
          @update:model-value="applyFilters"
        />
        <BaseButton variant="secondary" size="md" @click="applyFilters">Buscar</BaseButton>
      </div>
    </section>

    <BaseAlert v-if="store.error" variant="danger" class="mb-5">
      No se pudieron completar los cambios. {{ store.error }}
    </BaseAlert>

    <div class="grid min-h-[34rem] gap-4 lg:grid-cols-[minmax(18rem,0.85fr)_minmax(0,1.65fr)]">
      <section
        v-show="!isCompactDetail"
        class="overflow-hidden rounded-xl border border-border-muted bg-surface"
        aria-label="Hilos de comunicación"
      >
        <div class="flex items-center justify-between border-b border-border-muted px-4 py-3">
          <div>
            <h2 class="text-sm font-semibold text-text-default">Hilos</h2>
            <p class="text-xs text-text-subtle">{{ store.count }} en total</p>
          </div>
          <BaseButton
            variant="ghost"
            size="sm"
            :loading="store.isLoading"
            aria-label="Actualizar hilos"
            @click="loadThreads"
          >
            Actualizar
          </BaseButton>
        </div>

        <div v-if="store.isLoading && store.threads.length === 0" class="space-y-3 p-4">
          <BaseSkeleton v-for="index in 4" :key="index" class="h-24 rounded-xl" />
        </div>
        <BaseEmptyState
          v-else-if="store.threads.length === 0"
          title="No hay hilos con estos filtros"
          description="Cambia los filtros o registra la primera conversación."
          class="m-4"
        >
          <template #actions>
            <BaseButton variant="primary" size="sm" @click="openThreadModal">
              Crear hilo
            </BaseButton>
          </template>
        </BaseEmptyState>
        <div v-else class="divide-y divide-border-muted" data-testid="communications-thread-list">
          <!-- design-tokens: allow-raw-button -->
          <button
            v-for="thread in store.threads"
            :key="thread.id"
            type="button"
            class="block w-full px-4 py-4 text-left transition-colors hover:bg-surface-raised focus:outline-none focus:ring-2 focus:ring-inset focus:ring-focus-ring/40"
            :class="selectedThreadId === thread.id ? 'bg-primary-soft' : ''"
            :data-testid="`communication-thread-${thread.id}`"
            @click="selectThread(thread.id)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="max-w-full truncate text-sm font-semibold text-text-default" :title="thread.title">{{ thread.title }}</p>
                <p
                  class="mt-0.5 max-w-full truncate text-xs text-text-muted"
                  :title="thread.project_name ? `${thread.client_name} · ${thread.project_name}` : thread.client_name"
                >
                  {{ thread.client_name }}<template v-if="thread.project_name"> · {{ thread.project_name }}</template>
                </p>
              </div>
              <BaseBadge :variant="thread.status === 'open' ? 'success' : 'neutral'" size="sm">
                {{ thread.status === 'open' ? 'Abierto' : 'Cerrado' }}
              </BaseBadge>
            </div>
            <p v-if="thread.latest_message" class="mt-3 line-clamp-2 min-w-0 max-w-full text-xs text-text-subtle [overflow-wrap:anywhere]">
              {{ thread.latest_message.direction === 'incoming' ? 'Cliente:' : 'Nosotros:' }}
              {{ thread.latest_message.content }}
            </p>
            <div class="mt-3 flex flex-wrap items-center gap-2 text-2xs text-text-subtle">
              <span>{{ thread.messages_count }} mensaje{{ thread.messages_count === 1 ? '' : 's' }}</span>
              <span v-if="thread.draft_count" class="rounded-full bg-warning-soft px-2 py-0.5 text-warning-strong">
                {{ thread.draft_count }} borrador{{ thread.draft_count === 1 ? '' : 'es' }}
              </span>
              <span class="ml-auto">{{ formatDateTime(thread.last_activity_at) }}</span>
            </div>
          </button>
        </div>

        <div v-if="store.numPages > 1" class="flex items-center justify-between border-t border-border-muted p-3">
          <BaseButton
            variant="secondary"
            size="sm"
            :disabled="store.page <= 1"
            @click="changePage(store.page - 1)"
          >
            Anterior
          </BaseButton>
          <span class="text-xs text-text-subtle">{{ store.page }} / {{ store.numPages }}</span>
          <BaseButton
            variant="secondary"
            size="sm"
            :disabled="store.page >= store.numPages"
            @click="changePage(store.page + 1)"
          >
            Siguiente
          </BaseButton>
        </div>
      </section>

      <section
        v-show="!isPhone || isCompactDetail"
        class="flex min-w-0 flex-col overflow-hidden rounded-xl border border-border-muted bg-surface"
        aria-label="Detalle del hilo"
      >
        <BaseEmptyState
          v-if="!currentThread"
          title="Selecciona un hilo"
          description="Aquí verás el recorrido completo de la conversación."
          class="m-auto border-0"
        >
          <template #icon><ChatBubbleLeftRightIcon class="h-8 w-8" /></template>
        </BaseEmptyState>

        <template v-else>
          <header class="border-b border-border-muted px-4 py-4 sm:px-5">
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 items-start gap-2">
                <BaseActionButton
                  v-if="isPhone"
                  action="back"
                  variant="ghost"
                  size="sm"
                  label="Volver a los hilos"
                  @click="showCompactDetail = false"
                />
                <div class="min-w-0 flex-1">
                  <h2 class="min-w-0 max-w-full text-lg font-semibold text-text-default [overflow-wrap:anywhere]">{{ currentThread.title }}</h2>
                  <p class="mt-1 min-w-0 max-w-full text-sm text-text-muted [overflow-wrap:anywhere]">
                    <NuxtLink
                      :to="{ path: '/panel/clients', query: { client: currentThread.client_id } }"
                      class="text-text-brand hover:underline"
                    >
                      {{ currentThread.client_name }}
                    </NuxtLink>
                    <template v-if="currentThread.project_name"> · {{ currentThread.project_name }}</template>
                  </p>
                </div>
              </div>
              <BaseButton
                :variant="currentThread.status === 'open' ? 'secondary' : 'primary'"
                size="sm"
                :loading="store.isMutating"
                :data-testid="`communication-thread-toggle-${currentThread.id}`"
                @click="toggleThread"
              >
                {{ currentThread.status === 'open' ? 'Cerrar hilo' : 'Reabrir hilo' }}
              </BaseButton>
            </div>
          </header>

          <div class="flex-1 space-y-4 overflow-y-auto bg-surface-muted p-4 sm:p-5" data-testid="communication-timeline">
            <BaseEmptyState
              v-if="currentThread.messages.length === 0"
              title="Este hilo todavía no tiene mensajes"
              description="Registra lo enviado o la respuesta del cliente para iniciar el histórico."
            />
            <template v-else>
            <article
              v-for="message in currentThread.messages"
              :key="message.id"
              :id="`communication-message-${message.id}`"
              class="max-w-[92%] rounded-xl border p-4 shadow-sm sm:max-w-[82%]"
              :class="[
                message.direction === 'outgoing'
                  ? 'ml-auto border-primary/20 bg-primary-soft'
                  : 'mr-auto border-border-default bg-surface',
                message.voided_at ? 'opacity-60' : '',
              ]"
              :data-testid="`communication-message-${message.id}`"
            >
              <div class="flex flex-wrap items-center gap-2">
                <BaseBadge :variant="channelTone(message.channel)" size="sm">
                  {{ message.channel_display }}
                </BaseBadge>
                <BaseBadge :variant="messageStatusTone(message)" size="sm">
                  {{ messageStatusLabel(message) }}
                </BaseBadge>
                <span class="ml-auto text-2xs text-text-subtle">{{ formatDateTime(message.occurred_at) }}</span>
              </div>
              <p v-if="message.subject" class="mt-3 min-w-0 max-w-full text-sm font-semibold text-text-default [overflow-wrap:anywhere]">
                {{ message.subject }}
              </p>
              <a
                v-if="message.reply_to_id"
                :href="`#communication-message-${message.reply_to_id}`"
                class="mt-2 block rounded-lg border border-border-muted bg-surface/70 px-3 py-2 text-xs text-text-subtle hover:border-border-default hover:text-text-default"
              >
                <span class="font-semibold">En respuesta al mensaje #{{ message.reply_to_id }}</span>
                <span v-if="replyOriginPreview(message)" class="ml-1">
                  · “{{ replyOriginPreview(message) }}”
                </span>
              </a>
              <p class="mt-2 min-w-0 max-w-full whitespace-pre-wrap text-sm text-text-default [overflow-wrap:anywhere]">{{ message.content }}</p>

              <div v-if="message.documents.length" class="mt-3 space-y-1 border-t border-border-muted pt-3">
                <p class="text-2xs font-semibold uppercase tracking-wide text-text-subtle">Documentos referenciados</p>
                <BaseButton
                  v-for="document in message.documents"
                  :key="document.id"
                  as="NuxtLink"
                  :to="`/panel/documents/${document.id}/edit`"
                  variant="link"
                  size="sm"
                  class="mr-3 max-w-full whitespace-normal [overflow-wrap:anywhere]"
                >
                  <BaseActionIcon action="view" /> {{ document.title }}
                </BaseButton>
              </div>

              <p v-if="message.voided_at" class="mt-3 text-xs text-danger-strong">
                Motivo: {{ message.void_reason }}
              </p>
              <details v-if="message.date_corrections.length" class="mt-3 text-xs text-text-subtle">
                <summary class="cursor-pointer">{{ message.date_corrections.length }} corrección(es) de fecha</summary>
                <ul class="mt-2 space-y-1">
                  <li v-for="correction in message.date_corrections" :key="correction.id">
                    {{ formatDateTime(correction.previous_occurred_at) }} →
                    {{ formatDateTime(correction.corrected_occurred_at) }} · {{ correction.reason }}
                  </li>
                </ul>
              </details>

              <div v-if="!message.voided_at" class="mt-4 flex flex-wrap gap-2 border-t border-border-muted pt-3">
                <BaseButton
                  v-if="message.direction === 'outgoing'"
                  variant="ghost"
                  size="sm"
                  @click="copyMessage(message)"
                >
                  <BaseActionIcon action="copy" /> Copiar
                </BaseButton>
                <BaseButton
                  v-if="message.status === 'draft'"
                  variant="ghost"
                  size="sm"
                  @click="editDraft(message)"
                >
                  Editar
                </BaseButton>
                <BaseButton
                  v-if="message.status === 'draft' && message.direction === 'outgoing'"
                  variant="primary"
                  size="sm"
                  :loading="store.isMutating"
                  :data-testid="`communication-mark-sent-${message.id}`"
                  @click="markSent(message)"
                >
                  Marcar enviado
                </BaseButton>
                <BaseButton
                  v-if="message.status === 'draft'"
                  variant="danger-ghost"
                  size="sm"
                  @click="deleteDraft(message)"
                >
                  Eliminar
                </BaseButton>
                <BaseButton
                  v-else
                  variant="ghost"
                  size="sm"
                  @click="openCorrectionModal(message)"
                >
                  Corregir fecha
                </BaseButton>
                <BaseButton
                  v-if="message.status !== 'draft'"
                  variant="ghost"
                  size="sm"
                  @click="replyTo(message)"
                >
                  Responder
                </BaseButton>
                <BaseButton
                  v-if="message.status !== 'draft'"
                  variant="danger-ghost"
                  size="sm"
                  @click="openVoidModal(message)"
                >
                  Anular
                </BaseButton>
              </div>
            </article>
            </template>
          </div>

          <form
            v-if="currentThread.status === 'open'"
            ref="composerRef"
            class="border-t border-border-muted bg-surface p-4 sm:p-5"
            data-testid="communication-composer"
            @submit.prevent="submitMessage()"
          >
            <div v-if="messageForm.reply_to" class="mb-3 flex items-center justify-between rounded-lg bg-info-soft px-3 py-2 text-xs text-info-strong">
              <span>Respuesta al mensaje #{{ messageForm.reply_to }}</span>
              <BaseButton variant="ghost" size="sm" @click="messageForm.reply_to = null">Quitar</BaseButton>
            </div>
            <div class="grid gap-3 sm:grid-cols-3">
              <BaseFormField label="Dirección">
                <BaseSelect
                  v-model="messageForm.direction"
                  :options="DIRECTION_OPTIONS"
                  :disabled="Boolean(editingMessageId)"
                  data-testid="communication-message-direction"
                  @update:model-value="onDirectionChange"
                />
              </BaseFormField>
              <BaseFormField label="Canal">
                <BaseSelect
                  v-model="messageForm.channel"
                  :options="CHANNEL_OPTIONS"
                  data-testid="communication-message-channel"
                  @update:model-value="onChannelChange"
                />
              </BaseFormField>
              <BaseFormField label="Fecha y hora">
                <BaseInput v-model="messageForm.occurred_at" type="datetime-local" />
              </BaseFormField>
            </div>
            <BaseFormField v-if="messageForm.channel === 'email'" label="Asunto" class="mt-3">
              <BaseInput
                v-model="messageForm.subject"
                placeholder="Asunto del correo"
                data-testid="communication-message-subject"
              />
            </BaseFormField>
            <BaseFormField label="Contenido" class="mt-3">
              <BaseTextarea
                v-model="messageForm.content"
                :rows="4"
                placeholder="Escribe o pega el texto exacto de la comunicación..."
                data-testid="communication-message-content"
              />
            </BaseFormField>

            <details v-if="availableDocuments.length" class="mt-3 rounded-lg border border-border-muted p-3">
              <summary class="cursor-pointer text-sm font-medium text-text-default">
                Adjuntar documentos existentes ({{ messageForm.document_ids.length }} elegidos)
              </summary>
              <div class="mt-3 grid gap-2 sm:grid-cols-2">
                <BaseCheckbox
                  v-for="document in availableDocuments"
                  :key="document.id"
                  v-model="messageForm.document_ids"
                  :value="document.id"
                >
                  {{ document.title }}
                </BaseCheckbox>
              </div>
            </details>

            <div class="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <BaseButton
                v-if="editingMessageId"
                variant="secondary"
                size="md"
                @click="resetMessageForm"
              >
                Cancelar edición
              </BaseButton>
              <BaseButton
                v-if="editingMessageId"
                type="submit"
                variant="primary"
                size="md"
                :loading="store.isMutating"
              >
                Guardar cambios
              </BaseButton>
              <template v-else-if="messageForm.direction === 'outgoing'">
                <BaseButton
                  variant="secondary"
                  size="md"
                  :loading="store.isMutating"
                  data-testid="communication-save-draft"
                  @click="submitMessage('draft')"
                >
                  Guardar borrador
                </BaseButton>
                <BaseButton
                  variant="primary"
                  size="md"
                  :loading="store.isMutating"
                  data-testid="communication-register-sent"
                  @click="submitMessage('sent')"
                >
                  Registrar enviado
                </BaseButton>
              </template>
              <BaseButton
                v-else
                type="submit"
                variant="primary"
                size="md"
                :loading="store.isMutating"
                data-testid="communication-register-received"
              >
                Registrar respuesta recibida
              </BaseButton>
            </div>
          </form>
        </template>
      </section>
    </div>

    <BaseModal v-model="threadModalOpen" kind="form" padding="none">
      <form @submit.prevent="createThread">
        <div class="border-b border-border-muted px-5 py-4 sm:px-6">
          <h2 class="text-lg font-semibold text-text-default">Nuevo hilo de comunicación</h2>
          <p class="mt-1 text-sm text-text-subtle">Un cliente puede mantener varios hilos abiertos a la vez.</p>
        </div>
        <div class="space-y-4 px-5 py-5 sm:px-6">
          <BaseFormField label="Cliente">
            <ClientAutocomplete
              v-model="threadForm.client"
              :initial-label="threadForm.clientLabel"
              placeholder="Buscar cliente..."
              test-id="communication-thread-client"
              @select="onThreadClientSelect"
            />
          </BaseFormField>
          <ProjectSelect
            v-model="threadForm.project"
            :client-profile-id="threadForm.client"
            :client-label="threadForm.clientLabel"
            :allow-create="false"
            label="Proyecto (opcional)"
            testid="communication-thread-project"
          />
          <BaseFormField label="Título">
            <BaseInput
              v-model="threadForm.title"
              placeholder="Ej. Aprobación del alcance de la fase 2"
              data-testid="communication-thread-title"
            />
          </BaseFormField>
        </div>
        <BaseModalActions>
          <BaseButton variant="secondary" size="md" @click="threadModalOpen = false">Cancelar</BaseButton>
          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            :disabled="!threadForm.client || !threadForm.title.trim()"
            :loading="store.isMutating"
            data-testid="communication-thread-create-submit"
          >
            Crear hilo
          </BaseButton>
        </BaseModalActions>
      </form>
    </BaseModal>

    <BaseModal v-model="actionModal.open" kind="confirm" padding="none">
      <form @submit.prevent="submitActionModal">
        <div class="border-b border-border-muted px-5 py-4 sm:px-6">
          <h2 class="text-lg font-semibold text-text-default">
            {{ actionModal.kind === 'void' ? 'Anular mensaje' : 'Corregir fecha' }}
          </h2>
        </div>
        <div class="space-y-4 px-5 py-5 sm:px-6">
          <BaseFormField v-if="actionModal.kind === 'date'" label="Fecha y hora corregida">
            <BaseInput v-model="actionModal.occurred_at" type="datetime-local" />
          </BaseFormField>
          <BaseFormField label="Motivo" hint="Quedará guardado en el histórico de auditoría.">
            <BaseTextarea v-model="actionModal.reason" :rows="3" data-testid="communication-action-reason" />
          </BaseFormField>
        </div>
        <BaseModalActions>
          <BaseButton variant="secondary" size="md" @click="actionModal.open = false">Cancelar</BaseButton>
          <BaseButton
            type="submit"
            :variant="actionModal.kind === 'void' ? 'danger' : 'primary'"
            size="md"
            :disabled="!actionModal.reason.trim()"
            :loading="store.isMutating"
            data-testid="communication-action-submit"
          >
            {{ actionModal.kind === 'void' ? 'Anular mensaje' : 'Guardar corrección' }}
          </BaseButton>
        </BaseModalActions>
      </form>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { ChatBubbleLeftRightIcon } from '@heroicons/vue/24/outline';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectSelect from '~/components/accounting/ProjectSelect.vue';
import { useIsMobile } from '~/composables/useIsMobile';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { PANEL_BREAKPOINTS } from '~/config/responsive';
import { useCommunicationsStore } from '~/stores/communications';
import { useDocumentStore } from '~/stores/documents';
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const store = useCommunicationsStore();
const documentStore = useDocumentStore();
const notify = usePanelNotify();
const { isMobile: isPhone } = useIsMobile(PANEL_BREAKPOINTS.portrait - 1);

const selectedThreadId = ref(null);
const showCompactDetail = ref(false);
const threadModalOpen = ref(false);
const composerRef = ref(null);
const editingMessageId = ref(null);
const availableDocuments = computed(() => documentStore.documents || []);
const currentThread = computed(() => store.currentThread);
const isCompactDetail = computed(() => isPhone.value && showCompactDetail.value);

const filters = reactive({
  q: '',
  status: '',
  channel: '',
  direction: '',
  page: 1,
  client: route.query.client || '',
  project: route.query.project || '',
});

const THREAD_STATUS_OPTIONS = [
  { value: '', label: 'Todos los estados' },
  { value: 'open', label: 'Abiertos' },
  { value: 'closed', label: 'Cerrados' },
];
const CHANNEL_FILTER_OPTIONS = [
  { value: '', label: 'Todos los canales' },
  { value: 'email', label: 'Correo' },
  { value: 'whatsapp', label: 'WhatsApp' },
];
const DIRECTION_FILTER_OPTIONS = [
  { value: '', label: 'Ambas direcciones' },
  { value: 'outgoing', label: 'Salientes' },
  { value: 'incoming', label: 'Entrantes' },
];
const CHANNEL_OPTIONS = CHANNEL_FILTER_OPTIONS.slice(1);
const DIRECTION_OPTIONS = DIRECTION_FILTER_OPTIONS.slice(1);

const threadForm = reactive({
  client: route.query.client ? Number(route.query.client) : null,
  clientLabel: '',
  project: route.query.project ? Number(route.query.project) : null,
  title: '',
});

function localDateTime(date = new Date()) {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

const messageForm = reactive({
  direction: 'outgoing',
  channel: 'whatsapp',
  subject: '',
  content: '',
  occurred_at: localDateTime(),
  reply_to: null,
  document_ids: [],
});

const actionModal = reactive({
  open: false,
  kind: 'date',
  messageId: null,
  occurred_at: '',
  reason: '',
});

function requestFilters() {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== '' && value != null),
  );
}

async function loadThreads() {
  const result = await store.fetchThreads(requestFilters());
  if (!result.success) return;
  if (selectedThreadId.value && !store.getThreadById(selectedThreadId.value)) {
    selectedThreadId.value = null;
    store.currentThread = null;
  }
}

async function applyFilters() {
  filters.page = 1;
  await loadThreads();
}

async function changePage(page) {
  filters.page = page;
  await loadThreads();
}

async function selectThread(id) {
  selectedThreadId.value = id;
  showCompactDetail.value = true;
  const result = await store.fetchThread(id);
  if (!result.success) {
    notify.error({ title: 'No se pudo abrir el hilo', detail: result.message });
    return;
  }
  await loadDocumentsForThread();
}

async function loadDocumentsForThread() {
  if (!currentThread.value?.client_id) return;
  await documentStore.fetchDocuments({
    scope: 'all', client: currentThread.value.client_id, project: null,
  });
}

function openThreadModal() {
  threadForm.client = route.query.client ? Number(route.query.client) : null;
  threadForm.project = route.query.project ? Number(route.query.project) : null;
  threadForm.clientLabel = '';
  threadForm.title = '';
  threadModalOpen.value = true;
}

function onThreadClientSelect(client) {
  threadForm.clientLabel = client?.name || '';
  threadForm.project = null;
}

async function createThread() {
  const result = await store.createThread({
    client: threadForm.client,
    project: threadForm.project || null,
    title: threadForm.title.trim(),
  });
  if (!result.success) {
    notify.error({ title: 'No se pudo crear el hilo', detail: result.message });
    return;
  }
  threadModalOpen.value = false;
  selectedThreadId.value = result.data.id;
  showCompactDetail.value = true;
  await loadDocumentsForThread();
  notify.success({ title: 'Hilo creado' });
}

async function toggleThread() {
  const shouldOpen = currentThread.value.status === 'closed';
  const result = await store.setThreadOpen(currentThread.value.id, shouldOpen);
  if (!result.success) {
    notify.error({ title: shouldOpen ? 'No se pudo reabrir' : 'No se pudo cerrar', detail: result.message });
    return;
  }
  notify.success({ title: shouldOpen ? 'Hilo reabierto' : 'Hilo cerrado' });
}

function onDirectionChange(direction) {
  if (direction === 'incoming' && messageForm.reply_to) {
    const original = currentThread.value?.messages.find((item) => item.id === messageForm.reply_to);
    if (original?.direction === 'incoming') messageForm.reply_to = null;
  }
}

function onChannelChange(channel) {
  if (channel === 'whatsapp') messageForm.subject = '';
}

function resetMessageForm() {
  editingMessageId.value = null;
  Object.assign(messageForm, {
    direction: 'outgoing',
    channel: 'whatsapp',
    subject: '',
    content: '',
    occurred_at: localDateTime(),
    reply_to: null,
    document_ids: [],
  });
}

function messagePayload(statusOverride) {
  return {
    direction: messageForm.direction,
    channel: messageForm.channel,
    subject: messageForm.channel === 'email' ? messageForm.subject.trim() : '',
    content: messageForm.content.trim(),
    occurred_at: new Date(messageForm.occurred_at).toISOString(),
    reply_to: messageForm.reply_to,
    document_ids: [...messageForm.document_ids],
    ...(statusOverride ? { status: statusOverride } : {}),
  };
}

async function submitMessage(statusOverride = null) {
  if (!messageForm.content.trim()) {
    notify.warning({ title: 'Escribe el contenido del mensaje' });
    return;
  }
  if (messageForm.channel === 'email' && !messageForm.subject.trim()) {
    notify.warning({ title: 'El asunto es obligatorio para correo' });
    return;
  }
  const payload = messagePayload(
    messageForm.direction === 'incoming' ? 'received' : statusOverride,
  );
  const wasEditing = Boolean(editingMessageId.value);
  const result = editingMessageId.value
    ? await store.updateDraft(editingMessageId.value, payload)
    : await store.createMessage(currentThread.value.id, payload);
  if (!result.success) {
    notify.error({ title: 'No se pudo guardar el mensaje', detail: result.message });
    return;
  }
  resetMessageForm();
  await loadThreads();
  notify.success({
    title: wasEditing
      ? 'Borrador actualizado'
      : (payload.status === 'draft' ? 'Borrador guardado' : 'Mensaje registrado'),
  });
}

function editDraft(message) {
  editingMessageId.value = message.id;
  Object.assign(messageForm, {
    direction: message.direction,
    channel: message.channel,
    subject: message.subject || '',
    content: message.content,
    occurred_at: localDateTime(new Date(message.occurred_at)),
    reply_to: message.reply_to_id,
    document_ids: message.documents.map((document) => document.id),
  });
  nextTick(() => composerRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' }));
}

async function deleteDraft(message) {
  if (typeof window !== 'undefined' && !window.confirm('¿Eliminar este borrador?')) return;
  const result = await store.deleteDraft(message);
  if (!result.success) {
    notify.error({ title: 'No se pudo eliminar el borrador', detail: result.message });
    return;
  }
  await loadThreads();
  notify.success({ title: 'Borrador eliminado' });
}

async function markSent(message) {
  const result = await store.markSent(message.id, new Date().toISOString());
  if (!result.success) {
    notify.error({ title: 'No se pudo marcar como enviado', detail: result.message });
    return;
  }
  await loadThreads();
  notify.success({ title: 'Mensaje marcado como enviado' });
}

function replyTo(message) {
  resetMessageForm();
  messageForm.reply_to = message.id;
  messageForm.direction = message.direction === 'incoming' ? 'outgoing' : 'incoming';
  messageForm.channel = message.channel;
  if (messageForm.channel === 'email' && message.subject) {
    messageForm.subject = message.subject.startsWith('Re:') ? message.subject : `Re: ${message.subject}`;
  }
  nextTick(() => composerRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' }));
}

async function copyMessage(message) {
  try {
    await navigator.clipboard.writeText(message.content);
    notify.success({ title: 'Texto copiado' });
  } catch {
    notify.error({ title: 'No se pudo copiar el texto' });
  }
}

function openCorrectionModal(message) {
  Object.assign(actionModal, {
    open: true,
    kind: 'date',
    messageId: message.id,
    occurred_at: localDateTime(new Date(message.occurred_at)),
    reason: '',
  });
}

function openVoidModal(message) {
  Object.assign(actionModal, {
    open: true,
    kind: 'void',
    messageId: message.id,
    occurred_at: '',
    reason: '',
  });
}

async function submitActionModal() {
  const result = actionModal.kind === 'void'
    ? await store.voidMessage(actionModal.messageId, actionModal.reason)
    : await store.correctDate(
      actionModal.messageId,
      new Date(actionModal.occurred_at).toISOString(),
      actionModal.reason,
    );
  if (!result.success) {
    notify.error({ title: 'No se pudo actualizar el histórico', detail: result.message });
    return;
  }
  actionModal.open = false;
  await loadThreads();
  notify.success({ title: actionModal.kind === 'void' ? 'Mensaje anulado' : 'Fecha corregida' });
}

function formatDateTime(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium', timeStyle: 'short',
  }).format(new Date(value));
}

function statusTone(status) {
  return ({ draft: 'warning', sent: 'success', received: 'info', failed: 'danger' })[status] || 'neutral';
}

function messageStatusLabel(message) {
  if (message.voided_at) return 'Anulado';
  if (message.direction === 'outgoing' && message.has_reply) return 'Respondido';
  return message.status_display;
}

function messageStatusTone(message) {
  if (message.voided_at) return 'neutral';
  if (message.direction === 'outgoing' && message.has_reply) return 'info';
  return statusTone(message.status);
}

function replyOriginPreview(message) {
  if (!message.reply_to_id) return '';
  const origin = currentThread.value?.messages.find(
    (candidate) => candidate.id === message.reply_to_id,
  );
  if (!origin?.content) return '';
  return origin.content.length > 110
    ? `${origin.content.slice(0, 107)}…`
    : origin.content;
}

function channelTone(channel) {
  return channel === 'whatsapp' ? 'success' : 'info';
}

watch(
  () => route.query,
  async (query) => {
    filters.client = query.client || '';
    filters.project = query.project || '';
    await applyFilters();
  },
);

onMounted(async () => {
  await loadThreads();
  const requestedThread = Number(route.query.thread || 0);
  if (requestedThread) await selectThread(requestedThread);
  else if (store.threads.length === 1) await selectThread(store.threads[0].id);
});
</script>
