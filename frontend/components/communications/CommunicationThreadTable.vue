<template>
  <div
    v-if="compact"
    class="min-w-0 max-w-full overflow-x-hidden"
    data-testid="communication-thread-list"
    :aria-busy="loading ? 'true' : undefined"
  >
    <p class="sr-only" aria-live="polite">
      {{ loading ? 'Cargando hilos...' : `${threads.length} hilos en la lista` }}
    </p>

    <ul v-if="loading && threads.length === 0" class="grid min-w-0 gap-2" aria-hidden="true">
      <li
        v-for="index in 4"
        :key="index"
        class="h-20 min-w-0 animate-pulse overflow-hidden rounded-xl border border-border-muted bg-surface p-3"
      >
        <div class="h-3 w-2/3 rounded bg-surface-raised" />
        <div class="mt-2 h-2.5 w-1/2 rounded bg-surface-raised" />
        <div class="mt-3 h-2.5 w-3/4 rounded bg-surface-raised" />
      </li>
    </ul>

    <ul v-else class="grid min-w-0 gap-2" aria-label="Hilos de comunicación">
      <li
        v-for="thread in threads"
        :key="thread.id"
        :data-testid="`communication-thread-row-${thread.id}`"
        class="relative min-w-0 cursor-pointer overflow-hidden rounded-xl border border-border-muted bg-surface px-3 py-2.5 shadow-sm transition-colors hover:bg-surface-raised"
        @click="$emit('open', thread, $event)"
        @auxclick.middle="$emit('open', thread, $event)"
      >
        <div class="flex min-w-0 items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <BaseRowLink
              :to="hrefFor(thread)"
              stretch
              class="block min-w-0 font-semibold text-text-default hover:text-text-brand"
              @click="$emit('link-activate', thread, $event)"
            >
              <span class="block truncate">{{ thread.title }}</span>
            </BaseRowLink>
            <p class="mt-0.5 truncate text-xs text-text-subtle">
              <span class="font-medium text-text-muted">{{ thread.client_name }}</span>
              <span aria-hidden="true"> · </span>
              <span>{{ thread.project_name || 'Sin proyecto' }}</span>
            </p>
          </div>
          <!-- Espejo de los badges del gestor documental: identifica la
               comunicacion madre de la entidad frente a las conversaciones
               sueltas. Sin estado detras en el caso del cliente, que no tiene
               catalogo de ciclo de vida. -->
          <BaseBadge v-if="thread.thread_kind === 'project'" variant="info" size="sm">
            Proyecto
          </BaseBadge>
          <BaseBadge v-else-if="thread.thread_kind === 'client'" variant="neutral" size="sm">
            Cliente
          </BaseBadge>
          <BaseBadge :variant="thread.status === 'open' ? 'success' : 'neutral'" size="sm">
            {{ thread.status === 'open' ? 'Abierto' : 'Cerrado' }}
          </BaseBadge>
        </div>

        <div class="mt-2 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-text-muted">
          <span v-if="thread.channels?.length" class="flex min-w-0 flex-wrap gap-1">
            <BaseBadge
              v-for="channel in thread.channels"
              :key="channel"
              :variant="channel === 'whatsapp' ? 'success' : 'info'"
              size="sm"
            >
              {{ channel === 'whatsapp' ? 'WhatsApp' : 'Correo' }}
            </BaseBadge>
          </span>
          <span v-else>Sin mensajes</span>
          <span aria-hidden="true">·</span>
          <span class="tabular-nums">
            {{ thread.messages_count }} mensaje{{ thread.messages_count === 1 ? '' : 's' }}
          </span>
          <span aria-hidden="true">·</span>
          <time
            class="whitespace-nowrap"
            :datetime="thread.last_activity_at || undefined"
            :aria-label="formatDateTime(thread.last_activity_at)"
          >
            {{ formatDayMonth(thread.last_activity_at) || '—' }}
          </time>
          <BaseBadge v-if="thread.draft_count" variant="warning" size="sm">
            {{ thread.draft_count }} borrador{{ thread.draft_count === 1 ? '' : 'es' }}
          </BaseBadge>
        </div>
      </li>
    </ul>
  </div>

  <BaseResponsiveTable
    v-else
    :columns="COLUMNS"
    :rows="threads"
    :loading="loading"
    :highlight-query="searchQuery"
    caption="Hilos de comunicación"
    test-id-prefix="communication-thread"
    :show-actions="false"
    :show-default-actions="false"
    interactive-rows
    @row-click="(row, event) => $emit('open', row, event)"
    @row-auxclick="(row, event) => $emit('open', row, event)"
  >
    <template #cell-title="{ row }">
      <BaseRowLink
        :to="hrefFor(row)"
        stretch
        class="block min-w-0 font-semibold text-text-default hover:text-text-brand"
        @click="$emit('link-activate', row, $event)"
      >
        <span class="block truncate" :title="row.title">{{ row.title }}</span>
      </BaseRowLink>
    </template>

    <template #cell-context="{ row }">
      <span class="block truncate font-medium" :title="row.client_name">{{ row.client_name }}</span>
      <span class="mt-0.5 block truncate text-xs text-text-subtle" :title="row.project_name || 'Sin proyecto'">
        {{ row.project_name || 'Sin proyecto' }}
      </span>
    </template>

    <template #cell-status="{ row }">
      <BaseBadge :variant="row.status === 'open' ? 'success' : 'neutral'" size="sm">
        {{ row.status === 'open' ? 'Abierto' : 'Cerrado' }}
      </BaseBadge>
    </template>

    <template #cell-channels="{ row }">
      <span v-if="row.channels?.length" class="flex flex-wrap gap-1">
        <BaseBadge
          v-for="channel in row.channels"
          :key="channel"
          :variant="channel === 'whatsapp' ? 'success' : 'info'"
          size="sm"
        >
          {{ channel === 'whatsapp' ? 'WhatsApp' : 'Correo' }}
        </BaseBadge>
      </span>
      <span v-else class="text-xs text-text-subtle">Sin mensajes</span>
    </template>

    <template #cell-messages="{ row }">
      <span class="block tabular-nums">{{ row.messages_count }}</span>
      <span v-if="row.draft_count" class="mt-0.5 block text-xs text-warning-strong">
        {{ row.draft_count }} borrador{{ row.draft_count === 1 ? '' : 'es' }}
      </span>
    </template>

    <template #cell-last_activity_at="{ row }">
      <span class="whitespace-nowrap text-xs text-text-muted">{{ formatDateTime(row.last_activity_at) }}</span>
    </template>

    <template #empty>
      <span>No hay hilos con este recorte.</span>
    </template>
  </BaseResponsiveTable>
</template>

<script setup>
import { formatDateTime, formatDayMonth } from '~/utils/formatDate';

defineProps({
  threads: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  hrefFor: { type: Function, required: true },
  compact: { type: Boolean, default: false },
});

defineEmits(['open', 'link-activate']);

const COLUMNS = [
  {
    key: 'title', label: 'Asunto', size: 'name', link: true, textPolicy: 'truncate',
    responsive: { primary: true, compact: 'keep', portrait: 'keep', landscape: 'keep' },
  },
  {
    key: 'context', label: 'Cliente / proyecto', size: 'name', textPolicy: 'truncate',
    responsive: { compact: 'group', portrait: 'keep', landscape: 'keep' },
  },
  {
    key: 'status', label: 'Estado', size: 'badge',
    responsive: { compact: 'group', portrait: 'group', landscape: 'keep' },
  },
  {
    key: 'channels', label: 'Canales', size: 'badge',
    responsive: { compact: 'group', portrait: 'group', landscape: 'group' },
  },
  {
    key: 'messages', label: 'Mensajes', size: 'tiny', align: 'center',
    responsive: { compact: 'group', portrait: 'group', landscape: 'group' },
  },
  {
    key: 'last_activity_at', label: 'Última actividad', size: 'date',
    responsive: { compact: 'group', portrait: 'keep', landscape: 'keep' },
  },
];
</script>
