<template>
  <div ref="wrapperRef" class="relative">
    <div class="relative">
      <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-text-subtle">
        <MagnifyingGlassIcon class="h-4 w-4" />
      </span>
      <input
        ref="inputRef"
        v-model="inputText"
        type="text"
        role="combobox"
        :placeholder="placeholder"
        :data-testid="testId"
        :aria-expanded="isCatalog || isOpen"
        :aria-controls="isCatalog || isOpen ? listboxId : undefined"
        :aria-busy="isSearching || isLoadingMore"
        aria-autocomplete="list"
        aria-haspopup="listbox"
        autocomplete="off"
        class="w-full rounded-xl border border-input-border bg-input-bg py-2.5 pl-9 pr-9 text-sm text-input-text outline-none placeholder:text-text-subtle focus:border-focus-ring focus:ring-2 focus:ring-focus-ring/30"
        @input="onInput"
        @focus="onFocus"
        @keydown.down.prevent="onArrowDown"
        @keydown.up.prevent="onArrowUp"
        @keydown.enter.prevent="onEnter"
        @keydown.esc.prevent="onEscape"
      />
      <button
        v-if="modelValue || inputText"
        type="button"
        class="absolute inset-y-0 right-0 flex items-center pr-3 text-text-subtle transition-colors hover:text-text-default"
        :aria-label="$t ? $t('clients.autocomplete.clear') : 'Limpiar'"
        :title="$t ? $t('clients.autocomplete.clear') : 'Limpiar'"
        @click="clearSelection"
      >
        <BaseActionIcon action="clear" />
      </button>
    </div>

    <p
      v-if="modelValue && showLinkedHint"
      class="mt-1 text-xs text-text-subtle"
      data-testid="client-autocomplete-linked"
    >
      Cliente enlazado: {{ committedLabel }} <span class="tabular-nums">(#{{ modelValue }})</span>
    </p>

    <ClientAutocompleteResults
      v-if="isCatalog"
      class="mt-3"
      :listbox-id="listboxId"
      presentation="catalog"
      :results="results"
      :input-text="inputText"
      :model-value="modelValue"
      :highlight-index="highlightIndex"
      :has-searched="hasSearched"
      :is-searching="isSearching"
      :is-loading-more="isLoadingMore"
      :search-error="searchError"
      :load-more-error="loadMoreError"
      :sort-direction="sortDirection"
      @create-new="emitCreateNew"
      @highlight="highlightIndex = $event"
      @load-more="loadMore"
      @retry="retrySearch"
      @select="selectClient"
      @toggle-sort="toggleSort"
    />

    <BaseFloatingListbox
      v-else
      :id="listboxId"
      :open="isOpen"
      :anchor="inputRef"
      :owner="wrapperRef"
      @close="closeDropdown"
      @reach-end="loadMore"
    >
      <ClientAutocompleteResults
        :results="results"
        :input-text="inputText"
        :model-value="modelValue"
        :highlight-index="highlightIndex"
        :has-searched="hasSearched"
        :is-searching="isSearching"
        :is-loading-more="isLoadingMore"
        :search-error="searchError"
        :load-more-error="loadMoreError"
        @create-new="emitCreateNew"
        @highlight="highlightIndex = $event"
        @load-more="loadMore"
        @retry="retrySearch"
        @select="selectClient"
      />
    </BaseFloatingListbox>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, useId, watch } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import {
  MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline';
import BaseFloatingListbox from '~/components/base/BaseFloatingListbox.vue';
import ClientAutocompleteResults from '~/components/ui/ClientAutocompleteResults.vue';
import { usePersistedRef } from '~/composables/usePersistedRef';
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
  /** Floating autocomplete by default; catalog keeps the result list in flow. */
  presentation: {
    type: String,
    default: 'floating',
    validator: (value) => ['floating', 'catalog'].includes(value),
  },
});

const emit = defineEmits(['update:modelValue', 'select', 'create-new']);

const clientsStore = useProposalClientsStore();
const PAGE_SIZE = 20;
const CATALOG_SORT_STORAGE_KEY = 'projectapp-client-catalog-sort-direction';

const isCatalog = computed(() => props.presentation === 'catalog');
const {
  ref: persistedSortDirection,
  write: persistSortDirection,
} = usePersistedRef(CATALOG_SORT_STORAGE_KEY, 'asc', {
  serialize: String,
  deserialize: String,
});
if (!['asc', 'desc'].includes(persistedSortDirection.value)) {
  persistedSortDirection.value = 'asc';
}
const sortDirection = persistedSortDirection;

const wrapperRef = ref(null);
const inputRef = ref(null);
const listboxId = `${useId()}-listbox`;
const inputText = ref(isCatalog.value ? '' : (props.initialLabel || ''));
// El nombre del cliente que está REALMENTE enlazado, separado de lo que se
// teclea encima: es lo que se restaura al cerrar sin elegir y lo que nombra el
// hint mientras se busca.
const committedLabel = ref(props.initialLabel || '');
const isOpen = ref(isCatalog.value);
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
    const paging = {
      offset,
      limit: PAGE_SIZE,
    };
    if (isCatalog.value) {
      paging.order = sortDirection.value === 'desc' ? '-name' : 'name';
    }
    const result = await clientsStore.searchClients(query, paging);
    if (generation !== searchGeneration) return;
    if (result?.cancelled) {
      // Superseded searches are normally rejected after the next generation
      // starts. If an adapter cancels the current request on its own, close the
      // empty layer instead of leaving a permanent "Cargando" state behind.
      if (!append && !isCatalog.value) isOpen.value = false;
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
  if (!hasSearched.value && !isSearching.value && props.modelValue === null) {
    runSearch(inputText.value.trim());
  }
};

const retrySearch = () => runSearch(inputText.value.trim());

const loadMore = () => runSearch(inputText.value.trim(), { append: true });

// -------------------------------------------------------------------
// Selection
// -------------------------------------------------------------------

const selectClient = (client) => {
  emit('update:modelValue', client.id);
  emit('select', client);
  committedLabel.value = client.name;
  if (isCatalog.value) {
    highlightIndex.value = results.value.findIndex((row) => row.id === client.id);
    return;
  }
  inputText.value = client.name;
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
  if (isCatalog.value) runSearch('');
};

/**
 * `opts` llega como Event desde esc y click-outside; sólo un objeto con
 * `restore: false` explícito apaga la restauración (lo usa "Crear nuevo",
 * donde el texto tecleado es el nombre del cliente por crear).
 */
const closeDropdown = (opts) => {
  if (isCatalog.value) return;
  isOpen.value = false;
  highlightIndex.value = -1;
  const restore = !(opts && opts.restore === false);
  if (restore && props.modelValue !== null && inputText.value !== committedLabel.value) {
    inputText.value = committedLabel.value;
  }
};

const onEscape = () => {
  if (!isCatalog.value) {
    closeDropdown();
    return;
  }
  if (!inputText.value) return;
  inputText.value = '';
  runSearch('');
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
  if (isCatalog.value) return;
  // Lo tecleado ES el nombre del cliente nuevo: se vuelve la etiqueta enlazada
  // en vez de perderse contra el cliente anterior.
  committedLabel.value = typed;
  closeDropdown({ restore: false });
};

const toggleSort = () => {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  persistSortDirection(sortDirection.value);
  highlightIndex.value = -1;
  runSearch(inputText.value.trim());
};

// -------------------------------------------------------------------
// External value sync
// -------------------------------------------------------------------

watch(
  () => props.initialLabel,
  (newLabel) => {
    if (isCatalog.value) {
      committedLabel.value = newLabel || '';
      return;
    }
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

watch(
  () => props.modelValue,
  (newValue, previousValue) => {
    if (
      isCatalog.value
      && newValue != null
      && previousValue == null
      && hasSearched.value
      && results.value.length === 0
    ) {
      inputText.value = '';
      runSearch('');
    }
  },
);

onMounted(() => {
  if (isCatalog.value) runSearch('');
});

</script>
