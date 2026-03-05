<template>
  <button
    class="pdf-download fixed bottom-20 right-4 z-40
           flex items-center gap-2 px-4 py-2.5
           bg-white/90 backdrop-blur-sm shadow-lg border border-gray-200
           rounded-xl text-sm font-medium text-gray-700
           hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200
           transition-colors"
    @click="openPrintView"
  >
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    <span>PDF</span>
  </button>
</template>

<script setup>
const route = useRoute();

function openPrintView() {
  const uuid = route.params.uuid;
  window.open(`/proposal/${uuid}/print`, '_blank');
}
</script>
