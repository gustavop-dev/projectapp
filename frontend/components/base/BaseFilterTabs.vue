<template>
  <div>
    <!--
      Móvil: la tira colapsa en un selector.

      Variante `filter` a propósito: en nueve de las doce vistas del contable
      este control queda pegado al de navegación de sección, y los dos hacen
      cosas distintas — uno cambia de tab del módulo, éste aplica un filtro
      guardado. El de sección va sólido; éste, neutro como cualquier campo. El
      `aria-label` sostiene la distinción para quien no ve el color.
    -->
    <BaseMobileTabSelect
      class="mb-4"
      test-id="filter-tabs-select"
      aria-label="Filtro guardado"
      :model-value="configActive ? '__config__' : activeTabId"
      :options="mobileOptions"
      @update:model-value="handleMobileSelect"
    />

    <!--
      Desktop: horizontal tab bar.

      `flex-wrap` no es cosmético: sin él la tira se desborda a la derecha y el
      `body { overflow-x: hidden }` de app.vue la recorta SIN barra de scroll, así
      que los últimos filtros quedan inalcanzables y el corte se lee como el final
      de la lista. Envolver es lo que garantiza que ningún predefinido se esconda,
      y de paso deja siempre visible el activo sin tener que traerlo a la vista.
      Es el mismo mecanismo que ya usan ClientModuleTabs y AccountingSubnav.

      Si la tira necesita más de dos líneas, el problema dejó de ser de
      presentación: sobran predefinidos. Podar la lista, no volver a esconderlos.
    -->
    <div
      data-testid="filter-tabs-strip"
      class="hidden panel-landscape:flex flex-wrap items-center gap-1 mb-4 border-b border-border-default"
    >
      <!-- "Todas" tab -->
      <button
        type="button"
        data-testid="filter-tabs-tab-all"
        class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
        :class="String(activeTabId) === 'all'
          ? 'border-emerald-600 text-text-brand'
          : 'border-transparent text-text-muted hover:text-text-default'"
        @click="$emit('select', 'all')"
      >
        Todas<span
          v-if="allCount != null"
          data-testid="filter-tabs-count-all"
          class="ml-1 text-xs tabular-nums text-text-subtle"
          :title="countTitle"
        >({{ allCount }})</span>
      </button>

      <!--
        Saved tabs, reorderable.

        `class="contents"` keeps this wrapper out of the layout: its children
        have to stay direct flex items of the strip above, or the whole list
        would collapse into a single item and the wrap would break. It also
        keeps "Todas", "+" and "Configuraciones" as siblings — with "Todas"
        outside the sortable list, nothing can be dropped ahead of it, so it
        stays first by construction instead of by a rule someone must enforce.
      -->
      <draggable
        v-model="orderedTabs"
        item-key="id"
        tag="div"
        class="contents"
        ghost-class="opacity-30"
        :delay="TOUCH_DRAG_DELAY_MS"
        :delay-on-touch-only="true"
        :touch-start-threshold="5"
        @start="isDragging = true"
        @end="handleDragEnd"
      >
        <template #item="{ element: tab }">
          <div class="relative group flex items-center">
            <button
              type="button"
              :data-testid="`filter-tabs-tab-${tab.id}`"
              class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap cursor-grab active:cursor-grabbing"
              :class="String(activeTabId) === String(tab.id)
                ? 'border-emerald-600 text-text-brand'
                : 'border-transparent text-text-muted hover:text-text-default'"
              aria-keyshortcuts="Control+ArrowLeft Control+ArrowRight"
              @click="handleSelect(tab.id)"
              @keydown="onTabKeydown($event, tab)"
            >
              {{ tab.name }}<span
                v-if="isOwnTab(tab)"
                :data-testid="`filter-tabs-origin-${tab.id}`"
                class="ml-1 rounded-full bg-info-soft px-1.5 py-0.5 text-[10px] font-medium text-info-strong"
                title="Vista guardada por ti"
              >Propia</span><span
                v-if="countFor(tab) != null"
                :data-testid="`filter-tabs-count-${tab.id}`"
                class="ml-1 text-xs tabular-nums text-text-subtle"
                :title="countTitle"
              >({{ countFor(tab) }})</span><span
                v-if="isModified(tab)"
                :data-testid="`filter-tabs-modified-${tab.id}`"
                class="ml-1 text-warning-strong"
                title="Filtros modificados respecto a su base"
              >•</span>
            </button>
            <!--
              Context menu. Builtins get one too now: it is the only place
              they can be moved without dragging, which is the whole point of
              offering a non-drag path. What they still cannot do is be
              renamed, restored, re-based or deleted — they have no row of
              their own to rewrite.

              El `aria-label` es genérico a propósito, y no "Opciones de
              «Negociando»": Playwright empareja `name` por SUBCADENA salvo
              que se pida `exact`, así que un rótulo que lleve el nombre del
              chip hace que `getByRole('button', { name: 'Negociando' })`
              resuelva a dos elementos y reviente en strict mode — en las
              trece vistas que usan la tira, no sólo acá. El botón va pegado
              a su chip, que es lo que dice de cuál filtro son las opciones.
            -->
            <button
              type="button"
              :data-testid="`filter-tabs-menu-${tab.id}`"
              class="touch-reveal touch-target p-0.5 rounded text-text-subtle hover:text-text-muted opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity -ml-1 mr-1"
              aria-label="Opciones del filtro"
              title="Opciones del filtro"
              @click.stop="toggleMenu(tab.id)"
            >
              <BaseActionIcon action="more" />
            </button>
            <!-- Dropdown menu -->
            <div
              v-if="openMenuId === tab.id"
              class="absolute top-full left-0 mt-1 z-50 bg-surface border border-border-default rounded-lg shadow-lg py-1 min-w-[180px]"
            >
              <button
                type="button"
                :data-testid="`filter-tabs-move-left-${tab.id}`"
                class="touch-target w-full px-3 py-1.5 text-left text-sm text-text-default hover:bg-surface-raised
                       disabled:text-text-subtle disabled:hover:bg-transparent disabled:cursor-not-allowed"
                :disabled="isFirst(tab)"
                :title="isFirst(tab) ? 'Este filtro ya está en la primera posición.' : undefined"
                @click="handleMove(tab.id, -1)"
              >
                {{ isFirst(tab) ? 'Ya es el primer filtro' : 'Mover a la izquierda' }}
              </button>
              <button
                type="button"
                :data-testid="`filter-tabs-move-right-${tab.id}`"
                class="touch-target w-full px-3 py-1.5 text-left text-sm text-text-default hover:bg-surface-raised
                       disabled:text-text-subtle disabled:hover:bg-transparent disabled:cursor-not-allowed"
                :disabled="isLast(tab)"
                :title="isLast(tab) ? 'Este filtro ya está en la última posición.' : undefined"
                @click="handleMove(tab.id, 1)"
              >
                {{ isLast(tab) ? 'Ya es el último filtro' : 'Mover a la derecha' }}
              </button>
              <button
                v-if="!tab.builtin"
                type="button"
                data-testid="filter-tabs-rename"
                class="touch-target w-full px-3 py-1.5 text-left text-sm text-text-default hover:bg-surface-raised"
                @click="startRename(tab)"
              >
                Renombrar
              </button>
              <BaseButton
                v-if="!tab.builtin && isModified(tab)"
                variant="ghost"
                size="sm"
                class="w-full"
                data-testid="filter-tabs-restore"
                @click="handleRestore(tab.id)"
              >
                Restaurar filtros
              </BaseButton>
              <BaseButton
                v-if="!tab.builtin && isModified(tab)"
                variant="ghost"
                size="sm"
                class="w-full"
                data-testid="filter-tabs-rebase"
                @click="handleRebase(tab.id)"
              >
                Fijar como base
              </BaseButton>
              <BaseButton
                v-if="!tab.builtin"
                variant="danger-ghost"
                size="sm"
                class="w-full"
                data-testid="filter-tabs-delete"
                @click="handleDelete(tab.id)"
              >
                Eliminar
              </BaseButton>
            </div>
          </div>
        </template>
      </draggable>

      <!-- "+" button to create new tab -->
      <button
        type="button"
        data-testid="filter-tabs-create"
        class="px-3 py-2.5 text-sm font-medium transition-colors border-b-2 border-transparent -mb-px"
        :class="props.isTabLimitReached
          ? 'text-text-subtle cursor-not-allowed'
          : 'text-text-muted hover:text-text-brand'"
        :disabled="props.isTabLimitReached"
        :aria-label="props.isTabLimitReached ? `Máximo ${props.tabs.length} pestañas` : 'Guardar filtros como nueva pestaña'"
        :title="props.isTabLimitReached ? `Máximo ${props.tabs.length} pestañas` : 'Guardar filtros como nueva pestaña'"
        @click="!props.isTabLimitReached && startCreate()"
      >
        <BaseActionIcon action="create" />
      </button>

      <!--
        Fixed trailing config tab (opt-in per view). Va como un ítem más al final:
        con `flex-wrap`, un `ml-auto` empujaría la pestaña al extremo derecho de SU
        línea, que puede ser una línea propia casi vacía. Pegada al resto de la tira
        no se pierde nada — con el wrap la posición a la derecha ya no comunicaba.
      -->
      <button
        v-if="showConfigTab"
        type="button"
        data-testid="filter-tabs-config"
        class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
        :class="configActive
          ? 'border-emerald-600 text-text-brand'
          : 'border-transparent text-text-muted hover:text-text-default'"
        @click="$emit('config')"
      >
        Configuraciones
      </button>
    </div>

    <!-- Create / Rename inline input -->
    <Transition name="fade-modal">
      <div
        v-if="showInput"
        class="mb-4 flex items-center gap-2"
      >
        <input
          ref="nameInputRef"
          v-model="inputName"
          data-testid="filter-tabs-input"
          type="text"
          :placeholder="isRenaming ? 'Nuevo nombre...' : 'Nombre de la pestaña...'"
          class="flex-1 max-w-xs px-3 py-2 border border-border-default rounded-lg text-sm
                 bg-surface text-text-default
                 focus:ring-1 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
          @keyup.enter="confirmInput"
          @keyup.escape="cancelInput"
        />
        <BaseControlGate
          :reasons="!inputName.trim() ? ['Escribe el nombre del filtro.'] : []"
          :label="isRenaming ? 'Renombrar no disponible' : 'Guardar no disponible'"
          align="start"
        >
          <template #default="{ describedBy }">
            <BaseButton
              variant="primary"
              size="md"
              data-testid="filter-tabs-confirm"
              :disabled="!inputName.trim()"
              disabled-reason="Escribe el nombre del filtro."
              :aria-describedby="describedBy"
              @click="confirmInput"
            >
              {{ isRenaming ? 'Renombrar' : 'Guardar' }}
            </BaseButton>
          </template>
        </BaseControlGate>
        <BaseButton variant="ghost" size="md" data-testid="filter-tabs-cancel" @click="cancelInput">
          Cancelar
        </BaseButton>
      </div>
    </Transition>

    <!-- Click-outside overlay to close menus -->
    <div
      v-if="openMenuId"
      data-testid="filter-tabs-overlay"
      class="fixed inset-0 z-40"
      @click="openMenuId = null"
    />

    <!--
      A move is silent for anyone not watching the strip: the chip changes
      place and nothing else happens. This says where it landed.
    -->
    <p
      data-testid="filter-tabs-live"
      class="sr-only"
      role="status"
      aria-live="polite"
    >{{ liveMessage }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import { sameFilters } from '~/composables/useSavedFilterTabs';
import BaseControlGate from './BaseControlGate.vue';

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  activeTabId: { type: [String, Number], default: 'all' },
  isTabLimitReached: { type: Boolean, default: false },
  // Optional per-tab match count, keyed by tab id, so a quick filter can show
  // how many rows it would leave without being applied. Views that pass
  // nothing render exactly as before.
  counts: { type: Object, default: () => ({}) },
  // What the count badge means, which is not the same sentence in every view.
  countTitle: { type: String, default: 'Registros que cumplen este filtro' },
  // Opt-in fixed trailing "Configuraciones" tab for module-owned settings.
  showConfigTab: { type: Boolean, default: false },
  configActive: { type: Boolean, default: false },
});

const emit = defineEmits([
  'select', 'create', 'rename', 'delete', 'config', 'restore', 'rebase',
  'reorder',
]);

/**
 * Hold-to-drag on touch, immediate with a mouse (`delayOnTouchOnly`).
 *
 * On a touch screen the strip is also something you swipe across, and a drag
 * that started on contact would eat that gesture. A mouse has no such
 * ambiguity, and making it wait would just feel broken.
 */
const TOUCH_DRAG_DELAY_MS = 200;

// Builtin quick-filters carry no persisted definition; legacy tab payloads
// without base_filters must not flag as modified.
function isModified(tab) {
  return (
    !tab.builtin
    && tab.base_filters != null
    && !sameFilters(tab.filters, tab.base_filters)
  );
}

/**
 * Saved tabs carry numeric ids and builtins carry strings, so the lookup is
 * keyed by the stringified id. Returns null (not 0) when there is no count,
 * which is what keeps the badge off for the views that pass no `counts`.
 */
function countFor(tab) {
  const value = props.counts[String(tab.id)];
  return typeof value === 'number' ? value : null;
}

// "Todas" is rendered apart from the list, so its badge reads its own key.
const allCount = computed(() => {
  const value = props.counts.all;
  return typeof value === 'number' ? value : null;
});

/**
 * Todo lo que no está oculto se renderiza inline: la tira envuelve en varias
 * líneas y no esconde nada. Antes existía un tope `maxVisible` que mandaba el
 * excedente a un menú "+N", pero valía 0 en once de las trece vistas y ahí la
 * tira se cortaba en seco; y donde sí se pasaba, un tope fijo por cantidad no
 * adapta al ancho de la ventana. Un solo mecanismo para todas las vistas.
 *
 * Una pestaña oculta desde Configuración sigue existiendo; sólo deja de ocupar
 * lugar.
 */
const hasFactoryTabs = computed(() => props.tabs.some((tab) => tab.builtin || tab.is_seeded));

function isOwnTab(tab) {
  return hasFactoryTabs.value && !tab.builtin && !tab.is_seeded;
}

const visibleTabs = computed(() => props.tabs.filter((tab) => (
  !tab.is_hidden || String(tab.id) === String(props.activeTabId)
)));

/**
 * Mutable mirror of `visibleTabs`: vuedraggable writes the new order straight
 * into the array it is given, and `visibleTabs` is a computed over a prop.
 *
 * The parent stays the source of truth — every change to `props.tabs` resyncs
 * this — so a rejected reorder snaps the strip back on its own when the server
 * echo arrives with the old order.
 */
const orderedTabs = ref([...visibleTabs.value]);
watch(visibleTabs, (tabs) => { orderedTabs.value = [...tabs]; });

const isDragging = ref(false);
// Set on drop and cleared a turn later, to swallow the click the drop
// produces. See `handleSelect`.
const justDragged = ref(false);
const liveMessage = ref('');

function isFirst(tab) {
  return orderedTabs.value.findIndex((t) => t.id === tab.id) === 0;
}

function isLast(tab) {
  const list = orderedTabs.value;
  return list.findIndex((t) => t.id === tab.id) === list.length - 1;
}

function announceMove(tab) {
  const position = orderedTabs.value.findIndex((t) => t.id === tab.id) + 1;
  liveMessage.value = `«${tab.name}» movido a la posición ${position} de ${orderedTabs.value.length}`;
}

/** Persist whatever `orderedTabs` currently says, top to bottom. */
function commitOrder() {
  emit('reorder', orderedTabs.value.map((tab) => tab.id));
}

function handleDragEnd() {
  isDragging.value = false;
  // The browser fires `click` right after the drop, so the flag has to
  // outlive this handler by one turn to be there when it arrives.
  justDragged.value = true;
  setTimeout(() => { justDragged.value = false; }, 0);

  const moved = orderedTabs.value;
  const previous = visibleTabs.value;
  const changed = moved.some((tab, i) => tab.id !== previous[i]?.id);
  if (!changed) return;
  announceMove(moved.find((tab, i) => tab.id !== previous[i]?.id));
  commitOrder();
}

/**
 * Move without dragging: the menu entries and the keyboard shortcut.
 *
 * Dragging is not reachable for everyone and is awkward on a small screen,
 * and reordering is not an optional extra of this strip — so it cannot be the
 * only way in.
 */
function moveTab(tabId, delta) {
  const list = [...orderedTabs.value];
  const index = list.findIndex((tab) => tab.id === tabId);
  const target = index + delta;
  if (index === -1 || target < 0 || target >= list.length) return false;
  [list[index], list[target]] = [list[target], list[index]];
  orderedTabs.value = list;
  announceMove(list[target]);
  commitOrder();
  return true;
}

function handleMove(tabId, delta) {
  openMenuId.value = null;
  moveTab(tabId, delta);
}

/**
 * Ctrl/Cmd + arrow moves the focused chip. Bare arrows are left alone: they
 * are how a screen reader walks the strip, and stealing them would trade one
 * kind of reach for another.
 */
function onTabKeydown(event, tab) {
  if (!event.ctrlKey && !event.metaKey) return;
  const delta = event.key === 'ArrowLeft' ? -1 : (event.key === 'ArrowRight' ? 1 : 0);
  if (!delta) return;
  event.preventDefault();
  moveTab(tab.id, delta);
}

/**
 * Moving a chip must not apply its filter — the two gestures start the same
 * way and the strip changes the whole view.
 *
 * Sortable does suppress the click on the element it moved, but not reliably
 * on a drag that ends back where it began, which the browser still reports as
 * an ordinary click. Guarding here makes it deterministic instead.
 */
function handleSelect(tabId) {
  if (isDragging.value || justDragged.value) return;
  emit('select', tabId);
}

/**
 * Las opciones del selector móvil, en el MISMO orden que la tira de escritorio:
 * "Todas", las guardadas visibles y, si la vista la pide, Configuraciones. La
 * etiqueta arrastra el contador y el punto de "filtros modificados" porque en
 * móvil no hay una segunda línea donde ponerlos.
 */
const mobileOptions = computed(() => {
  const options = [{ value: 'all', label: 'Todas' }];
  for (const tab of visibleTabs.value) {
    const count = countFor(tab);
    options.push({
      value: String(tab.id),
      label: `${tab.name}${isOwnTab(tab) ? ' · Propia' : ''}${count != null ? ` (${count})` : ''}${isModified(tab) ? ' •' : ''}`,
    });
  }
  if (props.showConfigTab) options.push({ value: '__config__', label: '⚙ Configuraciones' });
  return options;
});

function handleMobileSelect(value) {
  if (value === '__config__') {
    emit('config');
    return;
  }
  emit('select', value);
}

const openMenuId = ref(null);
const showInput = ref(false);
const inputName = ref('');
const isRenaming = ref(false);
const renameTargetId = ref(null);
const nameInputRef = ref(null);

function toggleMenu(tabId) {
  openMenuId.value = openMenuId.value === tabId ? null : tabId;
}

function startCreate() {
  isRenaming.value = false;
  renameTargetId.value = null;
  inputName.value = '';
  showInput.value = true;
  nextTick(() => nameInputRef.value?.focus());
}

function startRename(tab) {
  openMenuId.value = null;
  isRenaming.value = true;
  renameTargetId.value = tab.id;
  inputName.value = tab.name;
  showInput.value = true;
  nextTick(() => nameInputRef.value?.focus());
}

function confirmInput() {
  const name = inputName.value.trim();
  if (!name) return;
  if (isRenaming.value && renameTargetId.value) {
    emit('rename', renameTargetId.value, name);
  } else {
    emit('create', name);
  }
  cancelInput();
}

function cancelInput() {
  showInput.value = false;
  inputName.value = '';
  isRenaming.value = false;
  renameTargetId.value = null;
}

function handleDelete(tabId) {
  openMenuId.value = null;
  emit('delete', tabId);
}

function handleRestore(tabId) {
  openMenuId.value = null;
  emit('restore', tabId);
}

function handleRebase(tabId) {
  openMenuId.value = null;
  emit('rebase', tabId);
}

</script>
