<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 max-w-md w-full text-center">
      <div v-if="isLoading" class="space-y-4">
        <div class="w-8 h-8 border-2 border-[#0A66C2]/30 border-t-[#0A66C2] rounded-full animate-spin mx-auto" />
        <p class="text-sm text-gray-600">Conectando con LinkedIn...</p>
      </div>
      <div v-else-if="success" class="space-y-4">
        <div class="w-12 h-12 bg-emerald-50 rounded-full flex items-center justify-center mx-auto">
          <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        </div>
        <p class="text-sm text-gray-900 font-medium">LinkedIn conectado correctamente</p>
        <p class="text-xs text-gray-500">Puedes cerrar esta ventana.</p>
      </div>
      <div v-else class="space-y-4">
        <div class="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto">
          <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </div>
        <p class="text-sm text-red-600">{{ errorMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useBlogStore } from '~/stores/blog';

definePageMeta({ layout: 'blank' });

const blogStore = useBlogStore();
const isLoading = ref(true);
const success = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const error = params.get('error');

  if (error) {
    isLoading.value = false;
    errorMessage.value = `LinkedIn: ${params.get('error_description') || error}`;
    return;
  }

  if (!code) {
    isLoading.value = false;
    errorMessage.value = 'No se recibió código de autorización.';
    return;
  }

  const state = params.get('state') || '';
  const result = await blogStore.linkedinCallback(code, state);
  isLoading.value = false;

  if (result.success) {
    success.value = true;
    // Notify opener window
    if (window.opener) {
      window.opener.postMessage({ type: 'linkedin-connected', data: result.data?.connection }, '*');
    }
  } else {
    errorMessage.value = result.error || 'Error al conectar con LinkedIn.';
  }
});
</script>
