<template>
  <div :class="[PAGE_MAX_WIDTH, 'flex min-h-full flex-col']" data-testid="communications-page">
    <header class="mb-4 flex flex-col gap-3 panel-portrait:flex-row panel-portrait:items-start panel-portrait:justify-between">
      <div>
        <h1 class="text-2xl font-light text-text-default">Comunicaciones</h1>
        <p class="mt-1 max-w-3xl text-sm text-text-subtle">
          Registro por cliente de lo enviado y recibido, organizado por proyecto o por cliente.
        </p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        data-testid="communications-new-thread"
        @click="openThreadForm"
      >
        <BaseActionIcon action="create" />
        Nuevo hilo
      </BaseButton>
    </header>

    <BaseAlert
      v-if="noticeReady && showNotice"
      variant="info"
      dismissible
      class="mb-4"
      data-testid="communications-channel-scope"
      @dismiss="dismissNotice"
    >
      Este módulo conserva el registro manual de las conversaciones. Copia el texto a WhatsApp o a tu correo y registra aquí lo enviado o recibido.
    </BaseAlert>
    <div v-else-if="noticeReady" class="mb-3">
      <BaseButton variant="link" size="sm" data-testid="communications-show-help" @click="showNotice = true">
        Cómo funciona el registro manual
      </BaseButton>
    </div>

    <BaseFilterTabs
      :tabs="displayTabs"
      :active-tab-id="activeTabId"
      :counts="tabCounts"
      :is-tab-limit-reached="isTabLimitReached"
      count-title="Hilos que cumplen este filtro"
      show-config-tab
      :config-active="isConfigOpen"
      @select="handleSelectTab"
      @create="handleCreateTab"
      @rename="renameTab"
      @delete="deleteTab"
      @restore="restoreTab"
      @rebase="rebaseTab"
      @reorder="reorderTabs"
      @config="isConfigOpen = true"
    />

    <ViewSettingsPanel
      v-if="isConfigOpen"
      :filter-views="[{ value: 'communication', label: 'Comunicaciones' }]"
      @reset="handleResetTabs"
    />

    <template v-else>
    <div class="mb-4 flex flex-col gap-3 rounded-xl border border-border-muted bg-surface p-3 panel-portrait:flex-row panel-portrait:items-center">
      <BaseInput
        v-model="searchInput"
        class="min-w-0 flex-1"
        placeholder="Buscar cliente, proyecto, asunto o texto..."
        aria-label="Buscar comunicaciones"
        data-testid="communications-search"
      />
      <BaseButton
        :variant="isFilterPanelOpen || activeFilterCount ? 'primary' : 'secondary'"
        size="md"
        data-testid="communications-filter-toggle"
        :aria-expanded="isFilterPanelOpen"
        @click="isFilterPanelOpen = !isFilterPanelOpen"
      >
        <BaseActionIcon action="filter" />
        Filtros<span v-if="activeFilterCount"> ({{ activeFilterCount }})</span>
      </BaseButton>
      <BaseSegmented
        :model-value="currentFilters.order"
        :options="ORDER_OPTIONS"
        size="sm"
        aria-label="Orden de los hilos"
        @update:model-value="setOrder"
      />
      <BaseActionButton
        action="refresh"
        label="Actualizar hilos"
        size="md"
        :loading="store.isLoading"
        @click="reloadThreadsAndCounts"
      />
    </div>

    <CommunicationFilterPanel
      :model-value="currentFilters"
      :facets="store.facets"
      :is-open="isFilterPanelOpen"
      :results-count="store.count"
      :search-value="currentFilters.q.trim()"
      @update:model-value="updateFilters"
      @clear-search="searchInput = ''"
      @reset="clearFilters"
    />

    <BaseAlert v-if="store.error" variant="danger" class="mb-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <span>No se pudieron cargar las comunicaciones. {{ store.error }}</span>
        <BaseButton variant="secondary" size="sm" @click="loadThreads">Reintentar</BaseButton>
      </div>
    </BaseAlert>

    <BaseButton
      v-if="isPanelStacked"
      variant="secondary"
      size="md"
      class="mb-4 w-full justify-between"
      data-testid="communications-navigation-drawer-trigger"
      aria-haspopup="dialog"
      :aria-expanded="navigationDrawerOpen"
      @click="navigationDrawerOpen = true"
    >
      <span class="flex min-w-0 items-center gap-2">
        <BaseActionIcon action="folders" />
        <span class="truncate">{{ compactNavigationLabel }}</span>
      </span>
      <span class="shrink-0 text-xs font-medium text-text-brand">Cambiar</span>
    </BaseButton>

    <div
      ref="navigationGridRef"
      class="grid min-h-[32rem] flex-1 grid-cols-1 items-stretch gap-6 panel-landscape:grid-cols-[var(--communications-panel-w,18rem)_1.5rem_minmax(0,1fr)] panel-landscape:gap-0"
      :class="panelDragging ? 'select-none' : ''"
      :style="panelGridStyle"
    >
      <CommunicationNavigation
        v-if="!isPanelStacked"
        :mode="currentFilters.by"
        :selection="navigationSelection"
        :facets="store.facets"
        data-testid="communications-navigation-panel"
        @update:mode="setMode"
        @select="selectNavigation"
      />

      <BaseResizeHandle
        v-if="!isPanelStacked"
        :value="panelWidth"
        :min="COMMUNICATION_PANEL_MIN"
        :max="COMMUNICATION_PANEL_MAX"
        label="Ajustar el ancho de la navegación de comunicaciones"
        test-id="communications-navigation-resize-handle"
        @pointer-start="onHandleDown"
        @pointer-move="onHandleMove"
        @pointer-end="onHandleUp"
        @resize="resizePanelWidth"
        @reset="resetPanelWidth"
      />

      <section class="min-w-0">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-sm font-semibold text-text-default">Hilos</h2>
            <p class="text-xs text-text-subtle">{{ store.count }} en este recorte</p>
          </div>
        </div>

        <BaseEmptyState
          v-if="!store.isLoading && store.threads.length === 0"
          title="No hay hilos con este recorte"
          description="Cambia la navegación o los filtros, o registra una conversación."
          class="rounded-xl border border-border-muted bg-surface"
        >
          <template #actions>
            <BaseButton variant="primary" size="sm" @click="openThreadForm">Crear hilo</BaseButton>
          </template>
        </BaseEmptyState>
        <CommunicationThreadTable
          v-else
          :threads="store.threads"
          :loading="store.isLoading"
          :search-query="currentFilters.q"
          :href-for="threadHref"
          @open="openThreadFromRow"
          @link-activate="markLinkActivation"
        />

        <BasePagination
          v-if="store.numPages > 1"
          class="mt-4"
          :current-page="store.page"
          :total-pages="store.numPages"
          :total-items="store.count"
          :range-from="(store.page - 1) * 20 + 1"
          :range-to="Math.min(store.page * 20, store.count)"
          @prev="page = Math.max(1, page - 1)"
          @next="page = Math.min(store.numPages, page + 1)"
          @go="page = $event"
        />
      </section>
    </div>

    <BaseDrawer
      v-model="navigationDrawerOpen"
      placement="left"
      :title="currentFilters.by === 'project' ? 'Proyectos' : 'Clientes'"
      test-id="communications-navigation-drawer"
    >
      <div class="h-full p-3">
        <CommunicationNavigation
          :mode="currentFilters.by"
          :selection="navigationSelection"
          :facets="store.facets"
          @update:mode="handleDrawerMode"
          @select="handleDrawerSelection"
        />
      </div>
    </BaseDrawer>
    </template>

    <CommunicationWorkspaceModal
      :model-value="workspaceOpen"
      :thread-id="requestedThreadId"
      @update:model-value="handleWorkspaceOpenChange"
      @changed="reloadThreadsAndCounts"
    />

    <BaseModal v-model="threadFormOpen" kind="form" padding="none">
      <form novalidate @submit.prevent="createThread">
        <div class="border-b border-border-muted px-5 py-4 panel-portrait:px-6">
          <h2 class="text-lg font-semibold text-text-default">Nuevo hilo de comunicación</h2>
          <p class="mt-1 text-sm text-text-subtle">Un cliente puede mantener varios hilos abiertos a la vez.</p>
        </div>
        <div class="space-y-4 px-5 py-5 panel-portrait:px-6">
          <BaseFormField
            v-slot="{ invalid, errorId }"
            label="Cliente"
            required
            :error="threadFormErrors.client"
          >
            <ClientAutocomplete
              v-model="threadForm.client"
              :initial-label="threadForm.clientLabel"
              placeholder="Buscar cliente..."
              test-id="communication-thread-client"
              :error="invalid"
              :error-described-by="errorId"
              @select="onThreadClientSelect"
            />
          </BaseFormField>
          <ProjectSelect
            v-model="threadForm.project"
            :client-profile-id="threadForm.client"
            :client-label="threadForm.clientLabel"
            :allow-create="false"
            label="Proyecto"
            testid="communication-thread-project"
          />
          <BaseFormField
            v-slot="{ invalid, errorId }"
            label="Título"
            required
            :error="threadFormErrors.title"
          >
            <BaseInput
              v-model="threadForm.title"
              placeholder="Ej. Aprobación del alcance de la fase 2"
              data-testid="communication-thread-title"
              :error="invalid"
              :aria-describedby="errorId"
              @update:model-value="clearThreadFormError('title')"
            />
          </BaseFormField>
        </div>
        <BaseModalActions>
          <BaseButton type="button" variant="secondary" size="md" @click="threadFormOpen = false">Cancelar</BaseButton>
          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            :loading="store.isMutating"
            data-testid="communication-thread-create-submit"
          >
            Crear hilo
          </BaseButton>
        </BaseModalActions>
      </form>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectSelect from '~/components/accounting/ProjectSelect.vue';
import CommunicationFilterPanel from '~/components/communications/CommunicationFilterPanel.vue';
import CommunicationNavigation from '~/components/communications/CommunicationNavigation.vue';
import CommunicationThreadTable from '~/components/communications/CommunicationThreadTable.vue';
import CommunicationWorkspaceModal from '~/components/communications/CommunicationWorkspaceModal.vue';
import ViewSettingsPanel from '~/components/panel/ViewSettingsPanel.vue';
import { useCommunicationFilters } from '~/composables/useCommunicationFilters';
import { useDetailQueryParam } from '~/composables/useDetailQueryParam';
import {
  COMMUNICATION_PANEL_MAX,
  COMMUNICATION_PANEL_MIN,
  useCommunicationPanelWidth,
} from '~/composables/useCommunicationPanelWidth';
import { useIsMobile } from '~/composables/useIsMobile';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useRowNavigation } from '~/composables/useRowNavigation';
import { PANEL_BREAKPOINTS } from '~/config/responsive';
import { useCommunicationsStore } from '~/stores/communications';
import { isPlainActivation } from '~/utils/rowNavigation';
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const NOTICE_KEY = 'projectapp-communications-manual-notice-v1';
const ORDER_OPTIONS = [
  { value: 'recent', label: 'Recientes', testId: 'communications-order-recent' },
  { value: 'oldest', label: 'Antiguos', testId: 'communications-order-oldest' },
  { value: 'title', label: 'A–Z', testId: 'communications-order-title' },
];

const route = useRoute();
const router = useRouter();
const store = useCommunicationsStore();
const notify = usePanelNotify();
const { openRow } = useRowNavigation();
const {
  currentFilters,
  page,
  activeTabId,
  isFilterPanelOpen,
  searchInput,
  displayTabs,
  tabCountSpecs,
  navigationSelection,
  activeFilterCount,
  isTabLimitReached,
  setMode,
  selectNavigation,
  updateFilters,
  setOrder,
  clearFilters,
  selectTab,
  saveTab,
  deleteTab,
  renameTab,
  restoreTab,
  rebaseTab,
  reorderTabs,
  reloadTabs,
  requestFilters,
} = useCommunicationFilters();

const { isMobile: isPanelStacked } = useIsMobile(PANEL_BREAKPOINTS.landscape - 1);
const navigationGridRef = ref(null);
const {
  width: panelWidth,
  dragging: panelDragging,
  gridStyle: panelGridStyle,
  onHandleDown,
  onHandleMove,
  onHandleUp,
  resizeWidth: resizePanelWidth,
  resetWidth: resetPanelWidth,
} = useCommunicationPanelWidth(navigationGridRef);

const noticeReady = ref(false);
const showNotice = ref(false);
const isConfigOpen = ref(false);
const tabCounts = ref({});
let tabCountsRequestId = 0;
const navigationDrawerOpen = ref(false);
const threadFormOpen = ref(false);
const workspaceOpenedLocally = ref(false);
const {
  openId: requestedThreadId,
  isOpen: workspaceOpen,
  toFor: threadLocation,
  close: removeThreadFromUrl,
} = useDetailQueryParam('thread');

const threadForm = reactive({
  client: null,
  clientLabel: '',
  project: null,
  title: '',
});
const threadFormErrors = ref({});

function clearThreadFormError(field) {
  const nextErrors = { ...threadFormErrors.value };
  delete nextErrors[field];
  threadFormErrors.value = nextErrors;
}

const compactNavigationLabel = computed(() => {
  if (navigationSelection.value === 'all') {
    return currentFilters.by === 'project' ? 'Todos los proyectos' : 'Todos los clientes';
  }
  if (navigationSelection.value === 'none') return 'Sin proyecto';
  const entries = currentFilters.by === 'project' ? store.facets.projects : store.facets.clients;
  return entries.find((entry) => String(entry.id) === String(navigationSelection.value))?.name
    || (currentFilters.by === 'project' ? 'Proyecto seleccionado' : 'Cliente seleccionado');
});

const requestSignature = computed(() => JSON.stringify(requestFilters()));
watch(requestSignature, loadThreads, { immediate: true });
const tabCountSignature = computed(() => JSON.stringify(
  [...tabCountSpecs.value].sort((left, right) => String(left.id).localeCompare(String(right.id))),
));
watch(tabCountSignature, refreshTabCounts, { immediate: true });
watch(requestedThreadId, (threadId) => {
  if (!threadId) store.clearCurrentThread();
});

onMounted(() => {
  noticeReady.value = true;
  showNotice.value = localStorage.getItem(NOTICE_KEY) !== 'dismissed';
});

function dismissNotice() {
  showNotice.value = false;
  localStorage.setItem(NOTICE_KEY, 'dismissed');
}

async function loadThreads() {
  await store.fetchThreads(requestFilters());
}

async function refreshTabCounts() {
  const requestId = ++tabCountsRequestId;
  const result = await store.fetchTabCounts(tabCountSpecs.value);
  if (requestId === tabCountsRequestId && result.success) tabCounts.value = result.counts;
}

async function reloadThreadsAndCounts() {
  await Promise.all([loadThreads(), refreshTabCounts()]);
}

function handleSelectTab(tabId) {
  isConfigOpen.value = false;
  selectTab(tabId);
}

async function handleResetTabs() {
  await reloadTabs();
  await refreshTabCounts();
}

async function handleCreateTab(name) {
  const tab = await saveTab(name);
  if (tab) notify.success({ title: 'Vista guardada' });
  else notify.error({ title: 'No se pudo guardar la vista' });
}

function handleDrawerMode(mode) {
  setMode(mode);
}

function handleDrawerSelection(selection) {
  selectNavigation(selection);
  navigationDrawerOpen.value = false;
}

function threadHref(thread) {
  return router.resolve(threadLocation(thread.id)).href;
}

function openThreadFromRow(thread, event) {
  if (isPlainActivation(event)) workspaceOpenedLocally.value = true;
  openRow(threadHref(thread), event);
}

function markLinkActivation(_thread, event) {
  if (isPlainActivation(event)) workspaceOpenedLocally.value = true;
}

function handleWorkspaceOpenChange(open) {
  if (open) return;
  if (workspaceOpenedLocally.value) {
    workspaceOpenedLocally.value = false;
    router.back();
    return;
  }
  removeThreadFromUrl();
}

function selectedClientEntry(clientId) {
  return store.facets.clients.find((entry) => String(entry.id) === String(clientId));
}

function openThreadForm() {
  threadFormErrors.value = {};
  Object.assign(threadForm, {
    client: null,
    clientLabel: '',
    project: null,
    title: '',
  });

  if (currentFilters.by === 'client' && currentFilters.client) {
    const client = selectedClientEntry(currentFilters.client);
    threadForm.client = Number(currentFilters.client);
    threadForm.clientLabel = client?.name || '';
  } else if (currentFilters.by === 'project' && currentFilters.project && currentFilters.project !== 'none') {
    const project = store.facets.projects.find(
      (entry) => String(entry.id) === String(currentFilters.project),
    );
    if (project && !project.unavailable) {
      threadForm.project = Number(project.id);
      threadForm.client = Number(project.client_id);
      threadForm.clientLabel = selectedClientEntry(project.client_id)?.name || '';
    }
  }
  threadFormOpen.value = true;
}

function onThreadClientSelect(client) {
  clearThreadFormError('client');
  threadForm.clientLabel = client?.name || '';
  threadForm.project = null;
}

async function createThread() {
  threadFormErrors.value = {
    ...(!threadForm.client ? { client: 'Elige un cliente.' } : {}),
    ...(!threadForm.title.trim() ? { title: 'Escribe el título del hilo.' } : {}),
  };
  if (Object.keys(threadFormErrors.value).length) return;

  const result = await store.createThread({
    client: threadForm.client,
    project: threadForm.project || null,
    title: threadForm.title.trim(),
  });
  if (!result.success) {
    threadFormErrors.value = result.fieldErrors || {};
    if (Object.keys(threadFormErrors.value).length) return;
    notify.error({ title: 'No se pudo crear el hilo', detail: result.message });
    return;
  }
  threadFormOpen.value = false;
  await reloadThreadsAndCounts();
  workspaceOpenedLocally.value = true;
  await router.push(threadLocation(result.data.id));
  notify.success({ title: 'Hilo creado' });
}
</script>
