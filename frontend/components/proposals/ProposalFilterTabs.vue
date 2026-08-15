<template>
  <div>
    <!-- Mobile: select dropdown -->
    <div class="md:hidden mb-4">
      <select
        :value="activeTabId"
        class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm font-medium
               text-text-default bg-surface
               focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none
               appearance-none cursor-pointer"
        :style="selectArrowStyle"
        @change="handleMobileSelect($event.target.value)"
      >
        <option value="all">Todas</option>
        <option v-for="tab in visibleTabs" :key="tab.id" :value="tab.id">
          {{ tab.name }}{{ countFor(tab) != null ? ` (${countFor(tab)})` : '' }}{{ isModified(tab) ? ' •' : '' }}
        </option>
        <option v-if="showConfigTab" value="__config__">⚙ Configuraciones</option>
      </select>
    </div>

    <!-- Desktop: horizontal tab bar -->
    <div class="hidden md:flex items-center gap-1 mb-4 border-b border-border-default">
      <!-- "Todas" tab -->
      <button
        type="button"
        class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
        :class="activeTabId === 'all'
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

      <!-- Saved tabs -->
      <div
        v-for="tab in stripTabs"
        :key="tab.id"
        class="relative group flex items-center"
      >
        <button
          type="button"
          :data-testid="`filter-tabs-tab-${tab.id}`"
          class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
          :class="activeTabId === tab.id
            ? 'border-emerald-600 text-text-brand'
            : 'border-transparent text-text-muted hover:text-text-default'"
          @click="$emit('select', tab.id)"
        >
          {{ tab.name }}<span
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
        <!-- Tab context menu trigger (builtin tabs can't be renamed/deleted) -->
        <button
          v-if="!tab.builtin"
          type="button"
          :data-testid="`filter-tabs-menu-${tab.id}`"
          class="p-0.5 rounded text-text-subtle hover:text-text-muted opacity-0 group-hover:opacity-100 transition-opacity -ml-1 mr-1"
          @click.stop="toggleMenu(tab.id)"
        >
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
          </svg>
        </button>
        <!-- Dropdown menu -->
        <div
          v-if="!tab.builtin && openMenuId === tab.id"
          class="absolute top-full left-0 mt-1 z-50 bg-surface border border-border-default rounded-lg shadow-lg py-1 min-w-[140px]"
        >
          <button
            type="button"
            data-testid="filter-tabs-rename"
            class="w-full px-3 py-1.5 text-left text-sm text-text-default hover:bg-surface-raised"
            @click="startRename(tab)"
          >
            Renombrar
          </button>
          <BaseButton
            v-if="isModified(tab)"
            variant="ghost"
            size="sm"
            class="w-full"
            data-testid="filter-tabs-restore"
            @click="handleRestore(tab.id)"
          >
            Restaurar filtros
          </BaseButton>
          <BaseButton
            v-if="isModified(tab)"
            variant="ghost"
            size="sm"
            class="w-full"
            data-testid="filter-tabs-rebase"
            @click="handleRebase(tab.id)"
          >
            Fijar como base
          </BaseButton>
          <BaseButton variant="danger-ghost" size="sm" class="w-full" data-testid="filter-tabs-delete" @click="handleDelete(tab.id)">
            Eliminar
          </BaseButton>
        </div>
      </div>

      <!-- Overflow: what did not fit, so the strip never wraps or clips -->
      <BaseDropdown
        v-if="overflowTabs.length"
        align="left"
        width="w-64"
        :items="overflowItems"
      >
        <template #trigger>
          <span
            data-testid="filter-tabs-overflow"
            class="inline-block cursor-pointer px-3 py-2.5 text-sm font-medium transition-colors border-b-2 border-transparent -mb-px whitespace-nowrap text-text-muted hover:text-text-default"
            :title="`${overflowTabs.length} pestañas más`"
          >
            +{{ overflowTabs.length }}
          </span>
        </template>
      </BaseDropdown>

      <!-- "+" button to create new tab -->
      <button
        type="button"
        data-testid="filter-tabs-create"
        class="px-3 py-2.5 text-sm font-medium transition-colors border-b-2 border-transparent -mb-px"
        :class="props.isTabLimitReached
          ? 'text-text-subtle cursor-not-allowed'
          : 'text-text-muted hover:text-text-brand'"
        :disabled="props.isTabLimitReached"
        :title="props.isTabLimitReached ? `Máximo ${props.tabs.length} pestañas` : 'Guardar filtros como nueva pestaña'"
        @click="!props.isTabLimitReached && startCreate()"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>

      <!-- Fixed trailing config tab (opt-in per view) -->
      <button
        v-if="showConfigTab"
        type="button"
        data-testid="filter-tabs-config"
        class="ml-auto px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
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
        <BaseButton variant="primary" size="md" data-testid="filter-tabs-confirm" :disabled="!inputName.trim()" @click="confirmInput">
          {{ isRenaming ? 'Renombrar' : 'Guardar' }}
        </BaseButton>
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
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue';
import BaseDropdown from '~/components/base/BaseDropdown.vue';
import { sameFilters } from '~/composables/useSavedFilterTabs';
import { SELECT_ARROW_STYLE as selectArrowStyle } from '~/utils/selectArrowStyle';

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  activeTabId: { type: String, default: 'all' },
  isTabLimitReached: { type: Boolean, default: false },
  // Optional per-tab match count, keyed by tab id, so a quick filter can show
  // how many rows it would leave without being applied. Views that pass
  // nothing render exactly as before.
  counts: { type: Object, default: () => ({}) },
  // What the count badge means, which is not the same sentence in every view.
  countTitle: { type: String, default: 'Registros que cumplen este filtro' },
  // How many tabs the strip shows before the rest move into a "+N" menu.
  // 0 keeps the previous behaviour: every tab rendered inline.
  maxVisible: { type: Number, default: 0 },
  // Opt-in fixed trailing "Configuraciones" tab (clients/proposals views).
  showConfigTab: { type: Boolean, default: false },
  configActive: { type: Boolean, default: false },
});

const emit = defineEmits([
  'select', 'create', 'rename', 'delete', 'config', 'restore', 'rebase',
]);

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

// A tab hidden from Configuración keeps existing; it just stops taking room.
const visibleTabs = computed(() => props.tabs.filter((tab) => !tab.is_hidden));

/**
 * Split the strip into what is shown inline and what moves into the "+N".
 *
 * The selected tab is always inline: swapped with the last visible slot when
 * it would have landed in the menu, so the strip never reads as if nothing
 * were applied.
 */
const splitTabs = computed(() => {
  const all = visibleTabs.value;
  const limit = Number(props.maxVisible) || 0;
  if (!limit || all.length <= limit) return { strip: all, overflow: [] };

  const strip = all.slice(0, limit);
  const overflow = all.slice(limit);
  const active = overflow.find(
    (tab) => String(tab.id) === String(props.activeTabId),
  );
  if (active) {
    const displaced = strip[limit - 1];
    strip[limit - 1] = active;
    overflow[overflow.indexOf(active)] = displaced;
  }
  return { strip, overflow };
});

const stripTabs = computed(() => splitTabs.value.strip);
const overflowTabs = computed(() => splitTabs.value.overflow);

const overflowItems = computed(() =>
  overflowTabs.value.map((tab) => {
    const count = countFor(tab);
    return {
      label: count != null ? `${tab.name} (${count})` : tab.name,
      onClick: () => emit('select', tab.id),
    };
  }),
);

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
