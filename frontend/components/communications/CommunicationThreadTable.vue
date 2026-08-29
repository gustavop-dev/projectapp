<template>
  <BaseResponsiveTable
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
        class="font-semibold text-text-default hover:text-text-brand"
        @click="$emit('link-activate', row, $event)"
      >
        <span class="block truncate" :title="row.title">{{ row.title }}</span>
      </BaseRowLink>
      <p
        v-if="row.latest_message"
        class="mt-1 line-clamp-2 text-xs font-normal text-text-subtle [overflow-wrap:anywhere]"
      >
        {{ row.latest_message.direction === 'incoming' ? 'Cliente:' : 'Nosotros:' }}
        {{ row.latest_message.content }}
      </p>
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
defineProps({
  threads: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  searchQuery: { type: String, default: '' },
  hrefFor: { type: Function, required: true },
});

defineEmits(['open', 'link-activate']);

const COLUMNS = [
  {
    key: 'title', label: 'Hilo', size: 'name', link: true, textPolicy: 'truncate',
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

function formatDateTime(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium', timeStyle: 'short',
  }).format(new Date(value));
}
</script>
