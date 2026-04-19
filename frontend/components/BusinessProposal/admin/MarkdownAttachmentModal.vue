<template>
  <Teleport to="body">
    <div v-if="open"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="onClose">
      <div class="bg-white dark:bg-esmerald rounded-2xl shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col overflow-hidden">

        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-white/[0.06]">
          <div>
            <h2 class="text-base font-semibold text-gray-800 dark:text-white">Adjuntar documento PDF al correo</h2>
            <p class="text-xs text-gray-500 dark:text-green-light/60 mt-0.5">
              Escribe en markdown, previsualiza el PDF y adjúntalo al composer.
            </p>
          </div>
          <button type="button" @click="onClose"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Body: 2 columns -->
        <div class="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-0 overflow-hidden">
          <!-- Editor column -->
          <div class="p-6 overflow-y-auto border-r border-gray-100 dark:border-white/[0.06] space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-green-light mb-1">Título del documento</label>
              <input v-model="title" type="text" placeholder="Ej: Resumen de cambios al alcance"
                class="w-full px-3 py-2 text-sm border border-gray-200 dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" />
            </div>

            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-green-light mb-1">Contenido (markdown)</label>
              <textarea v-model="markdown" rows="14"
                placeholder="# Encabezado&#10;&#10;Párrafo de introducción…"
                class="w-full px-3 py-2 text-sm font-mono border border-gray-200 dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y min-h-[280px]"></textarea>
            </div>

            <fieldset class="space-y-2">
              <legend class="text-xs font-medium text-gray-700 dark:text-green-light mb-1">Portadas</legend>
              <label class="flex items-center gap-2 text-xs text-gray-700 dark:text-green-light">
                <input type="checkbox" v-model="includePortada" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                Portada principal
              </label>
              <label class="flex items-center gap-2 text-xs text-gray-700 dark:text-green-light">
                <input type="checkbox" v-model="includeSubportada" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                Portada secundaria (carátula con título)
              </label>
              <label class="flex items-center gap-2 text-xs text-gray-700 dark:text-green-light">
                <input type="checkbox" v-model="includeContraportada" class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                Contraportada
              </label>
            </fieldset>

            <div v-if="error" class="text-xs text-red-500">{{ error }}</div>

            <button type="button" :disabled="!canPreview || loading"
              @click="generatePreview"
              class="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              {{ loading ? 'Generando…' : (previewUrl ? 'Actualizar vista previa' : 'Vista previa') }}
            </button>
          </div>

          <!-- Preview column -->
          <div class="bg-gray-50 dark:bg-white/[0.02] flex flex-col overflow-hidden">
            <div v-if="previewUrl" class="flex-1 min-h-0">
              <iframe :src="previewUrl" class="w-full h-full border-0" title="Vista previa PDF"></iframe>
            </div>
            <div v-else class="flex-1 flex items-center justify-center text-center p-8">
              <div class="max-w-xs">
                <svg class="w-12 h-12 mx-auto text-gray-300 dark:text-white/20 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p class="text-xs text-gray-400 dark:text-green-light/40">
                  Escribe un título y contenido, luego pulsa <span class="font-medium">Vista previa</span> para ver cómo queda el PDF.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 dark:border-white/[0.06]">
          <button type="button" @click="onClose"
            class="px-4 py-2 text-xs font-medium text-gray-600 dark:text-green-light bg-gray-50 dark:bg-white/[0.03] rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors">
            Cancelar
          </button>
          <button type="button" :disabled="!canAttach || loading"
            @click="attachToEmail"
            class="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
            {{ loading ? 'Procesando…' : 'Adjuntar al correo' }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import axios from 'axios';
import { getCookie } from '~/stores/services/request_http';

const props = defineProps({
  open: { type: Boolean, default: false },
  proposalId: { type: [Number, String], required: true },
});

const emit = defineEmits(['close', 'attach']);

const title = ref('');
const markdown = ref('');
const includePortada = ref(true);
const includeSubportada = ref(true);
const includeContraportada = ref(true);

const previewUrl = ref(null);
const previewSnapshot = ref(null);
const loading = ref(false);
const error = ref('');

const canPreview = computed(() => title.value.trim() && markdown.value.trim());
const canAttach = computed(() => canPreview.value);

const currentSnapshot = computed(() => JSON.stringify({
  title: title.value.trim(),
  markdown: markdown.value,
  p: includePortada.value,
  s: includeSubportada.value,
  c: includeContraportada.value,
}));

function revokePreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }
}

async function fetchPdfBlob() {
  const payload = {
    title: title.value.trim(),
    markdown: markdown.value,
    include_portada: includePortada.value,
    include_subportada: includeSubportada.value,
    include_contraportada: includeContraportada.value,
  };
  const response = await axios.post(
    `/api/proposals/${props.proposalId}/proposal-email/markdown-attachment/`,
    payload,
    {
      responseType: 'blob',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
    },
  );
  return response.data;
}

async function generatePreview() {
  if (!canPreview.value) return;
  loading.value = true;
  error.value = '';
  try {
    const blob = await fetchPdfBlob();
    revokePreview();
    previewUrl.value = URL.createObjectURL(blob);
    previewSnapshot.value = currentSnapshot.value;
  } catch (e) {
    error.value = 'No se pudo generar la vista previa.';
  } finally {
    loading.value = false;
  }
}

function slugify(s) {
  return (s || 'documento')
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'documento';
}

async function attachToEmail() {
  if (!canAttach.value) return;
  loading.value = true;
  error.value = '';
  try {
    let blob;
    if (previewUrl.value && previewSnapshot.value === currentSnapshot.value) {
      blob = await (await fetch(previewUrl.value)).blob();
    } else {
      blob = await fetchPdfBlob();
    }
    const filename = `${slugify(title.value)}.pdf`;
    const file = new File([blob], filename, { type: 'application/pdf' });
    emit('attach', file);
    emit('close');
  } catch (e) {
    error.value = 'No se pudo adjuntar el documento.';
  } finally {
    loading.value = false;
  }
}

function onClose() {
  emit('close');
}

function resetState() {
  title.value = '';
  markdown.value = '';
  includePortada.value = true;
  includeSubportada.value = true;
  includeContraportada.value = true;
  revokePreview();
  previewSnapshot.value = null;
  error.value = '';
}

watch(() => props.open, (isOpen) => {
  if (!isOpen) resetState();
});

onBeforeUnmount(revokePreview);
</script>
