<template>
  <div>
    <!-- Floating trigger button -->
    <button
      class="fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full bg-emerald-600 text-white shadow-lg
             hover:bg-emerald-700 transition-all flex items-center justify-center text-lg font-bold
             hover:scale-105"
      @click="isOpen = true"
      title="Manual de métricas"
    >
      ?
    </button>

    <!-- Slide-over panel -->
    <Teleport to="body">
      <Transition name="manual-slide">
        <div v-if="isOpen" class="fixed inset-0 z-[9980]" @click.self="isOpen = false">
          <div class="absolute inset-0 bg-black/20 backdrop-blur-[2px]" @click="isOpen = false" />
          <div class="absolute right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl flex flex-col">
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 class="text-lg font-bold text-gray-900">Manual de Métricas</h2>
              <button class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400" @click="isOpen = false">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Search -->
            <div class="px-6 py-3 border-b border-gray-50">
              <input
                v-model="search"
                type="text"
                placeholder="Buscar métrica..."
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
              <p v-if="search" class="text-[10px] text-gray-400 mt-1">{{ filteredMetrics.length }} resultado{{ filteredMetrics.length !== 1 ? 's' : '' }}</p>
            </div>

            <!-- Metrics list -->
            <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              <div
                v-for="metric in filteredMetrics"
                :key="metric.id"
                class="rounded-xl border border-gray-100 p-4 hover:border-emerald-100 transition-colors"
              >
                <div class="flex items-start gap-3">
                  <span class="text-lg flex-shrink-0">{{ metric.icon }}</span>
                  <div class="min-w-0">
                    <h3 class="text-sm font-semibold text-gray-900">{{ metric.name }}</h3>
                    <p class="text-xs text-gray-500 mt-1 leading-relaxed">{{ metric.description }}</p>
                    <div class="mt-2 space-y-1">
                      <p class="text-[11px] text-gray-400"><span class="font-medium text-gray-500">Cálculo:</span> {{ metric.calculation }}</p>
                      <p class="text-[11px] text-gray-400"><span class="font-medium text-gray-500">Acción:</span> {{ metric.action }}</p>
                    </div>
                  </div>
                </div>
              </div>
              <p v-if="!filteredMetrics.length" class="text-center text-sm text-gray-400 py-8">
                No se encontraron métricas para "{{ search }}"
              </p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const isOpen = ref(false);
const search = ref('');

const metrics = [
  {
    id: 'conversion_rate', icon: '📈', name: 'Tasa de conversión',
    description: 'Porcentaje de propuestas aceptadas sobre el total de propuestas con resultado final (aceptadas + rechazadas + expiradas).',
    calculation: 'aceptadas / (aceptadas + rechazadas + expiradas) × 100',
    action: 'Si es baja, revisar pricing, contenido de propuestas o proceso de follow-up.',
  },
  {
    id: 'engagement_score', icon: '🎯', name: 'Engagement Score (0-100)',
    description: 'Score consolidado que mide qué tan comprometido está un prospecto con la propuesta.',
    calculation: 'Sesiones recientes (25pts) + Tiempo en inversión (25pts) + Stakeholders únicos (20pts) + Días sin respuesta inverso (15pts) + Revisitas (15pts).',
    action: 'Priorizar follow-up en propuestas con score >70. Score <30 indica desinterés.',
  },
  {
    id: 'heat_score', icon: '🔥', name: 'Heat Score (1-10)',
    description: 'Indicador rápido de "temperatura" de una propuesta en el listado. Versión simplificada del engagement score.',
    calculation: 'Sesiones recientes (3pts) + Tiempo inversión (2pts) + IPs únicas (2pts) + Vistas totales (2pts) + Recencia (1pt).',
    action: 'Propuestas con score 8-10 necesitan contacto inmediato. Score 1-3 pueden estar frías.',
  },
  {
    id: 'time_to_first_view', icon: '⏱️', name: 'Tiempo a primera vista',
    description: 'Horas entre el envío de la propuesta y la primera vez que el cliente la abre.',
    calculation: 'first_viewed_at - sent_at (en horas).',
    action: 'Si es >48h, considerar re-enviar o contactar por WhatsApp. El promedio saludable es <24h.',
  },
  {
    id: 'time_to_response', icon: '⏳', name: 'Tiempo a respuesta',
    description: 'Horas entre la primera vista del cliente y su decisión (aceptar o rechazar).',
    calculation: 'responded_at - first_viewed_at (en horas).',
    action: 'Si es >72h y el cliente revisó varias veces, hacer follow-up proactivo.',
  },
  {
    id: 'win_rate_project', icon: '🏆', name: 'Win rate por tipo de proyecto',
    description: 'Tasa de aceptación segmentada por tipo de proyecto (Sitio Web, E-commerce, App Web, etc.).',
    calculation: 'aceptadas / (aceptadas + rechazadas + expiradas) por cada project_type.',
    action: 'Concentrar esfuerzo comercial en los tipos con mayor win rate. Ajustar pricing donde se pierde más.',
  },
  {
    id: 'win_rate_market', icon: '🎯', name: 'Win rate por tipo de mercado',
    description: 'Tasa de aceptación segmentada por tipo de mercado (B2B, B2C, SaaS, Retail, etc.).',
    calculation: 'aceptadas / (aceptadas + rechazadas + expiradas) por cada market_type.',
    action: 'Identificar nichos más rentables y enfocar contenido de propuestas.',
  },
  {
    id: 'funnel', icon: '🔽', name: 'Funnel de engagement',
    description: 'Visualización de cuántas sesiones llegan a cada sección de la propuesta, en orden.',
    calculation: 'Sesiones que visitaron cada sección / total de sesiones únicas.',
    action: 'Si hay un drop-off alto en una sección específica, mejorar su contenido o posición.',
  },
  {
    id: 'heatmap', icon: '🗺️', name: 'Heatmap de tiempo por sección',
    description: 'Tiempo total acumulado que todos los visitantes dedicaron a cada sección.',
    calculation: 'Suma de time_spent_seconds por section_type agrupado.',
    action: 'Las secciones con más tiempo son las que más interesan. Usarlo para personalizar follow-up.',
  },
  {
    id: 'device_breakdown', icon: '📱', name: 'Dispositivos',
    description: 'Desglose de sesiones por tipo de dispositivo (desktop, mobile, tablet).',
    calculation: 'Análisis de user_agent de cada ProposalViewEvent.',
    action: 'Si la mayoría usa mobile, asegurar que la propuesta se vea bien en móvil.',
  },
  {
    id: 'zombie', icon: '💀', name: 'Propuestas zombie',
    description: 'Propuestas enviadas hace >7 días, sin ninguna vista del cliente y sin actividad del vendedor.',
    calculation: 'status=sent, sent_at >7d, view_count=0, sin ChangeLogs de actividad.',
    action: 'Re-enviar, contactar por otro canal, o archivar si no hay respuesta.',
  },
  {
    id: 'seller_inactive', icon: '🏷️', name: 'Inactividad del vendedor',
    description: 'Propuestas vistas por el cliente pero sin follow-up del vendedor en >3 días.',
    calculation: 'status=sent/viewed, first_viewed_at existe, sin ChangeLogs recientes de tipo call/meeting/followup/note.',
    action: 'El vendedor debe hacer follow-up inmediato. Esta es la causa #1 de propuestas perdidas.',
  },
  {
    id: 'late_return', icon: '🔄', name: 'Regreso tardío',
    description: 'Cliente que no visitó la propuesta por ≥5 días y volvió en las últimas 24 horas.',
    calculation: 'Gap entre las 2 sesiones más recientes ≥5 días, última sesión <24h.',
    action: 'Contactar inmediatamente — el cliente probablemente comparó con competidores y regresó.',
  },
  {
    id: 'days_inactive', icon: '🔴', name: 'Días sin actividad (badge)',
    description: 'Badge rojo en la tabla cuando una propuesta sent/viewed no tiene actividad del vendedor en >3 días.',
    calculation: 'Diferencia entre ahora y last_activity_at (o sent_at/created_at como fallback).',
    action: 'Hacer follow-up inmediato para evitar que la propuesta se enfríe.',
  },
  {
    id: 'discount_close_rate', icon: '💰', name: 'Tasa de cierre con/sin descuento',
    description: 'Compara la tasa de aceptación entre propuestas con descuento vs sin descuento.',
    calculation: 'aceptadas/terminales para discount_percent>0 vs discount_percent=0.',
    action: 'Si no hay diferencia significativa, los descuentos no están ayudando a cerrar.',
  },
  {
    id: 'pct_reaching_investment', icon: '💎', name: '% que llega a Inversión',
    description: 'Porcentaje de propuestas vistas donde el cliente llegó a la sección de inversión.',
    calculation: 'Propuestas con section_views de tipo "investment" / total propuestas vistas.',
    action: 'Si es bajo, el contenido anterior no está reteniendo. Si es alto pero no cierran, revisar pricing.',
  },
];

const filteredMetrics = computed(() => {
  if (!search.value.trim()) return metrics;
  const q = search.value.trim().toLowerCase();
  return metrics.filter(m =>
    m.name.toLowerCase().includes(q) ||
    m.description.toLowerCase().includes(q) ||
    m.calculation.toLowerCase().includes(q) ||
    m.action.toLowerCase().includes(q)
  );
});
</script>

<style scoped>
.manual-slide-enter-active {
  transition: all 0.3s ease;
}
.manual-slide-leave-active {
  transition: all 0.2s ease;
}
.manual-slide-enter-from,
.manual-slide-leave-to {
  opacity: 0;
}
.manual-slide-enter-from > div:last-child,
.manual-slide-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
