/**
 * Centralized tooltip texts for the admin panel.
 *
 * All help-icon tooltip strings live here so they are easy to find, edit,
 * and eventually migrate to the i18n system if the panel gets translated.
 *
 * Usage:
 *   const { analytics, dashboard, proposalEdit } = useTooltipTexts()
 */

const analytics = {
  engagementScore:
    'Puntuación de 0 a 100 basada en frecuencia de visitas, tiempo en secciones clave, IPs únicas y revisitas recientes. Mayor puntaje = mayor interés.',
  summary:
    'Métricas clave de engagement: vistas totales, sesiones, cobertura de secciones y tiempos. Resume la interacción completa del cliente con esta propuesta.',
  views:
    'Número total de veces que se abrió la propuesta, incluyendo recargas y visitas repetidas.',
  sessions:
    'Sesiones únicas de navegación. Cada vez que el cliente abre la propuesta en una nueva pestaña o después de un periodo de inactividad, cuenta como sesión separada.',
  firstView:
    'Fecha y hora en que el cliente abrió la propuesta por primera vez después de ser enviada.',
  readingTime:
    'Tiempo acumulado que el cliente pasó leyendo las secciones de la propuesta, sumando todas las sesiones.',
  coverage:
    'Porcentaje de secciones habilitadas que el cliente visitó al menos una vez. 100% significa que revisó toda la propuesta.',
  lastVisit:
    'Fecha y hora de la visita más reciente del cliente a la propuesta.',
  technicalDetail:
    'Métricas unificadas del contenido técnico: incluye la sección técnica y los paneles vistos en modo técnico.',
  viewModeComparison:
    'Desglose del engagement según el modo de vista elegido: ejecutivo (resumen), detallado (completo) o técnico (arquitectura).',
  globalComparison:
    'Compara las métricas de esta propuesta con el promedio de todas tus propuestas. Verde = mejor que el promedio.',
  funnel:
    'Porcentaje de sesiones que alcanzaron cada sección en orden. Un alto drop-off indica dónde los clientes pierden interés.',
  sharedLinks:
    'Cuando el cliente comparte la propuesta con otros stakeholders, cada enlace se trackea por separado mostrando quién lo abrió y cuántas veces.',
  devices:
    'Distribución de sesiones por tipo de dispositivo del cliente.',
  suggestedActions:
    'Recomendaciones automáticas basadas en el comportamiento del cliente para optimizar tu seguimiento comercial.',
  skippedSections:
    'Secciones habilitadas que el cliente nunca visitó — oportunidades para mencionar en el próximo contacto.',
  heatmap:
    'Secciones ordenadas por tiempo de lectura. Las más calientes son las que más le interesaron al cliente.',
  sectionEngagement:
    'Detalle del tiempo invertido en cada sección: visitas, tiempo total y promedio por visita.',
  activityTimeline:
    'Cronología de todos los eventos: envíos, vistas, cambios de estado, comentarios y acciones.',
  sessionHistory:
    'Últimas 50 sesiones con detalle de IP, secciones vistas, modo y duración.',
}

const dashboard = {
  conversionRate:
    'Porcentaje de propuestas aceptadas sobre el total cerradas (aceptadas + rechazadas). No incluye borradores ni en proceso.',
  revisitRate:
    'Porcentaje de clientes que volvieron a ver la propuesta al menos una segunda vez después de su primera visita.',
  avgTimeToFirstView:
    'Tiempo promedio entre el envío de la propuesta y la primera vez que el cliente la abre (en horas).',
  avgTimeToResponse:
    'Tiempo promedio entre el envío y la respuesta del cliente (aceptación o rechazo), en horas.',
  avgAcceptedValue:
    'Valor monetario promedio de las propuestas que fueron aceptadas por el cliente.',
  statusDistribution:
    'Cantidad de propuestas en cada estado del ciclo de vida: borrador, enviada, vista, aceptada, rechazada y expirada.',
  topRejectionReasons:
    'Los motivos de rechazo más frecuentes seleccionados al rechazar una propuesta.',
  monthlyTrend:
    'Volumen de propuestas creadas, enviadas, aceptadas y rechazadas en los últimos 6 meses para identificar tendencias.',
  avgValueByStatus:
    'Inversión promedio agrupada por estado actual. Útil para comparar el ticket de aceptadas vs rechazadas.',
  winRateByProjectType:
    'Porcentaje de aceptación por categoría de proyecto. Identifica qué tipos tienen mayor probabilidad de cierre.',
  winRateByMarketType:
    'Porcentaje de aceptación por industria o mercado del cliente. Ayuda a enfocar esfuerzos comerciales.',
  winRateByViewMode:
    'Correlación entre el modo de vista predominante del cliente y la probabilidad de aceptación.',
  bestCombination:
    'Combinaciones de tipo de proyecto y mercado con mayor tasa de aceptación histórica.',
  engagementVsValue:
    'Compara el valor promedio de cierre entre propuestas con alto engagement (score ≥ 70) y bajo. Mayor engagement suele correlacionar con mayor valor.',
  calculator:
    'Porcentaje de clientes que abrieron la calculadora de módulos pero no confirmaron su selección (abandono).',
  droppedModules:
    'Los módulos que los clientes más frecuentemente desmarcan en la calculadora de inversión.',
}

const proposalEdit = {
  activeStatus:
    'Cuando está inactiva, el cliente verá un mensaje de propuesta expirada al intentar acceder al enlace.',
  automations:
    'Pausa o activa los emails automáticos: recordatorio, urgencia e inactividad. Úsalo si estás en negociación directa.',
  hostingPercent:
    'Porcentaje de la inversión total que representa el plan de hosting anual. Se sincroniza con la sección «Tu inversión y cómo pagar».',
  expirationDate:
    'Después de esta fecha, la propuesta se marcará como expirada automáticamente y el cliente verá un aviso.',
  discount:
    'Porcentaje de descuento incluido en el email de urgencia. Se aplica automáticamente al cumplir los días configurados.',
  logActivity:
    'Registra manualmente llamadas, reuniones, seguimientos o notas vinculadas a esta propuesta. Aparecerán en el historial y en Analytics.',
  activityHistory:
    'Cronología de todas las acciones: envíos, cambios de estado, respuestas del cliente y actividades registradas manualmente.',
  sectionCompleteness:
    'Porcentaje de secciones comerciales habilitadas que ya tienen contenido. No incluye el detalle técnico (tiene pestaña propia).',
}

export const useTooltipTexts = () => ({ analytics, dashboard, proposalEdit })
