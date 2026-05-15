<template>
  <span
    v-if="pathLabel"
    class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-surface-raised text-text-muted truncate max-w-[14rem]"
    :title="pathLabel"
  >
    <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7a2 2 0 012-2h4l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
    </svg>
    <span class="truncate">{{ pathLabel }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue';
import { useDocumentFolderStore } from '~/stores/document_folders';

const props = defineProps({
  folderId: { type: [Number, null], default: null },
});

const folderStore = useDocumentFolderStore();

const pathLabel = computed(() => {
  if (props.folderId == null) return '';
  const folder = folderStore.getById(props.folderId);
  if (!folder) return '';
  const ancestors = folderStore.ancestorsOf(props.folderId);
  const names = [...ancestors.map((a) => a.name), folder.name];
  return names.join(' › ');
});
</script>
