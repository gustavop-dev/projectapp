<template>
  <div :data-testid="testId" class="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3">
    <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
      <span><span class="text-gray-500">Secciones:</span> <span class="font-medium text-gray-900">{{ stats.sectionCount }}</span></span>
      <span><span class="text-gray-500">Progreso:</span> <span class="font-medium text-gray-900">{{ stats.progress }}%</span></span>
      <span><span class="text-gray-500">Tamaño del JSON:</span> <span class="font-medium text-gray-900">{{ stats.size }}</span></span>
      <span><span class="text-gray-500">Última actualización:</span> <span class="font-medium text-gray-900">{{ stats.updatedAt }}</span></span>
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
