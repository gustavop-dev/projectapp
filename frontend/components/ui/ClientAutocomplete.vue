<template>
  <div ref="wrapperRef" class="relative">
    <!-- Input -->
    <div class="relative">
      <span
        class="absolute inset-y-0 left-0 flex items-center pl-3 text-text-subtle pointer-events-none"
      >
        <MagnifyingGlassIcon class="w-4 h-4" />
      </span>
      <input
        ref="inputRef"
        v-model="inputText"
        type="text"
        :placeholder="placeholder"
        :data-testid="testId"
        autocomplete="off"
        class="w-full pl-9 pr-9 py-2.5 border border-input-border bg-input-bg text-input-text placeholder:text-text-subtle rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
        @input="onInput"
        @focus="onFocus"
        @keydown.down.prevent="onArrowDown"
        @keydown.up.prevent="onArrowUp"
        @keydown.enter.prevent="onEnter"
        @keydown.esc.prevent="closeDropdown"
        role="combobox"
        :aria-expanded="isOpen"
        :aria-controls="isOpen ? listboxId : undefined"
        :aria-busy="isSearching || isLoadingMore"
        aria-autocomplete="list"
        aria-haspopup="listbox"
      />
      <!-- Clear button — visible when there's a selected client OR text typed -->
      <button
        v-if="modelValue || inputText"
        type="button"
        class="absolute inset-y-0 right-0 flex items-center pr-3 text-text-subtle hover:text-text-default transition-colors"
        :aria-label="$t ? $t('clients.autocomplete.clear') : 'Limpiar'"
        :title="$t ? $t('clients.autocomplete.clear') : 'Limpiar'"
        @click="clearSelection"
      >
        <BaseActionIcon action="clear" />
      </button>
    </div>

    <!-- Linked client hint (id beside the name) -->
    <p
      v-if="modelValue && showLinkedHint"
      class="text-xs text-text-subtle mt-1"
      data-testid="client-autocomplete-linked"
    >
      Cliente enlazado: {{ committedLabel }} <span class="tabular-nums">(#{{ modelValue }})</span>
    </p>

    <!-- Dropdown -->
    <BaseFloatingListbox
      :id="listboxId"
      :open="isOpen"
      :anchor="inputRef"
      :owner="wrapperRef"
      @close="closeDropdown"
      @reach-end="loadMore"
    >
      <!-- Loading -->
      <div
        v-if="isSearching"
        class="px-4 py-3 text-sm text-text-subtle text-center"
      >
        {{ inputText.trim() ? 'Buscando...' : 'Cargando clientes...' }}
      </div>

      <!-- Request failed before there was anything useful to show. -->
      <div
        v-else-if="searchError"
        class="space-y-2 px-4 py-3 text-sm text-text-muted"
        data-testid="client-autocomplete-error"
      >
        <p>No se pudo cargar la lista de clientes.</p>
        <button
          type="button"
          class="text-xs font-medium text-text-brand hover:underline"
          data-testid="client-autocomplete-retry"
          @click="retrySearch"
        >
          Reintentar
        </button>
      </div>

      <!-- Results -->
      <template v-else-if="results.length > 0">
        <ul class="divide-y divide-border-muted">
          <li
            v-for="(client, idx) in results"
            :key="client.id"
            :data-testid="`client-autocomplete-option-${client.id}`"
            :class="[
              'px-4 py-2.5 cursor-pointer transition-colors',
              highlightIndex === idx ? 'bg-primary-soft' : 'hover:bg-surface-raised',
            ]"
            role="option"
            :aria-selected="highlightIndex === idx"
            @click="selectClient(client)"
            @mouseenter="highlightIndex = idx"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <p class="font-medium text-text-default text-sm truncate">
                    {{ client.name }}
                    <span class="text-text-subtle font-normal tabular-nums">(#{{ client.id }})</span>
                  </p>
                  <span
                    v-if="clientHasNoEmail(client)"
                    class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong font-medium uppercase tracking-wide"
                    title="Este cliente todavía no tiene correo. Las acciones que envían mensajes pedirán agregarlo antes de continuar."
                  >
                    📧 Sin correo
                  </span>
                </div>
                <p class="text-xs text-text-muted truncate mt-0.5">
                  <span v-if="client.company">{{ client.company }} · </span>
                  {{ clientHasNoEmail(client) ? 'Correo pendiente · habrá que agregarlo para enviar' : client.email }}
                </p>
              </div>
              <p
                v-if="client.phone"
                class="text-xs text-text-subtle flex-shrink-0 tabular-nums"
              >
                {{ client.phone }}
              </p>
            </div>
          </li>
        </ul>
        <div
          v-if="isLoadingMore"
          class="border-t border-border-muted px-4 py-2 text-center text-xs text-text-subtle"
          data-testid="client-autocomplete-loading-more"
        >
          Cargando más clientes...
        </div>
        <div
          v-else-if="loadMoreError"
          class="flex items-center justify-between gap-3 border-t border-border-muted px-4 py-2 text-xs text-text-muted"
          data-testid="client-autocomplete-load-more-error"
        >
          <span>No se pudo cargar la siguiente página.</span>
          <button type="button" class="font-medium text-text-brand hover:underline" @click="loadMore">
            Reintentar
          </button>
        </div>
      </template>

      <!-- No results — offer to create -->
      <div v-else-if="hasSearched && inputText.trim()" class="px-4 py-3 text-sm text-text-muted">
        <p class="mb-2">No se encontraron clientes con "{{ inputText }}".</p>
        <button
          type="button"
          class="w-full text-left px-3 py-2 rounded-lg bg-primary-soft text-text-brand hover:opacity-90 transition-colors font-medium text-xs flex items-center gap-2"
          data-testid="client-autocomplete-create-new"
          @click="emitCreateNew"
        >
          <BaseActionIcon action="create" />
          <span>Crear nuevo cliente "{{ inputText.trim() }}"</span>
        </button>
      </div>

      <!-- Empty catalog: blank query is a real list request, never an instruction
           to guess what to type. -->
      <div v-else-if="hasSearched" class="px-4 py-3 text-sm text-text-muted">
        <p class="mb-2">No hay clientes registrados.</p>
        <button
          type="button"
          class="w-full text-left px-3 py-2 rounded-lg bg-primary-soft text-text-brand hover:opacity-90 transition-colors font-medium text-xs flex items-center gap-2"
          data-testid="client-autocomplete-create-new"
          @click="emitCreateNew"
        >
          <BaseActionIcon action="create" />
          <span>Crear un cliente</span>
        </button>
      </div>

      <div v-else class="px-4 py-3 text-sm text-text-subtle text-center">
        Cargando clientes...
      </div>
    </BaseFloatingListbox>
  </div>
</template>

<script setup>
import { ref, useId, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import {
  MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline';
import BaseFloatingListbox from '~/components/base/BaseFloatingListbox.vue';
import { useProposalClientsStore } from '~/stores/proposal_clients';

/**
 * Searchable client picker for the proposal create/edit forms.
 *
 * Two-way binds the selected client id via v-model. When the user picks a
 * row from the dropdown, the parent receives the **full** client object via
 * the `select` event so it can auto-fill snapshot fields (email, phone,
 * company) on the proposal form.
 *
 * If the user types a name with no matching client, the dropdown shows a
 * "Crear nuevo" footer that emits `create-new` with the typed value — the
 * parent decides whether to open a modal, fall through to the inline
 * fields, or call the store's `createClient` directly.
 */

const props = defineProps({
  modelValue: { type: [Number, null], default: null },
  /** Pre-fill input when editing an existing proposal that already has a client. */
  initialLabel: { type: String, default: '' },
  placeholder: { type: String, default: 'Buscar cliente por nombre, email o empresa...' },
  testId: { type: String, default: 'client-autocomplete-input' },
  /**
   * Los layouts de barra pintan su propia línea de estado y necesitan que el
   * alto del picker sea constante: el hint en flujo hace crecer la celda del
   * flex y arrastra el input fuera de línea con los botones de al lado.
   */
  showLinkedHint: { type: Boolean, default: true },
});

const emit = defineEmits(['update:modelValue', 'select', 'create-new']);

const clientsStore = useProposalClientsStore();
const PAGE_SIZE = 20;

const wrapperRef = ref(null);
const inputRef = ref(null);
const listboxId = `${useId()}-listbox`;
const inputText = ref(props.initialLabel || '');
// El nombre del cliente que está REALMENTE enlazado, separado de lo que se
// teclea encima: es lo que se restaura al cerrar sin elegir y lo que nombra el
// hint mientras se busca.
const committedLabel = ref(props.initialLabel || '');
const isOpen = ref(false);
const hasSearched = ref(false);
const results = ref([]);
const highlightIndex = ref(-1);
const isSearching = ref(false);
const isLoadingMore = ref(false);
const hasMore = ref(false);
const nextOffset = ref(0);
const searchError = ref('');
const loadMoreError = ref('');
let searchGeneration = 0;

// -------------------------------------------------------------------
// Search (debounced 200ms)
// -------------------------------------------------------------------

const runSearch = async (query, { append = false } = {}) => {
  if (append && (!hasMore.value || isSearching.value || isLoadingMore.value)) return;

  const generation = append ? searchGeneration : ++searchGeneration;
  const offset = append ? nextOffset.value : 0;
  if (append) {
    isLoadingMore.value = true;
    loadMoreError.value = '';
  } else {
    isSearching.value = true;
    searchError.value = '';
    loadMoreError.value = '';
    hasSearched.value = false;
    hasMore.value = false;
    nextOffset.value = 0;
  }

  try {
    const result = await clientsStore.searchClients(query, {
      offset,
      limit: PAGE_SIZE,
    });
    if (generation !== searchGeneration) return;
    if (result?.cancelled) {
      // Superseded searches are normally rejected after the next generation
      // starts. If an adapter cancels the current request on its own, close the
      // empty layer instead of leaving a permanent "Cargando" state behind.
      if (!append) isOpen.value = false;
      return;
    }
    if (!result?.success) {
      if (append) loadMoreError.value = 'load_failed';
      else searchError.value = 'load_failed';
      return;
    }

    const page = Array.isArray(result.data) ? result.data : [];
    if (append) {
      const knownIds = new Set(results.value.map((client) => client.id));
      results.value = [
        ...results.value,
        ...page.filter((client) => !knownIds.has(client.id)),
      ];
    } else {
      results.value = page;
    }
    nextOffset.value = result.nextOffset ?? offset + page.length;
    hasMore.value = Boolean(result.hasMore);
    hasSearched.value = true;
    if (!append) highlightIndex.value = results.value.length > 0 ? 0 : -1;
  } finally {
    if (generation === searchGeneration) {
      if (append) isLoadingMore.value = false;
      else isSearching.value = false;
    }
  }
};

const debouncedSearch = useDebounceFn(runSearch, 200);

const onInput = () => {
  // Invalidate the request that belongs to the previous text immediately;
  // otherwise it could resolve during the 200 ms debounce window and flash a
  // result set for a query the input no longer contains.
  searchGeneration += 1;
  isOpen.value = true;
  hasSearched.value = false;
  searchError.value = '';
  isSearching.value = true;
  // Escribir es buscar, no desvincular. Soltar el id acá dejaba el formulario
  // sucio por un caracter y, al guardar, desvinculaba al cliente de verdad.
  // Para desvincular está la X (`clearSelection`).
  debouncedSearch(inputText.value.trim());
};

const onFocus = () => {
  isOpen.value = true;
  // Skip the auto-search when the parent already committed a selection
  // (editing an existing proposal) — otherwise we'd waste a request.
  if (!hasSearched.value && props.modelValue === null) {
    runSearch(inputText.value.trim());
  }
};

const retrySearch = () => runSearch(inputText.value.trim());

const loadMore = () => runSearch(inputText.value.trim(), { append: true });

const clientHasNoEmail = (client) => (
  Boolean(client?.is_email_placeholder) || !String(client?.email || '').trim()
);

// -------------------------------------------------------------------
// Selection
// -------------------------------------------------------------------

const selectClient = (client) => {
  emit('update:modelValue', client.id);
  emit('select', client);
  inputText.value = client.name;
  committedLabel.value = client.name;
  closeDropdown();
};

const clearSelection = () => {
  searchGeneration += 1;
  emit('update:modelValue', null);
  emit('select', null);
  inputText.value = '';
  committedLabel.value = '';
  results.value = [];
  hasSearched.value = false;
  hasMore.value = false;
  nextOffset.value = 0;
  searchError.value = '';
  loadMoreError.value = '';
  isSearching.value = false;
  isLoadingMore.value = false;
  highlightIndex.value = -1;
  inputRef.value?.focus();
};

/**
 * `opts` llega como Event desde esc y click-outside; sólo un objeto con
 * `restore: false` explícito apaga la restauración (lo usa "Crear nuevo",
 * donde el texto tecleado es el nombre del cliente por crear).
 */
const closeDropdown = (opts) => {
  isOpen.value = false;
  highlightIndex.value = -1;
  const restore = !(opts && opts.restore === false);
  if (restore && props.modelValue !== null && inputText.value !== committedLabel.value) {
    inputText.value = committedLabel.value;
  }
};

// -------------------------------------------------------------------
// Keyboard navigation
// -------------------------------------------------------------------

const onArrowDown = () => {
  if (!isOpen.value) {
    isOpen.value = true;
    if (!hasSearched.value && props.modelValue === null) {
      runSearch(inputText.value.trim());
    }
    return;
  }
  if (results.value.length === 0) return;
  highlightIndex.value =
    (highlightIndex.value + 1) % results.value.length;
};

const onArrowUp = () => {
  if (!isOpen.value || results.value.length === 0) return;
  highlightIndex.value =
    (highlightIndex.value - 1 + results.value.length) % results.value.length;
};

const onEnter = () => {
  if (!isOpen.value) return;
  if (highlightIndex.value >= 0 && results.value[highlightIndex.value]) {
    selectClient(results.value[highlightIndex.value]);
  } else if (hasSearched.value && results.value.length === 0 && inputText.value.trim()) {
    emitCreateNew();
  }
};

// -------------------------------------------------------------------
// Create new
// -------------------------------------------------------------------

const emitCreateNew = () => {
  const typed = inputText.value.trim();
  emit('create-new', typed);
  // Lo tecleado ES el nombre del cliente nuevo: se vuelve la etiqueta enlazada
  // en vez de perderse contra el cliente anterior.
  committedLabel.value = typed;
  closeDropdown({ restore: false });
};

// -------------------------------------------------------------------
// External value sync
// -------------------------------------------------------------------

watch(
  () => props.initialLabel,
  (newLabel) => {
    // Los dos casos del input son excluyentes (uno exige rótulo, el otro que no
    // lo haya), pero NINGUNO puede cortar el watcher: la sincronización de
    // `committedLabel` de más abajo tiene que correr siempre.
    if (!inputText.value && newLabel) {
      inputText.value = newLabel;
    } else if (!newLabel && props.modelValue == null) {
      // Retirar el rótulo con el valor ya vacío es el padre diciendo «esto se
      // fue» — una sugerencia que se retracta, un formulario que se resetea. El
      // input no puede seguir mostrando al cliente anterior: decía tener uno
      // cuando ya no lo tenía. Con un cliente elegido no se toca nada.
      inputText.value = '';
    }
    // El padre reetiqueta tras guardar; sincronizar sin pisar algo que el
    // usuario esté tecleando encima en ese momento.
    //
    // Va SIEMPRE, y ahí estuvo el bug: la hidratación de la página real entra
    // por la primera rama (el documento llega por red, así que el picker nace
    // sin rótulo), y cortar el watcher ahí dejaba `committedLabel` vacío para
    // siempre. Después, al salir del campo, el restore escribía ese vacío y
    // borraba el cliente de la pantalla.
    if (inputText.value === committedLabel.value || !committedLabel.value) {
      committedLabel.value = newLabel || '';
    }
  },
);

</script>
