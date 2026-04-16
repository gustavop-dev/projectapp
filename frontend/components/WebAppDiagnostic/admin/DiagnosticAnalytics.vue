<template>
  <section class="space-y-4">
    <div v-if="loading" class="py-12 text-center text-sm text-gray-400">Cargando analítica…</div>
    <template v-else-if="data">
      <!-- KPIs -->
      <div class="grid sm:grid-cols-4 gap-3">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">Vistas totales</div>
          <div class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mt-1">{{ data.view_count }}</div>
          <div v-if="data.last_viewed_at" class="text-xs text-gray-400 mt-1">última {{ formatDate(data.last_viewed_at) }}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">Sesiones</div>
          <div class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mt-1">{{ data.total_sessions }}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">Tiempo total</div>
          <div class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mt-1">{{ formatDuration(data.total_time_spent_seconds) }}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">Respuesta</div>
          <div class="text-sm text-gray-700 dark:text-gray-200 mt-1">
            <span v-if="data.responded_at">{{ formatDate(data.responded_at) }}</span>
            <span v-else class="text-gray-400 italic">sin respuesta</span>
          </div>
        </div>
      </div>

      <!-- Heat map per section -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
        <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
          Tiempo por sección
        </div>
        <div v-if="!data.sections.length" class="text-sm text-gray-400 italic">
          Aún no hay eventos de lectura por sección.
        </div>
        <ol v-else class="space-y-2">
          <li
            v-for="row in sortedSections"
            :key="row.section_type"
            class="flex items-center gap-3"
          >
            <div class="w-40 shrink-0 text-sm text-gray-700 dark:text-gray-200 truncate">
              {{ row.section_title || row.section_type }}
            </div>
            <div class="flex-1 h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-emerald-500 rounded-full"
                :style="{ width: widthPct(row.total_seconds) + '%' }"
              ></div>
            </div>
            <div class="w-28 text-right text-xs text-gray-500 dark:text-gray-400 tabular-nums">
              {{ formatDuration(row.total_seconds) }} · {{ row.visits }} visita(s)
            </div>
          </li>
        </ol>
      </div>

      <!-- Lifecycle timestamps -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
        <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">Ciclo del diagnóstico</div>
        <dl class="grid sm:grid-cols-3 gap-4 text-sm">
          <div>
            <dt class="text-xs text-gray-400">Envío inicial</dt>
            <dd class="text-gray-700 dark:text-gray-200 mt-0.5">{{ data.initial_sent_at ? formatDate(data.initial_sent_at) : '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-400">Envío final</dt>
            <dd class="text-gray-700 dark:text-gray-200 mt-0.5">{{ data.final_sent_at ? formatDate(data.final_sent_at) : '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs text-gray-400">Respondido</dt>
            <dd class="text-gray-700 dark:text-gray-200 mt-0.5">{{ data.responded_at ? formatDate(data.responded_at) : '—' }}</dd>
          </div>
        </dl>
      </div>
    </template>
    <div v-else class="py-12 text-center text-sm text-rose-500">No se pudo cargar la analítica.</div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';

const props = defineProps({
  diagnosticId: { type: Number, required: true },
  loader: { type: Function, required: true },
});

const data = ref(null);
const loading = ref(true);

const sortedSections = computed(() => {
  const rows = data.value?.sections || [];
  return [...rows].sort((a, b) => (b.total_seconds || 0) - (a.total_seconds || 0));
});

const maxSeconds = computed(() => {
  const rows = data.value?.sections || [];
  return Math.max(1, ...rows.map((r) => r.total_seconds || 0));
});

function widthPct(seconds) {
  if (!seconds || maxSeconds.value === 0) return 0;
  return Math.round((seconds / maxSeconds.value) * 100);
}

const dateFormatter = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
function formatDate(iso) {
  if (!iso) return '';
  return dateFormatter.format(new Date(iso));
}

function formatDuration(sec) {
  const n = Number(sec) || 0;
  if (n < 60) return `${Math.round(n)}s`;
  const mins = Math.floor(n / 60);
  const rem = Math.round(n - mins * 60);
  return rem ? `${mins}m ${rem}s` : `${mins}m`;
}

async function refresh() {
  loading.value = true;
  try {
    const result = await props.loader();
    data.value = result?.data || null;
  } finally {
    loading.value = false;
  }
}

watch(() => props.diagnosticId, refresh);
onMounted(refresh);

defineExpose({ refresh });
</script>
