<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-8 text-gray-400 text-sm">
      Cargando analytics...
    </div>

    <!-- No data -->
    <div v-else-if="!analytics" class="text-center py-8 text-gray-400 text-sm">
      No hay datos de analytics disponibles.
    </div>

    <template v-else>
      <!-- CSV Export button -->
      <div class="flex justify-end">
        <button
          class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors shadow-sm"
          @click="downloadCSV"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Exportar CSV
        </button>
      </div>

      <!-- Engagement score -->
      <div v-if="analytics.engagement_score != null" class="bg-white rounded-xl border shadow-sm p-5 flex items-center gap-5"
        :class="analytics.engagement_score >= 70 ? 'border-emerald-200' : analytics.engagement_score >= 40 ? 'border-yellow-200' : 'border-red-200'">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-white"
          :class="analytics.engagement_score >= 70 ? 'bg-emerald-500' : analytics.engagement_score >= 40 ? 'bg-yellow-500' : 'bg-red-400'">
          {{ analytics.engagement_score }}
        </div>
        <div>
          <p class="text-sm font-semibold text-gray-900">Engagement Score</p>
          <p class="text-xs text-gray-500 mt-0.5">
            {{ analytics.engagement_score >= 70 ? 'Alto engagement — prioridad de follow-up' : analytics.engagement_score >= 40 ? 'Engagement moderado' : 'Bajo engagement — necesita atención' }}
          </p>
        </div>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p class="text-xs text-gray-400 uppercase tracking-wider">Vistas</p>
          <p class="text-2xl font-light text-gray-900 mt-1">{{ analytics.total_views }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p class="text-xs text-gray-400 uppercase tracking-wider">Sesiones</p>
          <p class="text-2xl font-light text-gray-900 mt-1">{{ analytics.unique_sessions }}</p>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p class="text-xs text-gray-400 uppercase tracking-wider">Primera vista</p>
          <p class="text-sm font-light text-gray-900 mt-1">
            {{ analytics.first_viewed_at ? formatDate(analytics.first_viewed_at) : '—' }}
          </p>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p class="text-xs text-gray-400 uppercase tracking-wider">Tiempo a 1ra vista</p>
          <p class="text-2xl font-light text-gray-900 mt-1">
            {{ analytics.time_to_first_view_hours != null ? analytics.time_to_first_view_hours + 'h' : '—' }}
          </p>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p class="text-xs text-gray-400 uppercase tracking-wider">Tiempo a respuesta</p>
          <p class="text-2xl font-light text-gray-900 mt-1">
            {{ analytics.time_to_response_hours != null ? analytics.time_to_response_hours + 'h' : '—' }}
          </p>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p class="text-xs text-gray-400 uppercase tracking-wider">Respondida</p>
          <p class="text-sm font-light text-gray-900 mt-1">
            {{ analytics.responded_at ? formatDate(analytics.responded_at) : '—' }}
          </p>
        </div>
      </div>

      <!-- Comparison badges (Feature 13) -->
      <div v-if="analytics.comparison" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Comparación con promedio global</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="flex items-center gap-3 p-3 rounded-lg" :class="comparisonClass('ttfv')">
            <div class="text-2xl">{{ comparisonEmoji('ttfv') }}</div>
            <div>
              <p class="text-xs text-gray-500">Tiempo a 1ra vista</p>
              <p class="text-sm font-medium">
                {{ analytics.time_to_first_view_hours != null ? analytics.time_to_first_view_hours + 'h' : '—' }}
                <span v-if="analytics.comparison.avg_time_to_first_view_hours != null" class="text-xs text-gray-400">
                  vs {{ analytics.comparison.avg_time_to_first_view_hours }}h avg
                </span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 p-3 rounded-lg" :class="comparisonClass('ttr')">
            <div class="text-2xl">{{ comparisonEmoji('ttr') }}</div>
            <div>
              <p class="text-xs text-gray-500">Tiempo a respuesta</p>
              <p class="text-sm font-medium">
                {{ analytics.time_to_response_hours != null ? analytics.time_to_response_hours + 'h' : '—' }}
                <span v-if="analytics.comparison.avg_time_to_response_hours != null" class="text-xs text-gray-400">
                  vs {{ analytics.comparison.avg_time_to_response_hours }}h avg
                </span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 p-3 rounded-lg" :class="comparisonClass('views')">
            <div class="text-2xl">{{ comparisonEmoji('views') }}</div>
            <div>
              <p class="text-xs text-gray-500">Total vistas</p>
              <p class="text-sm font-medium">
                {{ analytics.total_views }}
                <span v-if="analytics.comparison.avg_views != null" class="text-xs text-gray-400">
                  vs {{ analytics.comparison.avg_views }} avg
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Funnel visualization (Feature 13) -->
      <div v-if="analytics.funnel?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">Funnel de navegación</h3>
          <p class="text-xs text-gray-400 mt-0.5">Porcentaje de sesiones que alcanzaron cada sección</p>
        </div>
        <div class="px-4 sm:px-6 py-4 space-y-3">
          <div v-for="(step, idx) in analytics.funnel" :key="step.section_type" class="flex items-center gap-3">
            <span class="text-xs text-gray-400 w-5 text-right">{{ idx + 1 }}</span>
            <div class="flex-1">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm text-gray-700 font-medium truncate">{{ step.section_title }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-500">{{ step.reached_count }} sesiones</span>
                  <span v-if="step.drop_off_percent > 0" class="text-xs text-red-500 font-medium">
                    -{{ step.drop_off_percent }}%
                  </span>
                </div>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all"
                  :class="funnelBarColor(step.drop_off_percent)"
                  :style="{ width: funnelBarWidth(step) + '%' }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Share links (Feature 13) -->
      <div v-if="analytics.share_links?.length" class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">Enlaces compartidos</h3>
          <p class="text-xs text-gray-400 mt-0.5">Tracking de propuestas compartidas con otros stakeholders</p>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th class="px-4 sm:px-6 py-3">Compartido por</th>
                <th class="px-4 py-3">Destinatario</th>
                <th class="px-4 py-3 text-center">Vistas</th>
                <th class="px-4 sm:px-6 py-3">Primera vista</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="link in analytics.share_links" :key="link.uuid" class="hover:bg-gray-50/50">
                <td class="px-4 sm:px-6 py-3">
                  <span class="font-medium text-gray-900">{{ link.shared_by_name }}</span>
                  <span v-if="link.shared_by_email" class="text-xs text-gray-400 ml-1">({{ link.shared_by_email }})</span>
                </td>
                <td class="px-4 py-3">
                  <span v-if="link.recipient_name" class="text-gray-700">{{ link.recipient_name }}</span>
                  <span v-else class="text-gray-400 italic">Pendiente</span>
                  <span v-if="link.recipient_email" class="text-xs text-gray-400 ml-1">({{ link.recipient_email }})</span>
                </td>
                <td class="px-4 py-3 text-center text-gray-600">{{ link.view_count }}</td>
                <td class="px-4 sm:px-6 py-3 text-gray-600">{{ link.first_viewed_at ? formatDate(link.first_viewed_at) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Device breakdown -->
      <div v-if="hasDeviceData" class="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Dispositivos</h3>
        <div class="flex gap-6 text-sm">
          <div class="flex items-center gap-2">
            <span class="text-lg">🖥️</span>
            <span class="text-gray-600">Desktop: <strong>{{ analytics.device_breakdown.desktop }}</strong></span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-lg">📱</span>
            <span class="text-gray-600">Mobile: <strong>{{ analytics.device_breakdown.mobile }}</strong></span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-lg">📋</span>
            <span class="text-gray-600">Tablet: <strong>{{ analytics.device_breakdown.tablet }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Suggested actions -->
      <div v-if="suggestions.length" class="bg-amber-50 rounded-xl border border-amber-100 shadow-sm p-4">
        <h3 class="text-sm font-medium text-amber-900 mb-3">💡 Acciones sugeridas</h3>
        <ul class="space-y-2">
          <li
            v-for="(s, i) in suggestions"
            :key="i"
            class="flex items-start gap-2 text-sm text-amber-800"
          >
            <span class="mt-0.5 flex-shrink-0 text-amber-500">{{ s.icon }}</span>
            <span>{{ s.text }}</span>
          </li>
        </ul>
      </div>

      <!-- Skipped sections -->
      <div v-if="analytics.skipped_sections?.length" class="bg-red-50 rounded-xl border border-red-100 shadow-sm p-4">
        <h3 class="text-sm font-medium text-red-800 mb-2">⚠️ Secciones no visitadas</h3>
        <p class="text-xs text-red-600 mb-3">El cliente nunca visitó estas secciones — información accionable para follow-up.</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="s in analytics.skipped_sections"
            :key="s.section_type"
            class="inline-flex items-center px-3 py-1.5 bg-white border border-red-200 rounded-lg text-xs text-red-700 font-medium"
          >
            {{ s.section_title }}
          </span>
        </div>
      </div>

      <!-- Section time heatmap -->
      <div v-if="sortedSections.length" class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">🔥 Heatmap de Interés</h3>
          <p class="text-xs text-gray-400 mt-0.5">Secciones ordenadas por tiempo total — las más calientes son las que más le importan al cliente</p>
        </div>
        <div class="px-4 sm:px-6 py-4 space-y-3">
          <div v-for="(section, idx) in sortedSections" :key="section.section_type" class="flex items-center gap-3">
            <span class="text-base w-5 flex-shrink-0">{{ heatEmoji(idx, sortedSections.length) }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1 gap-2">
                <span class="text-sm font-medium text-gray-800 truncate">{{ section.section_title }}</span>
                <span class="text-xs text-gray-500 flex-shrink-0 tabular-nums">{{ formatTime(section.total_time_seconds) }}</span>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-2.5">
                <div
                  class="h-2.5 rounded-full transition-all"
                  :class="heatBarColor(idx, sortedSections.length)"
                  :style="{ width: heatBarWidth(section.total_time_seconds) + '%' }"
                />
              </div>
            </div>
          </div>
        </div>
        <!-- Actionable insights -->
        <div v-if="sectionInsights.length" class="px-4 sm:px-6 pb-4 space-y-2">
          <div
            v-for="insight in sectionInsights"
            :key="insight.type"
            class="flex items-start gap-2 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3"
          >
            <span class="text-base flex-shrink-0">{{ insight.icon }}</span>
            <div>
              <p class="text-xs font-semibold text-emerald-800">{{ insight.label }}</p>
              <p class="text-xs text-emerald-700 mt-0.5">{{ insight.text }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Section engagement table -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">Engagement por sección</h3>
          <p class="text-xs text-gray-400 mt-0.5">Tiempo que el cliente pasó en cada sección</p>
        </div>
        <div v-if="analytics.sections.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th class="px-4 sm:px-6 py-3">Sección</th>
                <th class="px-4 py-3 text-center">Visitas</th>
                <th class="px-4 py-3 text-right">Tiempo total</th>
                <th class="px-4 py-3 text-right">Promedio</th>
                <th class="px-4 sm:px-6 py-3">Engagement</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="section in analytics.sections" :key="section.section_type" class="hover:bg-gray-50/50">
                <td class="px-4 sm:px-6 py-3">
                  <span class="font-medium text-gray-900">{{ section.section_title }}</span>
                  <span class="text-xs text-gray-400 ml-1">({{ section.section_type }})</span>
                </td>
                <td class="px-4 py-3 text-center text-gray-600">{{ section.visit_count }}</td>
                <td class="px-4 py-3 text-right text-gray-600">{{ formatTime(section.total_time_seconds) }}</td>
                <td class="px-4 py-3 text-right text-gray-600">{{ formatTime(section.avg_time_seconds) }}</td>
                <td class="px-4 sm:px-6 py-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-gray-100 rounded-full h-2 max-w-[120px]">
                      <div
                        class="h-2 rounded-full transition-all"
                        :class="barColor(section.avg_time_seconds)"
                        :style="{ width: barWidth(section.avg_time_seconds) + '%' }"
                      />
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-6 py-8 text-center text-gray-400 text-sm">
          Aún no hay datos de engagement por sección.
        </div>
      </div>

      <!-- Activity Timeline -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">Historial de actividad</h3>
          <p class="text-xs text-gray-400 mt-0.5">Timeline cronológico de eventos de la propuesta</p>
        </div>
        <div v-if="analytics.timeline?.length" class="px-4 sm:px-6 py-4">
          <div class="relative">
            <div class="absolute left-4 top-0 bottom-0 w-px bg-gray-200"></div>
            <div v-for="(event, idx) in analytics.timeline" :key="idx" class="relative pl-10 pb-5 last:pb-0">
              <div class="absolute left-2.5 w-3 h-3 rounded-full border-2 border-white" :class="timelineColor(event.change_type)"></div>
              <div class="flex flex-wrap items-baseline gap-2">
                <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="timelineBadge(event.change_type)">
                  {{ timelineIcon(event.change_type) }} {{ event.change_type }}
                </span>
                <span class="text-xs text-gray-400">{{ formatDate(event.created_at) }}</span>
              </div>
              <p class="text-sm text-gray-600 mt-1">{{ event.description }}</p>
            </div>
          </div>
        </div>
        <div v-else class="px-6 py-8 text-center text-gray-400 text-sm">
          Aún no hay eventos registrados.
        </div>
      </div>

      <!-- Sessions history -->
      <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">Historial de sesiones</h3>
          <p class="text-xs text-gray-400 mt-0.5">Últimas 50 sesiones de navegación</p>
        </div>
        <div v-if="analytics.sessions.length" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wider">
                <th class="px-4 sm:px-6 py-3">Sesión</th>
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3 text-center">Secciones vistas</th>
                <th class="px-4 sm:px-6 py-3 text-right">Tiempo total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="session in analytics.sessions" :key="session.session_id" class="hover:bg-gray-50/50">
                <td class="px-4 sm:px-6 py-3">
                  <span class="font-mono text-xs text-gray-500">{{ session.session_id.slice(0, 12) }}...</span>
                  <span v-if="session.ip_address" class="text-xs text-gray-400 ml-2">{{ session.ip_address }}</span>
                </td>
                <td class="px-4 py-3 text-gray-600">{{ formatDate(session.viewed_at) }}</td>
                <td class="px-4 py-3 text-center text-gray-600">{{ session.sections_viewed }}</td>
                <td class="px-4 sm:px-6 py-3 text-right text-gray-600">{{ formatTime(session.total_time_seconds) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-6 py-8 text-center text-gray-400 text-sm">
          Aún no hay sesiones registradas.
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  proposalId: { type: [Number, String], required: true },
  proposal: { type: Object, default: null },
});

const proposalStore = useProposalStore();
const loading = ref(true);
const analytics = ref(null);

const suggestions = computed(() => {
  if (!analytics.value) return [];
  const list = [];
  const a = analytics.value;
  const status = props.proposal?.status;

  const skippedTypes = (a.skipped_sections || []).map(s => s.section_type);

  if (skippedTypes.includes('investment')) {
    list.push({ icon: '💰', text: 'El cliente no vio la sección de Inversión — envía un resumen de precios por email o menciónalo en el próximo contacto.' });
  }

  if (a.total_views >= 3 && !a.responded_at) {
    list.push({ icon: '🔥', text: `El cliente revisó la propuesta ${a.total_views} veces sin responder — es un señal de interés, haz un follow-up en caliente.` });
  }

  skippedTypes.filter(t => t !== 'investment').forEach(t => {
    const section = (a.skipped_sections || []).find(s => s.section_type === t);
    if (section) {
      list.push({ icon: '👁️', text: `El cliente no vio «${section.section_title}» — menciónala en el próximo contacto.` });
    }
  });

  if (a.time_to_first_view_hours != null && a.time_to_first_view_hours > 24) {
    list.push({ icon: '📬', text: `El cliente tardó ${a.time_to_first_view_hours}h en abrir la propuesta — verifica que el email llegó correctamente o considera reenviarla.` });
  }

  if (status === 'rejected') {
    list.push({ icon: '🔄', text: 'Propuesta rechazada — considera enviar una versión ajustada al presupuesto o un alcance reducido para retomar la negociación.' });
  }

  if (a.unique_sessions === 1 && !a.responded_at && status === 'viewed') {
    list.push({ icon: '📞', text: 'El cliente abrió la propuesta una sola vez — un seguimiento por llamada o WhatsApp puede aumentar la probabilidad de respuesta.' });
  }

  return list;
});

const hasDeviceData = computed(() => {
  const d = analytics.value?.device_breakdown;
  return d && (d.desktop || d.mobile || d.tablet);
});

const sortedSections = computed(() => {
  if (!analytics.value?.sections?.length) return [];
  return [...analytics.value.sections].sort(
    (a, b) => (b.total_time_seconds || 0) - (a.total_time_seconds || 0),
  );
});

const SECTION_INSIGHTS = {
  timeline: {
    icon: '⏱️',
    label: 'Preocupación: plazos de entrega',
    text: 'El cliente invirtió tiempo en el cronograma. En el follow-up, enfócate en la velocidad de ejecución y el primer entregable rápido.',
  },
  investment: {
    icon: '💰',
    label: 'Señal de interés en precio',
    text: 'Revisó en detalle la inversión. Ofrece opciones de pago o un desglose más claro del ROI para facilitar la decisión.',
  },
  functional_requirements: {
    icon: '📋',
    label: 'Duda sobre el alcance',
    text: 'Le costó entender qué incluye el proyecto. Clarifica las funcionalidades clave y lo que está fuera del alcance en la siguiente llamada.',
  },
  context_diagnostic: {
    icon: '🎯',
    label: 'El problema resonó',
    text: 'Se identificó con el diagnóstico. En el follow-up, refuerza el dolor que resuelves — ya tienes su atención.',
  },
  proposal_closing: {
    icon: '🤔',
    label: 'Evaluando la decisión final',
    text: 'Pasó tiempo en el cierre. Es un buen momento para contactarlo directamente y ofrecer resolver cualquier duda.',
  },
  about_us: {
    icon: '🔍',
    label: 'Investigando tu credibilidad',
    text: 'Quiere saber quién eres antes de decidir. Comparte casos de éxito o testimonios de clientes similares.',
  },
  portfolio: {
    icon: '🖼️',
    label: 'Revisó tu portafolio',
    text: 'Está validando la calidad de tu trabajo. Menciona proyectos similares en el follow-up.',
  },
};

const sectionInsights = computed(() => {
  if (!sortedSections.value.length) return [];
  const top = sortedSections.value.slice(0, 2);
  const insights = [];
  for (const sec of top) {
    const def = SECTION_INSIGHTS[sec.section_type];
    if (def && sec.total_time_seconds >= 10) {
      insights.push({ type: sec.section_type, ...def });
    }
  }
  return insights;
});

onMounted(async () => {
  loading.value = true;
  const result = await proposalStore.fetchProposalAnalytics(props.proposalId);
  if (result.success) {
    analytics.value = result.data;
  }
  loading.value = false;
});

function downloadCSV() {
  const url = `/api/proposals/${props.proposalId}/analytics/csv/`;
  window.open(url, '_blank');
}

function formatTime(seconds) {
  if (!seconds || seconds < 1) return '< 1s';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  return new Date(isoStr).toLocaleString('es-CO', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function barWidth(avgSeconds) {
  return Math.min(100, (avgSeconds / 180) * 100);
}

function barColor(avgSeconds) {
  if (avgSeconds >= 60) return 'bg-emerald-500';
  if (avgSeconds >= 20) return 'bg-blue-500';
  if (avgSeconds >= 5) return 'bg-amber-400';
  return 'bg-gray-300';
}

function heatBarWidth(totalSeconds) {
  if (!sortedSections.value.length) return 0;
  const max = sortedSections.value[0].total_time_seconds || 1;
  return Math.min(100, Math.round((totalSeconds / max) * 100));
}

function heatBarColor(idx, total) {
  const ratio = total <= 1 ? 1 : idx / (total - 1);
  if (ratio <= 0.15) return 'bg-red-500';
  if (ratio <= 0.35) return 'bg-orange-400';
  if (ratio <= 0.55) return 'bg-amber-400';
  if (ratio <= 0.75) return 'bg-yellow-300';
  return 'bg-gray-300';
}

function heatEmoji(idx, total) {
  const ratio = total <= 1 ? 1 : idx / (total - 1);
  if (ratio <= 0.15) return '🔴';
  if (ratio <= 0.35) return '🟠';
  if (ratio <= 0.55) return '🟡';
  return '⚪';
}

function timelineIcon(type) {
  const icons = {
    created: '📝', updated: '✏️', sent: '📧', viewed: '👁️',
    accepted: '✅', rejected: '❌', resent: '🔁', expired: '⏰', duplicated: '📋',
  };
  return icons[type] || '•';
}

function timelineColor(type) {
  const colors = {
    created: 'bg-blue-400', updated: 'bg-amber-400', sent: 'bg-indigo-400',
    viewed: 'bg-green-400', accepted: 'bg-emerald-500', rejected: 'bg-red-500',
    resent: 'bg-purple-400', expired: 'bg-yellow-500', duplicated: 'bg-gray-400',
  };
  return colors[type] || 'bg-gray-400';
}

function timelineBadge(type) {
  const badges = {
    created: 'bg-blue-50 text-blue-700', updated: 'bg-amber-50 text-amber-700',
    sent: 'bg-indigo-50 text-indigo-700', viewed: 'bg-green-50 text-green-700',
    accepted: 'bg-emerald-50 text-emerald-700', rejected: 'bg-red-50 text-red-700',
    resent: 'bg-purple-50 text-purple-700', expired: 'bg-yellow-50 text-yellow-700',
    duplicated: 'bg-gray-50 text-gray-700',
  };
  return badges[type] || 'bg-gray-50 text-gray-700';
}

function funnelBarWidth(step) {
  if (!analytics.value?.unique_sessions) return 0;
  return Math.round((step.reached_count / analytics.value.unique_sessions) * 100);
}

function funnelBarColor(dropOff) {
  if (dropOff <= 10) return 'bg-emerald-500';
  if (dropOff <= 30) return 'bg-blue-500';
  if (dropOff <= 50) return 'bg-amber-400';
  return 'bg-red-400';
}

function comparisonClass(metric) {
  const c = analytics.value?.comparison;
  if (!c) return 'bg-gray-50';
  if (metric === 'ttfv') {
    const val = analytics.value?.time_to_first_view_hours;
    const avg = c.avg_time_to_first_view_hours;
    if (val == null || avg == null) return 'bg-gray-50';
    return val < avg ? 'bg-emerald-50' : 'bg-amber-50';
  }
  if (metric === 'ttr') {
    const val = analytics.value?.time_to_response_hours;
    const avg = c.avg_time_to_response_hours;
    if (val == null || avg == null) return 'bg-gray-50';
    return val < avg ? 'bg-emerald-50' : 'bg-amber-50';
  }
  if (metric === 'views') {
    const val = analytics.value?.total_views;
    const avg = c.avg_views;
    if (val == null || avg == null) return 'bg-gray-50';
    return val > avg ? 'bg-emerald-50' : 'bg-amber-50';
  }
  return 'bg-gray-50';
}

function comparisonEmoji(metric) {
  const c = analytics.value?.comparison;
  if (!c) return '📊';
  if (metric === 'ttfv') {
    const val = analytics.value?.time_to_first_view_hours;
    const avg = c.avg_time_to_first_view_hours;
    if (val == null || avg == null) return '📊';
    return val < avg ? '🔥' : '🐢';
  }
  if (metric === 'ttr') {
    const val = analytics.value?.time_to_response_hours;
    const avg = c.avg_time_to_response_hours;
    if (val == null || avg == null) return '📊';
    return val < avg ? '⚡' : '⏳';
  }
  if (metric === 'views') {
    const val = analytics.value?.total_views;
    const avg = c.avg_views;
    if (val == null || avg == null) return '📊';
    return val > avg ? '👀' : '😴';
  }
  return '📊';
}
</script>
