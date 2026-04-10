<template>
  <div v-if="issues.length" class="mt-4 bg-amber-50 dark:bg-amber-500/10 border border-amber-300 dark:border-amber-500/20 rounded-xl p-4">
    <div class="flex items-start gap-3">
      <svg class="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.963-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-1">JSON con formato desactualizado</h4>
        <p class="text-xs text-amber-700 dark:text-amber-300 mb-3 leading-relaxed">
          El JSON que cargaste no corresponde al formato actual del documento técnico. Los siguientes campos usan una estructura antigua que el sistema no puede renderizar correctamente:
        </p>
        <ul class="text-xs text-amber-700 dark:text-amber-300 space-y-1 mb-4 pl-4 list-disc">
          <li v-for="issue in issues" :key="issue">
            <code class="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded text-[11px]">{{ fieldLabels[issue] || issue }}</code>
          </li>
        </ul>
        <p class="text-xs text-amber-700 dark:text-amber-300 mb-3">{{ actionLabel }}</p>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg transition-colors"
          @click="$emit('download')"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Descargar JSON corregido
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  issues: { type: Array, required: true },
  fieldLabels: { type: Object, required: true },
  actionLabel: { type: String, default: 'Descarga la versión corregida y úsala para crear o actualizar la propuesta:' },
});
defineEmits(['download']);
</script>
