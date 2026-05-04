<template>
  <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
      <div>
        <h3 class="text-sm font-medium text-text-default">Checklist de desarrollo</h3>
        <p class="text-xs text-text-subtle mt-0.5">
          Markdown listo para el equipo de diseño y desarrollo. Se actualiza al recargar la propuesta.
        </p>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0">
        <BaseButton
          variant="secondary"
          size="sm"
          :disabled="refreshing"
          @click="handleRefresh"
        >
          <svg
            class="w-3.5 h-3.5"
            :class="{ 'animate-spin': refreshing }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Actualizar
        </BaseButton>
        <BaseButton
          variant="secondary"
          size="sm"
          :disabled="!markdown"
          @click="handleCopy"
        >
          <DocumentDuplicateIcon class="w-3.5 h-3.5" />
          {{ copied ? '¡Copiado!' : 'Copiar' }}
        </BaseButton>
        <BaseButton
          variant="secondary"
          size="sm"
          :disabled="!markdown"
          @click="handleDownload"
        >
          <ArrowDownTrayIcon class="w-3.5 h-3.5" />
          Descargar
        </BaseButton>
      </div>
    </div>

    <textarea
      :value="markdown"
      readonly
      data-testid="dev-checklist-markdown-textarea"
      :rows="22"
      class="w-full px-4 py-3 border border-border-default dark:border-white/[0.08] rounded-xl text-xs font-mono leading-relaxed
             bg-surface-raised text-text-default outline-none resize-y cursor-text select-all"
    />
  </div>
</template>

<script setup>
import { ref, toRef } from 'vue';
import { DocumentDuplicateIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import { useDevChecklistMarkdown } from '~/composables/useDevChecklistMarkdown';

const props = defineProps({
  proposal: {
    type: Object,
    default: null,
  },
  refreshing: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['refresh']);

const { markdown, filename } = useDevChecklistMarkdown(toRef(props, 'proposal'));

const copied = ref(false);

function handleRefresh() {
  emit('refresh');
}

async function handleCopy() {
  if (!markdown.value) return;
  try {
    await navigator.clipboard.writeText(markdown.value);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch (e) {
    console.error('Copy failed:', e);
  }
}

function handleDownload() {
  if (!markdown.value) return;
  const blob = new Blob([markdown.value], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename.value;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
</script>
