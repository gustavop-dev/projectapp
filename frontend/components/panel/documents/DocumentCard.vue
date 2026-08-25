<script setup>
import { computed } from 'vue'
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue'
import {
  documentStatusBadgeClass, documentStatusLabel, formatDocumentDate, archivedAgeLabel,
} from '~/utils/documentStatus'
import { makeSafeExcerpt } from '~/utils/markdownExcerpt'
import { tagBadgeClass, tagDotClass } from '~/utils/documentTagColors.js'
import BaseButton from '~/components/base/BaseButton.vue'
import BaseOverflowText from '~/components/base/BaseOverflowText.vue'

const props = defineProps({
  document: { type: Object, required: true },
  editTo: { type: [String, Object], default: null },
  newlyCreated: { type: Boolean, default: false },
  dragging: { type: Boolean, default: false },
  archived: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'action', 'dragstart', 'dragend'])

const MAX_TAGS = 2

const excerpt = computed(() => makeSafeExcerpt(props.document.content_excerpt || ''))
const tags = computed(() => props.document.tag_details || [])
const visibleTags = computed(() => tags.value.slice(0, MAX_TAGS))
const extraTagNames = computed(() => tags.value.slice(MAX_TAGS).map((t) => t.name).join(', '))

const meta = computed(() => {
  const parts = []
  const clientLabel = props.document.client_display_name || props.document.client_name
  if (clientLabel) parts.push(clientLabel)
  if (props.document.project_name) parts.push(props.document.project_name)
  if (props.archived) {
    parts.push(`Archivado · ${archivedAgeLabel(props.document.archived_at) || '—'}`)
  } else {
    parts.push(formatDocumentDate(props.document.created_at))
  }
  return parts.join(' · ')
})
</script>

<template>
  <article
    class="group bg-surface border border-border-muted rounded-xl shadow-card overflow-hidden
           cursor-pointer select-none [content-visibility:auto]
           focus-within:ring-2 focus-within:ring-focus-ring/40
           hover:shadow-raised motion-safe:transition-[transform,box-shadow]
           motion-safe:duration-fast motion-safe:ease-out-soft motion-safe:hover:-translate-y-0.5"
    :class="[
      { 'opacity-50': dragging },
      { 'ring-2 ring-focus-ring/40 bg-primary-soft': newlyCreated },
    ]"
    :draggable="!archived"
    :data-testid="`document-card-${document.id}`"
    @click="emit('open', $event)"
    @auxclick.middle="emit('open', $event)"
    @dragstart="emit('dragstart', $event)"
    @dragend="emit('dragend', $event)"
  >
    <!-- Mini-preview -->
    <div class="relative h-36 overflow-hidden border-b border-border-muted" aria-hidden="true">
      <DocumentMarkdownBody
        v-if="excerpt"
        :markdown="excerpt"
        variant="mini"
        class="px-4 py-3 pointer-events-none select-none"
      />
      <div v-else class="flex items-center justify-center h-full text-text-subtle">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div class="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-surface to-transparent"></div>
      <span
        v-if="archived"
        class="absolute top-2 right-2 inline-flex items-center rounded-full bg-surface-raised px-2 py-0.5 text-2xs font-semibold uppercase text-text-muted shadow-sm dark:text-text-subtle"
      >
        Archivado
      </span>
      <span
        v-else
        class="absolute top-2 right-2 inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium shadow-sm"
        :class="documentStatusBadgeClass(document.status)"
      >
        {{ documentStatusLabel(document.status) }}
      </span>
    </div>

    <!-- Info -->
    <div class="p-4">
      <!-- Sin `stretch`: el kebab vive en esta misma tarjeta y quedaría
           tapado. La tarjeta entera ya responde al clic simple. -->
      <BaseOverflowText
        :to="editTo"
        :text="document.title"
        :lines="2"
        :test-id="`document-card-open-${document.id}`"
        content-classes="text-sm font-semibold leading-snug text-text-default"
      />
      <p class="text-xs text-text-muted mt-1 tabular-nums truncate">{{ meta }}</p>

      <div class="flex items-center justify-between gap-2 mt-2 min-h-11">
        <div class="flex flex-wrap items-center gap-1 min-w-0">
          <span
            v-for="tag in visibleTags"
            :key="tag.id"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-2xs font-medium"
            :class="tagBadgeClass(tag.color)"
          >
            <span class="w-1.5 h-1.5 rounded-full" :class="tagDotClass(tag.color)"></span>
            {{ tag.name }}
          </span>
          <BaseTooltip v-if="extraTagNames" :text="extraTagNames">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium bg-surface-raised text-text-muted">
              +{{ tags.length - 2 }}
            </span>
          </BaseTooltip>
          <span v-if="tags.length === 0" class="text-2xs text-text-subtle">—</span>
        </div>
        <BaseButton
          variant="ghost"
          size="lg"
          icon-only
          title="Acciones"
          :aria-label="`Acciones de ${document.title}`"
          class="flex-shrink-0 min-w-11 min-h-11 -mr-2 text-text-subtle hover:text-text-default"
          @click.stop="emit('action')"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="5" r="1.6" />
            <circle cx="12" cy="12" r="1.6" />
            <circle cx="12" cy="19" r="1.6" />
          </svg>
        </BaseButton>
      </div>
    </div>
  </article>
</template>
