<script setup>
import { computed } from 'vue';

import BaseActionIcon from '~/components/base/BaseActionIcon.vue';
import BaseButton from '~/components/base/BaseButton.vue';

const props = defineProps({
  results: { type: Array, default: () => [] },
  inputText: { type: String, default: '' },
  modelValue: { type: [Number, null], default: null },
  highlightIndex: { type: Number, default: -1 },
  hasSearched: { type: Boolean, default: false },
  isSearching: { type: Boolean, default: false },
  isLoadingMore: { type: Boolean, default: false },
  searchError: { type: String, default: '' },
  loadMoreError: { type: String, default: '' },
  presentation: { type: String, default: 'floating' },
  sortDirection: { type: String, default: 'asc' },
  listboxId: { type: String, default: undefined },
});

const emit = defineEmits([
  'create-new',
  'highlight',
  'load-more',
  'retry',
  'select',
  'toggle-sort',
]);

const isCatalog = computed(() => props.presentation === 'catalog');

const clientHasNoEmail = (client) => (
  Boolean(client?.is_email_placeholder) || !String(client?.email || '').trim()
);

function onCatalogScroll(event) {
  const panel = event.currentTarget;
  const remaining = panel.scrollHeight - panel.scrollTop - panel.clientHeight;
  if (remaining <= 48) emit('load-more');
}
</script>

<template>
  <div
    v-if="isCatalog"
    class="overflow-hidden rounded-xl border border-border-default bg-surface"
    data-testid="client-catalog"
  >
    <div
      role="row"
      class="grid h-10 grid-cols-1 items-center border-b border-border-muted bg-surface-muted px-4 text-xs font-semibold uppercase tracking-wide text-text-subtle panel-portrait:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1.4fr)]"
    >
      <div
        role="columnheader"
        :aria-sort="sortDirection === 'desc' ? 'descending' : 'ascending'"
      >
        <!-- design-tokens: allow-raw-button (sortable column header, not a standalone action) -->
        <button
          type="button"
          class="inline-flex items-center gap-1.5 rounded-md text-left hover:text-text-default focus:outline-none focus:ring-2 focus:ring-focus-ring/30"
          :aria-label="sortDirection === 'desc'
            ? 'Ordenar clientes por nombre de A a Z'
            : 'Ordenar clientes por nombre de Z a A'"
          data-testid="client-catalog-sort-name"
          @click="emit('toggle-sort')"
        >
          <span>Nombre</span>
          <BaseActionIcon
            :action="sortDirection === 'desc' ? 'sort-descending' : 'sort-ascending'"
            class="h-3.5 w-3.5"
          />
        </button>
      </div>
      <div role="columnheader" class="hidden panel-portrait:block">Empresa</div>
      <div role="columnheader" class="hidden panel-portrait:block">Correo</div>
    </div>

    <div
      :id="listboxId"
      role="listbox"
      class="max-h-80 overflow-y-auto overscroll-contain panel-portrait:max-h-72"
      data-testid="client-catalog-scroll"
      :aria-busy="isSearching || isLoadingMore"
      @scroll.passive="onCatalogScroll"
    >
      <div
        v-if="isSearching"
        class="px-4 py-3 text-center text-sm text-text-subtle"
      >
        {{ inputText.trim() ? 'Buscando...' : 'Cargando clientes...' }}
      </div>

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
          @click="emit('retry')"
        >
          Reintentar
        </button>
      </div>

      <template v-else-if="results.length > 0">
        <!-- design-tokens: allow-raw-button (each option is a selectable list row) -->
        <button
          v-for="(client, idx) in results"
          :key="client.id"
          type="button"
          role="option"
          :aria-selected="modelValue === client.id"
          :data-testid="`client-autocomplete-option-${client.id}`"
          :class="[
            'grid h-16 w-full grid-cols-1 content-center border-b border-border-muted px-4 py-2 text-left text-sm transition-colors panel-portrait:h-14 panel-portrait:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1.4fr)] panel-portrait:items-center',
            modelValue === client.id || highlightIndex === idx
              ? 'bg-primary-soft'
              : 'hover:bg-surface-raised',
          ]"
          @click="emit('select', client)"
          @mouseenter="emit('highlight', idx)"
          @focus="emit('highlight', idx)"
        >
          <span class="min-w-0 font-medium text-text-default">
            <span class="block truncate" :title="client.name">
              {{ client.name }}
              <span class="font-normal tabular-nums text-text-subtle">(#{{ client.id }})</span>
            </span>
          </span>
          <span class="min-w-0 truncate text-xs text-text-muted" :title="client.company || ''">
            <span class="panel-portrait:hidden">Empresa: </span>{{ client.company || '—' }}
          </span>
          <span class="min-w-0 truncate text-xs text-text-muted">
            <span class="panel-portrait:hidden">Correo: </span>
            <span
              v-if="clientHasNoEmail(client)"
              class="rounded-full bg-warning-soft px-1.5 py-0.5 font-medium text-warning-strong"
              title="Este cliente todavía no tiene correo. Las acciones que envían mensajes pedirán agregarlo antes de continuar."
            >
              Sin correo
            </span>
            <span v-else class="truncate" :title="client.email">{{ client.email }}</span>
          </span>
        </button>

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
          <button
            type="button"
            class="font-medium text-text-brand hover:underline"
            @click="emit('load-more')"
          >
            Reintentar
          </button>
        </div>
      </template>

      <div v-else-if="hasSearched" class="px-4 py-3 text-sm text-text-muted">
        <p class="mb-2">
          {{ inputText.trim()
            ? `No se encontraron clientes con "${inputText}".`
            : 'No hay clientes registrados.' }}
        </p>
        <BaseButton
          variant="secondary"
          size="sm"
          class="w-full"
          data-testid="client-autocomplete-create-new"
          @click="emit('create-new')"
        >
          <BaseActionIcon action="create" />
          <span>{{ inputText.trim()
            ? `Crear nuevo cliente "${inputText.trim()}"`
            : 'Crear un cliente' }}</span>
        </BaseButton>
      </div>

      <div v-else class="px-4 py-3 text-center text-sm text-text-subtle">
        Cargando clientes...
      </div>
    </div>
  </div>

  <template v-else>
    <div v-if="isSearching" class="px-4 py-3 text-center text-sm text-text-subtle">
      {{ inputText.trim() ? 'Buscando...' : 'Cargando clientes...' }}
    </div>

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
        @click="emit('retry')"
      >
        Reintentar
      </button>
    </div>

    <template v-else-if="results.length > 0">
      <ul class="divide-y divide-border-muted">
        <li
          v-for="(client, idx) in results"
          :key="client.id"
          role="option"
          :aria-selected="highlightIndex === idx"
          :data-testid="`client-autocomplete-option-${client.id}`"
          :class="[
            'cursor-pointer px-4 py-2.5 transition-colors',
            highlightIndex === idx ? 'bg-primary-soft' : 'hover:bg-surface-raised',
          ]"
          @click="emit('select', client)"
          @mouseenter="emit('highlight', idx)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="truncate text-sm font-medium text-text-default">
                  {{ client.name }}
                  <span class="font-normal tabular-nums text-text-subtle">(#{{ client.id }})</span>
                </p>
                <span
                  v-if="clientHasNoEmail(client)"
                  class="rounded-full bg-warning-soft px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-warning-strong"
                  title="Este cliente todavía no tiene correo. Las acciones que envían mensajes pedirán agregarlo antes de continuar."
                >
                  Sin correo
                </span>
              </div>
              <p class="mt-0.5 truncate text-xs text-text-muted">
                <span v-if="client.company">{{ client.company }} · </span>
                {{ clientHasNoEmail(client)
                  ? 'Correo pendiente · habrá que agregarlo para enviar'
                  : client.email }}
              </p>
            </div>
            <p v-if="client.phone" class="flex-shrink-0 text-xs tabular-nums text-text-subtle">
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
        <button type="button" class="font-medium text-text-brand hover:underline" @click="emit('load-more')">
          Reintentar
        </button>
      </div>
    </template>

    <div v-else-if="hasSearched" class="px-4 py-3 text-sm text-text-muted">
      <p class="mb-2">
        {{ inputText.trim()
          ? `No se encontraron clientes con "${inputText}".`
          : 'No hay clientes registrados.' }}
      </p>
      <BaseButton
        variant="secondary"
        size="sm"
        class="w-full"
        data-testid="client-autocomplete-create-new"
        @click="emit('create-new')"
      >
        <BaseActionIcon action="create" />
        <span>{{ inputText.trim()
          ? `Crear nuevo cliente "${inputText.trim()}"`
          : 'Crear un cliente' }}</span>
      </BaseButton>
    </div>

    <div v-else class="px-4 py-3 text-center text-sm text-text-subtle">
      Cargando clientes...
    </div>
  </template>
</template>
