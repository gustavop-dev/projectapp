<template>
  <section class="bg-white dark:bg-esmerald border border-gray-100 dark:border-white/[0.06] rounded-xl p-5">
    <div class="flex items-center gap-2 mb-4">
      <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="text-sm font-semibold text-gray-800 dark:text-white">Plantillas para diagnóstico</h3>
    </div>
    <p class="text-xs text-gray-500 dark:text-green-light/60 mb-4">
      Copia o descarga estos documentos base para preparar el diagnóstico con el cliente.
    </p>

    <div v-if="loading" class="text-xs text-gray-400 dark:text-green-light/40">Cargando plantillas…</div>
    <div v-else-if="error" class="text-xs text-red-500">{{ error }}</div>
    <ul v-else class="divide-y divide-gray-100 dark:divide-white/[0.06]">
      <li v-for="t in templates" :key="t.slug" class="py-3">
        <div class="flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="text-sm font-medium text-gray-800 dark:text-white">{{ t.title }}</div>
            <div class="text-xs text-gray-400 dark:text-green-light/40 mt-0.5">
              {{ t.filename }} · {{ formatBytes(t.size_bytes) }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" :disabled="busy[t.slug]"
              @click="copyTemplate(t.slug)"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors disabled:opacity-50">
              {{ copied[t.slug] ? '¡Copiado!' : 'Copiar contenido' }}
            </button>
            <button type="button" :disabled="busy[t.slug]"
              @click="downloadTemplate(t.slug, t.filename)"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 dark:bg-white/[0.03] text-gray-600 dark:text-green-light rounded-lg text-xs font-medium hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors disabled:opacity-50">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Descargar .md
            </button>
            <button type="button" @click="togglePreview(t.slug)"
              class="text-xs text-gray-500 dark:text-green-light/60 hover:text-emerald-600">
              {{ expanded[t.slug] ? 'Ocultar' : 'Vista previa' }}
            </button>
          </div>
        </div>
        <pre v-if="expanded[t.slug] && cache[t.slug]"
          class="mt-3 p-3 bg-gray-50 dark:bg-white/[0.02] border border-gray-100 dark:border-white/[0.06] rounded-lg text-xs text-gray-700 dark:text-green-light overflow-auto max-h-96 whitespace-pre-wrap font-mono">{{ cache[t.slug] }}</pre>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { get_request } from '~/stores/services/request_http';

const templates = ref([]);
const loading = ref(true);
const error = ref('');
const cache = reactive({});
const expanded = reactive({});
const copied = reactive({});
const busy = reactive({});

onMounted(async () => {
  try {
    const res = await get_request('diagnostic-templates/');
    templates.value = res.data || [];
  } catch (e) {
    error.value = 'No se pudieron cargar las plantillas.';
  } finally {
    loading.value = false;
  }
});

async function ensureContent(slug) {
  if (cache[slug]) return cache[slug];
  busy[slug] = true;
  try {
    const res = await get_request(`diagnostic-templates/${slug}/`);
    cache[slug] = res.data?.content_markdown || '';
    return cache[slug];
  } finally {
    busy[slug] = false;
  }
}

async function copyTemplate(slug) {
  const content = await ensureContent(slug);
  await navigator.clipboard.writeText(content);
  copied[slug] = true;
  setTimeout(() => { copied[slug] = false; }, 2000);
}

async function downloadTemplate(slug, filename) {
  const content = await ensureContent(slug);
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function togglePreview(slug) {
  if (!expanded[slug]) await ensureContent(slug);
  expanded[slug] = !expanded[slug];
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
</script>
