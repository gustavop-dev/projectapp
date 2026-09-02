<template>
  <BaseModal
    :model-value="modelValue"
    kind="workspace"
    full-height
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-shrink-0 items-center justify-between gap-3 border-b border-border-muted px-4 py-4 sm:px-6">
      <div class="min-w-0">
        <h2 class="truncate text-lg font-semibold text-text-default" data-testid="document-thread-index-title">
          Hilos de documentos
        </h2>
        <p class="mt-0.5 text-xs text-text-subtle">
          {{ threadStore.threadCount }} hilos · cada documento pertenece a uno solo
        </p>
      </div>
      <BaseActionButton action="close" label="Cerrar hilos de documentos" @click="emit('update:modelValue', false)" />
    </div>

    <div class="flex flex-shrink-0 flex-col gap-3 px-4 pt-4 sm:flex-row sm:items-center sm:px-6">
      <input
        v-model="search"
        type="search"
        placeholder="Buscar hilo o documento…"
        class="w-full rounded-xl border border-border-default bg-surface px-3 py-2.5 text-sm text-text-default outline-none focus:border-focus-ring focus:ring-2 focus:ring-focus-ring/30"
        data-testid="document-thread-index-search"
      >
      <BaseSegmented
        v-model="order"
        size="sm"
        :options="orderOptions"
      />
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6">
      <BaseAlert v-if="loadError" variant="danger" title="No se pudieron cargar los hilos" class="mb-4">
        {{ loadError }}
      </BaseAlert>

      <div v-if="threadStore.isLoadingThreads" class="py-10 text-center text-sm text-text-subtle" role="status">
        Cargando hilos…
      </div>
      <BaseEmptyState
        v-else-if="!threadStore.threads.length"
        title="No hay hilos"
        :description="search
          ? 'Ningún hilo coincide con esa búsqueda.'
          : 'Enlaza dos documentos relacionados desde el menú de acciones para crear el primero.'"
      />
      <ul v-else class="space-y-2" data-testid="document-thread-index-rows">
        <li v-for="row in threadStore.threads" :key="row.id">
          <!-- design-tokens: allow-raw-button — fila de hilo seleccionable -->
          <button
            type="button"
            class="w-full rounded-xl border border-border-muted bg-surface p-3 text-left transition-colors hover:border-border-default"
            :data-testid="`thread-index-row-${row.id}`"
            @click="openThread(row)"
          >
            <span class="flex min-w-0 items-center gap-2">
              <span class="min-w-0 flex-1 truncate text-sm font-medium text-text-default">{{ row.title }}</span>
              <BaseBadge variant="info" size="sm">Hilo · {{ row.document_count }}</BaseBadge>
            </span>
            <span class="mt-0.5 block truncate text-xs text-text-subtle">{{ spanLine(row) }}</span>
            <span class="mt-1 block truncate text-xs text-text-muted">{{ membersLine(row) }}</span>
          </button>
        </li>
      </ul>
    </div>

    <div class="flex-shrink-0 border-t border-border-muted px-4 py-3 sm:px-6">
      <BasePagination
        :current-page="page"
        :total-pages="totalPages"
        :total-items="threadStore.threadCount"
        :range-from="rangeFrom"
        :range-to="rangeTo"
        aria-label="Hilos de documentos"
        @prev="goToPage(page - 1)"
        @next="goToPage(page + 1)"
        @go="goToPage"
      />
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useDocumentThreadStore } from '~/stores/document_threads';

const PAGE_SIZE = 20;

const props = defineProps({
  modelValue: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'open-thread']);

const threadStore = useDocumentThreadStore();
const search = ref('');
const order = ref('recent');
const page = ref(1);
const loadError = ref('');
let searchTimer = null;

const orderOptions = [
  { value: 'recent', label: 'Reciente', testId: 'thread-order-recent' },
  { value: 'milestone', label: 'Último hito', testId: 'thread-order-milestone' },
  { value: 'title', label: 'A–Z', testId: 'thread-order-title' },
];

const totalPages = computed(() => Math.max(1, Math.ceil(threadStore.threadCount / PAGE_SIZE)));
const rangeFrom = computed(() => (
  threadStore.threadCount ? ((page.value - 1) * PAGE_SIZE) + 1 : 0
));
const rangeTo = computed(() => Math.min(page.value * PAGE_SIZE, threadStore.threadCount));

function formatDate(value) {
  if (!value) return null;
  const [year, month, day] = String(value).slice(0, 10).split('-');
  return `${day}/${month}/${year}`;
}

function spanLine(row) {
  const first = formatDate(row.first_occurred_on);
  const last = formatDate(row.last_occurred_on);
  if (!first && !last) return 'Sin fechas registradas';
  if (first === last) return first;
  return `${first} → ${last}`;
}

function membersLine(row) {
  const titles = (row.documents || []).map(item => item.title);
  if (!titles.length) return '';
  return row.documents_truncated ? `${titles.join(' · ')} …` : titles.join(' · ');
}

async function load() {
  loadError.value = '';
  const result = await threadStore.fetchThreads({
    search: search.value,
    order: order.value,
    page: page.value,
    pageSize: PAGE_SIZE,
  });
  if (!result.success && !result.stale) loadError.value = result.message;
}

function goToPage(next) {
  if (next < 1 || next > totalPages.value || next === page.value) return;
  page.value = next;
  load();
}

// La fila del índice no trae el documento completo: el hilo se abre por su
// primer miembro, que es lo que el workspace existente necesita para hidratarse.
function openThread(row) {
  const first = (row.documents || [])[0];
  if (!first) return;
  emit('open-thread', { id: first.document_id, title: first.title });
}

watch([search, order], () => {
  page.value = 1;
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(load, 300);
});

watch(() => props.modelValue, (open) => {
  if (!open) return;
  page.value = 1;
  load();
}, { immediate: true });

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer);
});
</script>
