<script setup>
import { ref } from 'vue';
import { formatDateTime } from '~/utils/formatDate';
import BaseCollapse from '~/components/base/BaseCollapse.vue';

/**
 * Sent-email history panel — shared by the Proposals and Diagnostics email
 * composers. Self-contained expand/collapse (animated via BaseCollapse). The
 * consumer owns pagination and emits nothing but `load-more`.
 *
 * The `#entry-meta` slot receives each entry so a module can append extra
 * metadata (e.g. the diagnostics template label) after the date.
 */
defineProps({
  history: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  hasNextPage: { type: Boolean, default: false },
  emptyLabel: { type: String, default: 'No se han enviado correos.' },
})

defineEmits(['load-more'])

const STATUS_LABELS = { sent: 'Enviado', delivered: 'Entregado', bounced: 'Rebotado', failed: 'Fallido' }
function statusLabel(s) { return STATUS_LABELS[s] || s }

function formatDate(isoString) {
  return formatDateTime(isoString, { fallback: '' })
}

// metadata.sections stores legacy plain strings and new {text, markdown} dicts.
function sectionText(section) {
  return typeof section === 'string' ? section : (section?.text || '')
}
function sectionIsMarkdown(section) {
  return typeof section === 'object' && !!section?.markdown
}

const expandedIds = ref({})
function toggleExpand(id) {
  if (expandedIds.value[id]) delete expandedIds.value[id]
  else expandedIds.value[id] = true
}
</script>

<template>
  <div v-if="loading && !history.length" class="text-xs text-text-subtle py-4 text-center">
    Cargando historial…
  </div>
  <div v-else-if="!history.length" class="text-xs text-text-subtle py-4 text-center">
    {{ emptyLabel }}
  </div>
  <div v-else class="space-y-2">
    <div v-for="entry in history" :key="entry.id"
      class="border border-border-muted rounded-lg overflow-hidden">
      <button type="button" @click="toggleExpand(entry.id)"
        class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-surface-muted motion-safe:transition-colors motion-safe:duration-fast focus:outline-none focus:ring-2 focus:ring-focus-ring/40">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-text-default truncate">{{ entry.subject }}</span>
            <span class="px-1.5 py-0.5 rounded text-2xs font-medium"
              :class="{
                'bg-primary-soft text-text-brand': entry.status === 'sent' || entry.status === 'delivered',
                'bg-danger-soft text-danger-strong': entry.status === 'failed' || entry.status === 'bounced',
              }">{{ statusLabel(entry.status) }}</span>
          </div>
          <div class="flex items-center gap-2 mt-0.5">
            <span class="text-2xs text-text-muted">{{ entry.recipient }}</span>
            <span class="text-2xs text-text-subtle">{{ formatDate(entry.sent_at) }}</span>
            <slot name="entry-meta" :entry="entry" />
          </div>
        </div>
        <svg class="w-4 h-4 text-text-subtle motion-safe:transition-transform motion-safe:duration-fast" :class="{ 'rotate-180': expandedIds[entry.id] }"
          fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <BaseCollapse :open="Boolean(expandedIds[entry.id])">
        <div class="border-t border-border-muted px-4 py-3 bg-surface-muted space-y-3">
          <div v-if="entry.metadata?.greeting">
            <p class="text-2xs text-text-subtle uppercase tracking-wide mb-0.5">Saludo</p>
            <p class="text-xs text-text-default">{{ entry.metadata.greeting }}</p>
          </div>
          <div v-if="entry.metadata?.sections?.length">
            <p class="text-2xs text-text-subtle uppercase tracking-wide mb-1">Secciones</p>
            <div v-for="(section, idx) in entry.metadata.sections" :key="idx"
              class="bg-surface rounded-lg px-3 py-2 mb-1.5 border border-border-muted">
              <span v-if="sectionIsMarkdown(section)"
                class="inline-block mb-1 px-1.5 py-0.5 bg-primary-soft text-text-brand rounded text-[9px] font-medium uppercase tracking-wide">MD</span>
              <p class="text-xs text-text-default whitespace-pre-wrap">{{ sectionText(section) }}</p>
            </div>
          </div>
          <div v-if="entry.metadata?.footer">
            <p class="text-2xs text-text-subtle uppercase tracking-wide mb-0.5">Pie de correo</p>
            <p class="text-xs text-text-default">{{ entry.metadata.footer }}</p>
          </div>
          <div v-if="entry.metadata?.attachment_names?.length">
            <p class="text-2xs text-text-subtle uppercase tracking-wide mb-0.5">Adjuntos</p>
            <div class="flex flex-wrap gap-1">
              <span v-for="(name, idx) in entry.metadata.attachment_names" :key="idx"
                class="inline-flex items-center gap-1 px-2 py-0.5 bg-surface border border-border-default rounded text-2xs text-text-muted">
                &#128206; {{ name }}
              </span>
            </div>
          </div>
        </div>
      </BaseCollapse>
    </div>

    <div v-if="hasNextPage" class="pt-3 text-center">
      <button type="button" :disabled="loading" @click="$emit('load-more')"
        class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-text-muted bg-surface-muted rounded-lg hover:bg-border-muted motion-safe:transition-colors motion-safe:duration-fast disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-focus-ring/40">
        {{ loading ? 'Cargando…' : 'Cargar más' }}
      </button>
    </div>
  </div>
</template>
