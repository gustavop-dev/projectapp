<template>
  <div>
    <!-- Floating trigger button -->
    <button
      class="fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full bg-primary text-white shadow-lg
             hover:bg-primary-strong transition-all flex items-center justify-center text-lg font-bold
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
          <div class="absolute right-0 top-0 bottom-0 w-full max-w-md bg-surface shadow-2xl flex flex-col">
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-border-muted">
              <h2 class="text-lg font-bold text-text-default">Manual de Métricas</h2>
              <button class="p-1.5 rounded-lg hover:bg-gray-100 text-text-subtle" @click="isOpen = false">
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
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
              />
              <p v-if="search" class="text-[10px] text-text-subtle mt-1">{{ filteredMetrics.length }} resultado{{ filteredMetrics.length !== 1 ? 's' : '' }}</p>
            </div>

            <!-- Metrics list -->
            <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              <div
                v-for="metric in filteredMetrics"
                :key="metric.id"
                class="rounded-xl border border-border-muted p-4 hover:border-emerald-100 transition-colors"
              >
                <div class="flex items-start gap-3">
                  <span class="text-lg flex-shrink-0">{{ metric.icon }}</span>
                  <div class="min-w-0">
                    <h3 class="text-sm font-semibold text-text-default">{{ metric.name }}</h3>
                    <p class="text-xs text-text-muted mt-1 leading-relaxed">{{ metric.description }}</p>
                    <div class="mt-2 space-y-1">
                      <p class="text-[11px] text-text-subtle"><span class="font-medium text-text-muted">Cálculo:</span> {{ metric.calculation }}</p>
                      <p class="text-[11px] text-text-subtle"><span class="font-medium text-text-muted">Acción:</span> {{ metric.action }}</p>
                    </div>
                  </div>
                </div>
              </div>
              <p v-if="!filteredMetrics.length" class="text-center text-sm text-text-subtle py-8">
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
  {
    id: 'pipeline_value', icon: '💵', name: 'Valor del pipeline',
    description: 'Suma total de la inversión de todas las propuestas activas en estado enviada o vista. Representa el valor potencial de negocios en curso.',
    calculation: 'Suma de total_investment donde status=sent/viewed e is_active=true.',
    action: 'Monitorear para asegurar un pipeline saludable. Si baja, crear más propuestas o hacer follow-up a las existentes.',
  },
  {
    id: 'pct_revisit', icon: '🔁', name: 'Tasa de revisita',
    description: 'Porcentaje de propuestas vistas donde el cliente regresó a ver la propuesta más de una vez.',
    calculation: 'Propuestas con sesiones únicas > 1 / total propuestas vistas × 100.',
    action: 'Una tasa alta indica interés. Propuestas con revisitas son candidatas prioritarias para follow-up.',
  },
  {
    id: 'pct_viewed_within_24h', icon: '⚡', name: '% vistas dentro de 24h',
    description: 'Porcentaje de propuestas enviadas que fueron abiertas por el cliente dentro de las primeras 24 horas.',
    calculation: '(first_viewed_at - sent_at ≤ 24h) / total con ambos timestamps × 100.',
    action: 'Si es bajo, revisar el asunto del email, la hora de envío o el canal de comunicación.',
  },
  {
    id: 'top_dropoff_section', icon: '🚪', name: 'Top sección de abandono',
    description: 'Sección con el mayor porcentaje de abandono global (cross-portfolio). Indica dónde los clientes dejan de navegar con más frecuencia.',
    calculation: '(1 - sesiones que vieron la sección / total sesiones globales) × 100, por cada section_type.',
    action: 'Mejorar el contenido o reposicionar la sección problemática. Puede indicar contenido poco relevante o muy extenso.',
  },
  {
    id: 'win_rate_combination', icon: '🧩', name: 'Win rate combinación proyecto × mercado',
    description: 'Tasa de aceptación cruzando tipo de proyecto y tipo de mercado. Identifica las combinaciones más rentables.',
    calculation: 'aceptadas / terminales por cada par (project_type, market_type) con ≥2 propuestas terminales.',
    action: 'Enfocar esfuerzo comercial en las combinaciones con mayor win rate. Ajustar oferta donde se pierde más.',
  },
  {
    id: 'engagement_value_insight', icon: '📊', name: 'Engagement vs Valor de cierre',
    description: 'Compara el valor promedio de cierre entre propuestas aceptadas con alto engagement vs bajo engagement.',
    calculation: 'Promedio de total_investment para propuestas aceptadas con tiempo de engagement sobre/bajo la mediana.',
    action: 'Si hay gran diferencia, invertir en mejorar el engagement (contenido, interactividad) puede aumentar el ticket promedio.',
  },
  {
    id: 'top_dropped_modules', icon: '🧮', name: 'Módulos más descartados (calculadora)',
    description: 'Módulos que los clientes eliminan con más frecuencia al usar el calculador interactivo de inversión.',
    calculation: 'Conteo de módulos en el campo "deselected" de los ChangeLogs tipo calc_confirmed.',
    action: 'Revisar si esos módulos son percibidos como innecesarios o caros. Considerar hacerlos opcionales por defecto.',
  },
  {
    id: 'calc_abandonment_rate', icon: '🚫', name: 'Tasa de abandono calculadora',
    description: 'Porcentaje de clientes que abrieron el calculador interactivo pero no confirmaron su selección.',
    calculation: 'calc_abandoned / (calc_confirmed + calc_abandoned) × 100.',
    action: 'Si es >50%, simplificar la experiencia del calculador o reducir la cantidad de opciones.',
  },
  {
    id: 'monthly_trend', icon: '📅', name: 'Tendencia mensual',
    description: 'Evolución mensual de propuestas creadas, enviadas, aceptadas y rechazadas en los últimos 6 meses.',
    calculation: 'Conteo agrupado por mes (TruncMonth) de created_at, filtrado por status.',
    action: 'Detectar tendencias estacionales y medir el impacto de cambios en el proceso comercial.',
  },
  {
    id: 'avg_value_by_status', icon: '💲', name: 'Valor promedio por estado',
    description: 'Inversión promedio de las propuestas agrupadas por su estado actual (aceptadas, rechazadas, enviadas, etc.).',
    calculation: 'Promedio de total_investment por cada status.',
    action: 'Si las rechazadas tienen valor muy alto, puede haber un problema de pricing. Si las aceptadas son bajas, buscar subir el ticket.',
  },
  {
    id: 'top_rejection_reasons', icon: '❌', name: 'Top motivos de rechazo',
    description: 'Los motivos de rechazo más frecuentes reportados por los clientes al declinar una propuesta.',
    calculation: 'Conteo de rejection_reason agrupado, ordenado por frecuencia (top 10).',
    action: 'Abordar los motivos más comunes: si es precio, revisar estructura; si es timing, mejorar urgencia.',
  },
  {
    id: 'comparison', icon: '📐', name: 'Comparación con promedio global',
    description: 'Badges por propuesta que comparan sus métricas (tiempo a 1ra vista, tiempo a respuesta, vistas) contra el promedio de todas las propuestas.',
    calculation: 'Valores individuales vs promedios globales de time_to_first_view, time_to_response y total_views.',
    action: 'Propuestas por debajo del promedio en vistas necesitan más visibilidad. Por encima en tiempo indica lentitud.',
  },
  {
    id: 'share_links', icon: '🔗', name: 'Enlaces compartidos (stakeholders)',
    description: 'Tracking de cuando un cliente comparte la propuesta con otros miembros de su equipo. Cada enlace tiene su propio conteo de vistas.',
    calculation: 'ProposalShareLink por propuesta: compartido por, destinatario, vistas, primera vista.',
    action: 'Múltiples stakeholders viendo la propuesta es señal de decisión grupal. Preparar materiales para diferentes perfiles.',
  },
  {
    id: 'skipped_sections', icon: '⚠️', name: 'Secciones no visitadas',
    description: 'Secciones habilitadas de la propuesta que el cliente nunca visitó durante ninguna de sus sesiones.',
    calculation: 'Secciones con is_enabled=true que no tienen registros en ProposalSectionView.',
    action: 'Mencionar esas secciones en el follow-up. Si inversión no fue vista, enviar resumen de precios directamente.',
  },
  {
    id: 'post_expiration_visit', icon: '🔥🕰️', name: 'Visita post-expiración',
    description: 'Alerta cuando un cliente visita una propuesta que ya ha expirado. Indica interés renovado.',
    calculation: 'ProposalViewEvent registrado después de expires_at con status=expired.',
    action: 'Contactar inmediatamente — el cliente quiere retomar. Ofrecer extender la vigencia o crear nueva propuesta.',
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
