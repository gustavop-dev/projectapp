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
        @change="$emit('select', $event.target.value)"
      >
        <option value="all">Todas</option>
        <option v-for="tab in tabs" :key="tab.id" :value="tab.id">
          {{ tab.name }}
        </option>
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
          : 'border-transparent text-text-muted hover:text-text-default dark:text-gray-400 dark:hover:text-gray-300'"
        @click="$emit('select', 'all')"
      >
        Todas
      </button>

      <!-- Saved tabs -->
      <div
        v-for="tab in tabs"
        :key="tab.id"
        class="relative group flex items-center"
      >
        <button
          type="button"
          :data-testid="`filter-tabs-tab-${tab.id}`"
          class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
          :class="activeTabId === tab.id
            ? 'border-emerald-600 text-text-brand'
            : 'border-transparent text-text-muted hover:text-text-default dark:text-gray-400 dark:hover:text-gray-300'"
          @click="$emit('select', tab.id)"
        >
          {{ tab.name }}
        </button>
        <!-- Tab context menu trigger -->
        <button
          type="button"
          :data-testid="`filter-tabs-menu-${tab.id}`"
          class="p-0.5 rounded text-gray-400 hover:text-text-muted dark:hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity -ml-1 mr-1"
          @click.stop="toggleMenu(tab.id)"
        >
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
          </svg>
        </button>
        <!-- Dropdown menu -->
        <div
          v-if="openMenuId === tab.id"
          class="absolute top-full left-0 mt-1 z-50 bg-surface border border-border-default rounded-lg shadow-lg py-1 min-w-[140px]"
        >
          <button
            type="button"
            data-testid="filter-tabs-rename"
            class="w-full px-3 py-1.5 text-left text-sm text-text-default hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="startRename(tab)"
          >
            Renombrar
          </button>
          <button
            type="button"
            data-testid="filter-tabs-delete"
            class="w-full px-3 py-1.5 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            @click="handleDelete(tab.id)"
          >
            Eliminar
          </button>
        </div>
      </div>

      <!-- "+" button to create new tab -->
      <button
        type="button"
        data-testid="filter-tabs-create"
        class="px-3 py-2.5 text-sm font-medium transition-colors border-b-2 border-transparent -mb-px"
        :class="props.isTabLimitReached
          ? 'text-gray-300 dark:text-text-muted cursor-not-allowed'
          : 'text-gray-400 hover:text-text-brand dark:text-text-muted dark:hover:text-emerald-400'"
        :disabled="props.isTabLimitReached"
        :title="props.isTabLimitReached ? `Máximo ${props.tabs.length} pestañas` : 'Guardar filtros como nueva pestaña'"
        @click="!props.isTabLimitReached && startCreate()"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
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
        <button
          type="button"
          data-testid="filter-tabs-confirm"
          class="px-3 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-strong transition-colors disabled:opacity-50"
          :disabled="!inputName.trim()"
          @click="confirmInput"
        >
          {{ isRenaming ? 'Renombrar' : 'Guardar' }}
        </button>
        <button
          type="button"
          data-testid="filter-tabs-cancel"
          class="px-3 py-2 bg-gray-100 text-text-muted rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          @click="cancelInput"
        >
          Cancelar
        </button>
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
import { nextTick, ref } from 'vue';
import { SELECT_ARROW_STYLE as selectArrowStyle } from '~/utils/selectArrowStyle';

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  activeTabId: { type: String, default: 'all' },
  isTabLimitReached: { type: Boolean, default: false },
});

const emit = defineEmits(['select', 'create', 'rename', 'delete']);

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

</script>
