<template>
  <div :data-testid="testId" class="rounded-xl border border-border-muted bg-gray-50 px-4 py-3">
    <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
      <span><span class="text-text-muted">Secciones:</span> <span class="font-medium text-text-default">{{ stats.sectionCount }}</span></span>
      <span><span class="text-text-muted">Progreso:</span> <span class="font-medium text-text-default">{{ stats.progress }}%</span></span>
      <span><span class="text-text-muted">Tamaño del JSON:</span> <span class="font-medium text-text-default">{{ stats.size }}</span></span>
      <span><span class="text-text-muted">Última actualización:</span> <span class="font-medium text-text-default">{{ stats.updatedAt }}</span></span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stats: {
    type: Object,
    required: true,
  },
  testId: {
    type: String,
    required: true,
  },
})
</script>
