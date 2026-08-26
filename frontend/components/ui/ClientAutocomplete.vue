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
    <div
      v-if="isOpen"
      class="absolute z-30 mt-1 w-full bg-surface border border-border-default rounded-xl shadow-lg max-h-72 overflow-auto"
      role="listbox"
    >
      <!-- Loading -->
      <div
        v-if="isSearching"
        class="px-4 py-3 text-sm text-text-subtle text-center"
      >
        Buscando...
      </div>

      <!-- Results -->
      <ul v-else-if="results.length > 0" class="divide-y divide-border-muted">
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
                  v-if="client.is_email_placeholder"
                  class="text-[10px] px-1.5 py-0.5 rounded-full bg-warning-soft text-warning-strong font-medium uppercase tracking-wide"
                  title="Este cliente todavía no tiene correo. Las acciones que envían mensajes pedirán agregarlo antes de continuar."
                >
                  📧 Sin correo
                </span>
              </div>
              <p class="text-xs text-text-muted truncate mt-0.5">
                {{ client.is_email_placeholder ? 'Correo pendiente · habrá que agregarlo para enviar' : client.email }}
                <span v-if="client.company" class="text-text-subtle">· {{ client.company }}</span>
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

      <!-- No results — offer to create -->
      <div v-else-if="hasSearched" class="px-4 py-3 text-sm text-text-muted">
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

      <!-- Empty state (just opened, no input yet) -->
      <div v-else class="px-4 py-3 text-sm text-text-subtle text-center">
        Escribe al menos 1 caracter para buscar
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useDebounceFn, onClickOutside } from '@vueuse/core';
import {
  MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline';
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

const wrapperRef = ref(null);
const inputRef = ref(null);
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

// -------------------------------------------------------------------
// Search (debounced 200ms)
// -------------------------------------------------------------------

const runSearch = async (query) => {
  isSearching.value = true;
  try {
    const result = await clientsStore.searchClients(query);
    if (result.cancelled) return;
    results.value = result.success ? result.data || [] : [];
    hasSearched.value = true;
    highlightIndex.value = results.value.length > 0 ? 0 : -1;
  } finally {
    isSearching.value = false;
  }
};

const debouncedSearch = useDebounceFn(runSearch, 200);

const onInput = () => {
  isOpen.value = true;
  hasSearched.value = false;
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
    debouncedSearch(inputText.value.trim());
  }
};

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
  emit('update:modelValue', null);
  emit('select', null);
  inputText.value = '';
  committedLabel.value = '';
  results.value = [];
  hasSearched.value = false;
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

// Click-outside to close — onClickOutside auto-removes the listener on unmount.
onClickOutside(wrapperRef, closeDropdown);
</script>
