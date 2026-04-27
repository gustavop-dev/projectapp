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
          class="inline-flex items-center gap-2 px-4 py-2 bg-surface border border-border-default dark:border-white/[0.08] rounded-xl text-sm text-text-muted hover:bg-surface-raised transition-colors shadow-sm"
          @click="downloadCSV"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Exportar CSV
        </button>
      </div>

      <!-- Engagement score -->
      <details
        v-if="analytics.engagement_score != null"
        open
        class="group bg-surface rounded-xl border shadow-sm"
        :class="analytics.engagement_score >= 70 ? 'border-emerald-200' : analytics.engagement_score >= 40 ? 'border-yellow-200' : 'border-red-200'"
      >
        <summary class="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-default">
          <div class="flex items-center gap-1.5">
            <h3 class="text-sm font-medium text-text-default">Engagement Score</h3>
            <BaseTooltip position="right" width="max-w-2xl">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
              </template>
              {{ tt.engagementScore }}
            </BaseTooltip>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="p-5 flex items-center gap-5">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-white"
            :class="analytics.engagement_score >= 70 ? 'bg-emerald-500' : analytics.engagement_score >= 40 ? 'bg-yellow-500' : 'bg-red-400'">
            {{ analytics.engagement_score }}
          </div>
          <p class="text-xs text-text-muted">
            {{ analytics.engagement_score >= 70 ? 'Alto engagement — prioridad de follow-up' : analytics.engagement_score >= 40 ? 'Engagement moderado' : 'Bajo engagement — necesita atención' }}
          </p>
        </div>
      </details>

      <!-- Summary cards -->
      <details open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div class="flex items-center gap-1.5">
            <h3 class="text-sm font-medium text-text-default">Resumen general</h3>
            <BaseTooltip position="right" width="max-w-2xl">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
              </template>
              {{ tt.summary }}
            </BaseTooltip>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-4 p-4">
          <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4">
            <div class="flex items-center gap-1">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Vistas</p>
              <BaseTooltip position="bottom" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-text-muted transition-colors" />
                </template>
                {{ tt.views }}
              </BaseTooltip>
            </div>
            <p class="text-2xl font-light text-text-default mt-1">{{ analytics.total_views }}</p>
          </div>
          <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4">
            <div class="flex items-center gap-1">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Sesiones</p>
              <BaseTooltip position="bottom" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-text-muted transition-colors" />
                </template>
                {{ tt.sessions }}
              </BaseTooltip>
            </div>
            <p class="text-2xl font-light text-text-default mt-1">{{ analytics.unique_sessions }}</p>
          </div>
          <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4">
            <div class="flex items-center gap-1">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Primera vista</p>
              <BaseTooltip position="bottom" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-text-muted transition-colors" />
                </template>
                {{ tt.firstView }}
              </BaseTooltip>
            </div>
            <p class="text-sm font-light text-text-default mt-1">
              {{ analytics.first_viewed_at ? formatDate(analytics.first_viewed_at) : '—' }}
            </p>
          </div>
          <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4">
            <div class="flex items-center gap-1">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Tiempo de lectura</p>
              <BaseTooltip position="bottom" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-text-muted transition-colors" />
                </template>
                {{ tt.readingTime }}
              </BaseTooltip>
            </div>
            <p class="text-2xl font-light text-text-default mt-1">{{ formatTime(totalReadingTime) }}</p>
          </div>
          <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4">
            <div class="flex items-center gap-1">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Cobertura</p>
              <BaseTooltip position="bottom" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-text-muted transition-colors" />
                </template>
                {{ tt.coverage }}
              </BaseTooltip>
            </div>
            <p class="text-2xl font-light mt-1"
              :class="sectionCoverage == null ? 'text-text-default' : sectionCoverage >= 80 ? 'text-text-brand' : sectionCoverage >= 50 ? 'text-amber-500 dark:text-amber-400' : 'text-red-500 dark:text-red-400'">
              {{ sectionCoverage != null ? sectionCoverage + '%' : '—' }}
            </p>
          </div>
          <div class="bg-surface rounded-xl border border-border-muted shadow-sm p-4">
            <div class="flex items-center gap-1">
              <p class="text-xs text-gray-400 uppercase tracking-wider">Última visita</p>
              <BaseTooltip position="bottom" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-3.5 h-3.5 text-gray-300 hover:text-text-muted transition-colors" />
                </template>
                {{ tt.lastVisit }}
              </BaseTooltip>
            </div>
            <p class="text-sm font-light text-text-default mt-1">
              {{ lastVisitedAt ? formatDate(lastVisitedAt) : '—' }}
            </p>
          </div>
        </div>
      </details>

      <!-- Comparison with global average -->
      <details v-if="analytics.comparison" open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div class="flex items-center gap-1.5">
            <h3 class="text-sm font-medium text-text-default">Comparación con promedio global</h3>
            <BaseTooltip position="right" width="max-w-2xl">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
              </template>
              {{ tt.globalComparison }}
            </BaseTooltip>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4">
          <div class="flex items-center gap-3 p-3 rounded-lg" :class="comparisonClass('ttfv')">
            <div class="text-2xl">{{ comparisonEmoji('ttfv') }}</div>
            <div>
              <p class="text-xs text-text-muted">Tiempo a 1ra vista</p>
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
              <p class="text-xs text-text-muted">Tiempo a respuesta</p>
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
              <p class="text-xs text-text-muted">Total vistas</p>
              <p class="text-sm font-medium">
                {{ analytics.total_views }}
                <span v-if="analytics.comparison.avg_views != null" class="text-xs text-gray-400">
                  vs {{ analytics.comparison.avg_views }} avg
                </span>
              </p>
            </div>
          </div>
        </div>
      </details>

      <!-- Funnel visualization -->
      <details v-if="analytics.funnel?.length" open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div>
            <div class="flex items-center gap-1.5">
              <h3 class="text-sm font-medium text-text-default">Funnel de navegación</h3>
              <BaseTooltip position="right" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.funnel }}
              </BaseTooltip>
            </div>
            <p class="text-xs text-text-subtle mt-0.5">Porcentaje de sesiones que alcanzaron cada sección</p>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="px-4 sm:px-6 py-4 space-y-3">
          <div v-for="(step, idx) in analytics.funnel" :key="step.section_type" class="flex items-center gap-3">
            <span class="text-xs text-text-subtle w-5 text-right">{{ idx + 1 }}</span>
            <div class="flex-1">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm text-text-default font-medium truncate">{{ step.section_title }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-text-muted">{{ step.reached_count }} sesiones</span>
                  <span v-if="step.drop_off_percent > 0" class="text-xs text-red-500 font-medium">
                    -{{ step.drop_off_percent }}%
                  </span>
                </div>
              </div>
              <div class="w-full bg-surface-raised rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all"
                  :class="funnelBarColor(step.drop_off_percent)"
                  :style="{ width: funnelBarWidth(step) + '%' }"
                />
              </div>
            </div>
          </div>
        </div>
      </details>

      <!-- Device breakdown -->
      <details v-if="hasDeviceData" open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div class="flex items-center gap-1.5">
            <h3 class="text-sm font-medium text-text-default">Dispositivos</h3>
            <BaseTooltip position="right" width="max-w-2xl">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
              </template>
              {{ tt.devices }}
            </BaseTooltip>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="flex gap-6 text-sm p-4">
          <div class="flex items-center gap-2">
            <span class="text-lg">🖥️</span>
            <span class="text-text-muted">Desktop: <strong>{{ analytics.device_breakdown.desktop }}</strong></span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-lg">📱</span>
            <span class="text-text-muted">Mobile: <strong>{{ analytics.device_breakdown.mobile }}</strong></span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-lg">📋</span>
            <span class="text-text-muted">Tablet: <strong>{{ analytics.device_breakdown.tablet }}</strong></span>
          </div>
        </div>
      </details>

      <!-- Suggested actions -->
      <details v-if="suggestions.length" class="group bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-100 dark:border-amber-900/40 shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-amber-100 dark:border-amber-900/40">
          <div class="flex items-center gap-1.5">
            <h3 class="text-sm font-medium text-amber-900 dark:text-amber-200">💡 Acciones sugeridas</h3>
            <BaseTooltip position="right" width="max-w-2xl">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-4 h-4 text-amber-400 hover:text-amber-600 transition-colors" />
              </template>
              {{ tt.suggestedActions }}
            </BaseTooltip>
          </div>
          <svg class="w-4 h-4 text-amber-600 dark:text-amber-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <ul class="space-y-2 p-4">
          <li
            v-for="(s, i) in suggestions"
            :key="i"
            class="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-200"
          >
            <span class="mt-0.5 flex-shrink-0 text-amber-500">{{ s.icon }}</span>
            <span>{{ s.text }}</span>
          </li>
        </ul>
      </details>

      <!-- Skipped sections -->
      <details v-if="analytics.skipped_sections?.length" class="group bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-100 dark:border-red-900/40 shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-red-100 dark:border-red-900/40">
          <div class="flex items-center gap-1.5">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-300">⚠️ Secciones no visitadas</h3>
            <BaseTooltip position="right" width="max-w-2xl">
              <template #trigger>
                <QuestionMarkCircleIcon class="w-4 h-4 text-red-400 hover:text-red-600 transition-colors" />
              </template>
              {{ tt.skippedSections }}
            </BaseTooltip>
          </div>
          <svg class="w-4 h-4 text-red-500 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="p-4">
          <p class="text-xs text-red-600 dark:text-red-300 mb-3">El cliente nunca visitó estas secciones — información accionable para follow-up.</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="s in analytics.skipped_sections"
              :key="s.section_type"
              class="inline-flex items-center px-3 py-1.5 bg-surface border border-red-200 dark:border-red-900/50 rounded-lg text-xs text-red-700 dark:text-red-300 font-medium"
            >
              {{ s.section_title }}
            </span>
          </div>
        </div>
      </details>

      <!-- Section time heatmap -->
      <details v-if="sortedSections.length" open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div>
            <div class="flex items-center gap-1.5">
              <h3 class="text-sm font-medium text-text-default">🔥 Heatmap de Interés</h3>
              <BaseTooltip position="right" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.heatmap }}
              </BaseTooltip>
            </div>
            <p class="text-xs text-gray-400 mt-0.5">Secciones ordenadas por tiempo total — las más calientes son las que más le importan al cliente</p>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div class="px-4 sm:px-6 py-4 space-y-3">
          <div v-for="(section, idx) in sortedSections" :key="section.section_type" class="flex items-center gap-3">
            <span class="text-base w-5 flex-shrink-0">{{ heatEmoji(idx, sortedSections.length) }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1 gap-2">
                <span class="text-sm font-medium text-text-default truncate">{{ section.section_title }}</span>
                <span class="text-xs text-text-muted flex-shrink-0 tabular-nums">{{ formatTime(section.total_time_seconds) }}</span>
              </div>
              <div class="w-full bg-surface-raised rounded-full h-2.5">
                <div
                  class="h-2.5 rounded-full transition-all"
                  :class="heatBarColor(idx, sortedSections.length)"
                  :style="{ width: heatBarWidth(section.total_time_seconds) + '%' }"
                />
              </div>
            </div>
          </div>
        </div>
        <div v-if="sectionInsights.length" class="px-4 sm:px-6 pb-4 space-y-2">
          <div
            v-for="insight in sectionInsights"
            :key="insight.type"
            class="flex items-start gap-2 bg-primary-soft border border-emerald-100 dark:border-emerald-900/40 rounded-xl px-4 py-3"
          >
            <span class="text-base flex-shrink-0">{{ insight.icon }}</span>
            <div>
              <p class="text-xs font-semibold text-emerald-800 dark:text-emerald-300">{{ insight.label }}</p>
              <p class="text-xs text-text-brand mt-0.5">{{ insight.text }}</p>
            </div>
          </div>
        </div>
      </details>

      <!-- Section engagement table -->
      <details open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div>
            <div class="flex items-center gap-1.5">
              <h3 class="text-sm font-medium text-text-default">Engagement por sección</h3>
              <BaseTooltip position="right" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.sectionEngagement }}
              </BaseTooltip>
            </div>
            <p class="text-xs text-gray-400 mt-0.5">Tiempo que el cliente pasó en cada sección</p>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div v-if="analytics.sections.length" class="overflow-x-auto rounded-b-xl overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                <th class="px-4 sm:px-6 py-3">Sección</th>
                <th class="px-4 py-3 text-center">Visitas</th>
                <th class="px-4 py-3 text-right">Tiempo total</th>
                <th class="px-4 py-3 text-right">Promedio</th>
                <th class="px-4 sm:px-6 py-3">Engagement</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
              <tr v-for="section in analytics.sections" :key="section.section_type" class="hover:bg-gray-50/50 dark:hover:bg-gray-700/50">
                <td class="px-4 sm:px-6 py-3">
                  <span class="font-medium text-text-default">{{ section.section_title }}</span>
                </td>
                <td class="px-4 py-3 text-center text-text-muted">{{ section.visit_count }}</td>
                <td class="px-4 py-3 text-right text-text-muted">{{ formatTime(section.total_time_seconds) }}</td>
                <td class="px-4 py-3 text-right text-text-muted">{{ formatTime(section.avg_time_seconds) }}</td>
                <td class="px-4 sm:px-6 py-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 bg-surface-raised rounded-full h-2 max-w-[120px]">
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
      </details>

      <!-- Activity Timeline -->
      <details open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div>
            <div class="flex items-center gap-1.5">
              <h3 class="text-sm font-medium text-text-default">Historial de actividad</h3>
              <BaseTooltip position="right" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.activityTimeline }}
              </BaseTooltip>
            </div>
            <p class="text-xs text-gray-400 mt-0.5">Timeline cronológico de eventos del diagnóstico</p>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div v-if="analytics.timeline?.length" class="px-4 sm:px-6 py-4">
          <div class="relative">
            <div class="absolute left-4 top-0 bottom-0 w-px bg-border-default"></div>
            <div v-for="(event, idx) in analytics.timeline" :key="idx" class="relative pl-10 pb-5 last:pb-0">
              <div class="absolute left-2.5 w-3 h-3 rounded-full border-2 border-surface" :class="timelineColor(event.change_type)"></div>
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="timelineBadge(event.change_type)">
                  {{ timelineIcon(event.change_type) }} {{ timelineLabel(event.change_type) }}
                </span>
                <span class="text-[10px] font-medium px-1.5 py-0.5 rounded-full" :class="actorBadgeClass(event.actor_type)">
                  {{ actorLabel(event.actor_type) }}
                </span>
                <span class="text-xs text-gray-400">{{ formatDate(event.created_at) }}</span>
              </div>
              <!-- eslint-disable-next-line vue/no-v-html -->
              <div class="text-sm text-text-muted mt-1" v-html="formatTimelineDescription(event)"></div>
            </div>
          </div>
        </div>
        <div v-else class="px-6 py-8 text-center text-gray-400 text-sm">
          Aún no hay eventos registrados.
        </div>
      </details>

      <!-- Sessions history -->
      <details open class="group bg-surface rounded-xl border border-border-muted shadow-sm">
        <summary class="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden border-b border-border-muted">
          <div>
            <div class="flex items-center gap-1.5">
              <h3 class="text-sm font-medium text-text-default">Historial de sesiones</h3>
              <BaseTooltip position="right" width="max-w-2xl">
                <template #trigger>
                  <QuestionMarkCircleIcon class="w-4 h-4 text-gray-400 hover:text-text-muted dark:text-text-muted dark:hover:text-gray-300 transition-colors" />
                </template>
                {{ tt.sessionHistory }}
              </BaseTooltip>
            </div>
            <p class="text-xs text-gray-400 mt-0.5">Últimas 50 sesiones de navegación</p>
          </div>
          <svg class="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div v-if="analytics.sessions.length" class="overflow-x-auto rounded-b-xl overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-surface-raised text-left text-xs text-text-muted uppercase tracking-wider">
                <th class="px-4 sm:px-6 py-3">Sesión</th>
                <th class="px-4 py-3">Fecha</th>
                <th class="px-4 py-3 text-center">Secciones vistas</th>
                <th class="px-4 sm:px-6 py-3 text-right">Tiempo total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
              <tr v-for="session in analytics.sessions" :key="session.session_id" class="hover:bg-gray-50/50 dark:hover:bg-gray-700/50">
                <td class="px-4 sm:px-6 py-3">
                  <span class="font-mono text-xs text-text-muted">{{ (session.session_id || '').slice(0, 12) }}...</span>
                  <span v-if="session.ip_address" class="text-xs text-gray-400 ml-2">{{ session.ip_address }}</span>
                </td>
                <td class="px-4 py-3 text-text-muted">{{ formatDate(session.viewed_at) }}</td>
                <td class="px-4 py-3 text-center text-text-muted">{{ session.sections_viewed }}</td>
                <td class="px-4 sm:px-6 py-3 text-right text-text-muted">{{ formatTime(session.total_time_seconds) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-6 py-8 text-center text-gray-400 text-sm">
          Aún no hay sesiones registradas.
        </div>
      </details>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/outline';

const { analytics: tt } = useTooltipTexts();

const props = defineProps({
  diagnosticId: { type: [Number, String], required: true },
  loader: { type: Function, required: true },
  diagnostic: { type: Object, default: null },
});

const loading = ref(true);
const analytics = ref(null);

const hasDeviceData = computed(() => {
  const d = analytics.value?.device_breakdown;
  return d && (d.desktop || d.mobile || d.tablet);
});

const lastVisitedAt = computed(() => {
  const data = analytics.value;
  if (!data) return null;
  return data.last_viewed_at || data.sessions?.[0]?.viewed_at || data.first_viewed_at || null;
});

const totalReadingTime = computed(() => {
  const sections = analytics.value?.sections;
  if (!sections?.length) return 0;
  return sections.reduce((sum, s) => sum + (s.total_time_seconds || 0), 0);
});

const sectionCoverage = computed(() => {
  const visited = analytics.value?.sections?.length || 0;
  const skipped = analytics.value?.skipped_sections?.length || 0;
  const total = visited + skipped;
  if (total === 0) return null;
  return Math.round((visited / total) * 100);
});

const sortedSections = computed(() => {
  if (!analytics.value?.sections?.length) return [];
  return [...analytics.value.sections].sort(
    (a, b) => (b.total_time_seconds || 0) - (a.total_time_seconds || 0),
  );
});

const SECTION_INSIGHTS = {
  cost: {
    icon: '💰',
    label: 'Interés en el costo',
    text: 'Revisó en detalle la inversión del diagnóstico. Refuerza el ROI y opciones de pago en el seguimiento.',
  },
  scope: {
    icon: '📋',
    label: 'Duda sobre el alcance',
    text: 'Pasó tiempo en alcance y consideraciones. Clarifica los entregables y límites antes de la siguiente llamada.',
  },
  timeline: {
    icon: '⏱️',
    label: 'Preocupación por plazos',
    text: 'Invirtió tiempo en el cronograma. En el follow-up, enfócate en velocidad de ejecución y el primer entregable.',
  },
  purpose: {
    icon: '🎯',
    label: 'Entiende la severidad',
    text: 'Leyó con atención el propósito y la escala de severidad. Ya tienes su atención sobre el dolor a resolver.',
  },
  radiography: {
    icon: '🩻',
    label: 'Reconoció su radiografía',
    text: 'Pasó tiempo revisando la radiografía de su aplicación. Úsala como ancla en el próximo contacto.',
  },
  categories: {
    icon: '🗂️',
    label: 'Revisó categorías evaluadas',
    text: 'Examinó las categorías evaluadas. Prepárate para profundizar en las que más le interesaron.',
  },
  executive_summary: {
    icon: '📑',
    label: 'Leyó el resumen ejecutivo',
    text: 'Se detuvo en el resumen ejecutivo — probablemente lo compartirá con otros stakeholders. Prepara material de apoyo.',
  },
  delivery_structure: {
    icon: '🏗️',
    label: 'Evalúa la estructura de entrega',
    text: 'Pasó tiempo en la estructura de entrega. Ofrece una llamada para alinear ritmo y puntos de control.',
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

const suggestions = computed(() => {
  if (!analytics.value) return [];
  const list = [];
  const a = analytics.value;
  const status = props.diagnostic?.status;

  const skippedTypes = (a.skipped_sections || []).map((s) => s.section_type);

  if (skippedTypes.includes('cost')) {
    list.push({
      icon: '💰',
      text: 'El cliente no vio la sección de Costo y formas de pago — envía un resumen por email o menciónalo en el próximo contacto.',
    });
  }

  if (skippedTypes.includes('scope')) {
    list.push({
      icon: '📋',
      text: 'No revisó Alcance y consideraciones — confirma expectativas antes de avanzar para evitar malentendidos.',
    });
  }

  if (a.total_views >= 3 && !a.responded_at) {
    list.push({
      icon: '🔥',
      text: `El cliente revisó el diagnóstico ${a.total_views} veces sin responder — señal de interés, haz un follow-up en caliente.`,
    });
  }

  skippedTypes
    .filter((t) => !['cost', 'scope'].includes(t))
    .forEach((t) => {
      const section = (a.skipped_sections || []).find((s) => s.section_type === t);
      if (section) {
        list.push({
          icon: '👁️',
          text: `El cliente no vio «${section.section_title}» — menciónala en el próximo contacto.`,
        });
      }
    });

  if (a.time_to_first_view_hours != null && a.time_to_first_view_hours > 24) {
    list.push({
      icon: '📬',
      text: `El cliente tardó ${a.time_to_first_view_hours}h en abrir el diagnóstico — verifica que el email llegó o considera reenviarlo.`,
    });
  }

  if (status === 'rejected') {
    list.push({
      icon: '🔄',
      text: 'Diagnóstico rechazado — considera ajustar alcance o presupuesto para retomar la negociación.',
    });
  }

  if (a.unique_sessions === 1 && !a.responded_at && status === 'sent') {
    list.push({
      icon: '📞',
      text: 'El cliente abrió el diagnóstico una sola vez — un seguimiento por llamada o WhatsApp puede aumentar la probabilidad de respuesta.',
    });
  }

  return list;
});

async function refresh() {
  loading.value = true;
  try {
    const result = await props.loader();
    analytics.value = result?.success ? result.data : (result?.data || null);
  } finally {
    loading.value = false;
  }
}

watch(() => props.diagnosticId, refresh);
onMounted(refresh);

defineExpose({ refresh });

function downloadCSV() {
  const url = `/api/diagnostics/${props.diagnosticId}/analytics/csv/`;
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
    day: 'numeric', month: 'long', year: 'numeric',
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

const TIMELINE_LABELS = {
  created: 'Creado',
  updated: 'Actualizado',
  section_updated: 'Sección actualizada',
  sent: 'Enviado',
  viewed: 'Visto',
  negotiating: 'Negociando',
  accepted: 'Aceptado',
  rejected: 'Rechazado',
  finished: 'Finalizado',
  email_sent: 'Email enviado',
  note: 'Nota',
  call: 'Llamada',
  meeting: 'Reunión',
  followup: 'Seguimiento',
  status_change: 'Cambio de estado',
};

const ACTOR_LABELS = { client: 'Cliente', seller: 'Ventas', system: 'Sistema', '': 'Sistema' };
const ACTOR_BADGE_CLASSES = {
  client: 'bg-blue-50 text-blue-600 border border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700',
  seller: 'bg-purple-50 text-purple-600 border border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700',
  system: 'bg-surface-raised text-text-muted border border-border-default',
  '': 'bg-surface-raised text-text-muted border border-border-default',
};

const FIELD_LABELS = {
  title: 'Título',
  client_name: 'Nombre del cliente',
  client_email: 'Email del cliente',
  client_phone: 'Teléfono del cliente',
  client_company: 'Empresa del cliente',
  status: 'Estado',
  language: 'Idioma',
  default_currency: 'Moneda',
  default_investment_amount: 'Inversión',
};

function timelineLabel(type) { return TIMELINE_LABELS[type] || type; }

function actorLabel(actorType) { return ACTOR_LABELS[actorType || ''] || 'Sistema'; }

function actorBadgeClass(actorType) {
  return ACTOR_BADGE_CLASSES[actorType || ''] || ACTOR_BADGE_CLASSES[''];
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatTimelineDescription(event) {
  const desc = event.description || '';

  if (event.change_type === 'updated' && event.field_name) {
    const fieldLabel = FIELD_LABELS[event.field_name] || event.field_name;
    const oldDisplay = escapeHtml(event.old_value || '(vacío)');
    const newDisplay = `<strong>${escapeHtml(event.new_value || '(vacío)')}</strong>`;
    return `<strong>${escapeHtml(fieldLabel)}</strong>: ${oldDisplay} → ${newDisplay}`;
  }

  if (event.change_type === 'status_change' && event.old_value && event.new_value) {
    return `<strong>Estado</strong>: ${escapeHtml(event.old_value)} → <strong>${escapeHtml(event.new_value)}</strong>`;
  }

  return escapeHtml(desc);
}

function timelineIcon(type) {
  const icons = {
    created: '📝', updated: '✏️', section_updated: '🧩',
    sent: '📧', viewed: '👁️', negotiating: '🤝',
    accepted: '✅', rejected: '❌', finished: '🏁',
    email_sent: '📨', note: '📝', call: '📞',
    meeting: '🤝', followup: '📩', status_change: '🔄',
  };
  return icons[type] || '•';
}

function timelineColor(type) {
  const colors = {
    created: 'bg-blue-400', updated: 'bg-amber-400', section_updated: 'bg-amber-400',
    sent: 'bg-indigo-400', viewed: 'bg-green-400', negotiating: 'bg-indigo-400',
    accepted: 'bg-emerald-500', rejected: 'bg-red-500', finished: 'bg-emerald-500',
    email_sent: 'bg-indigo-400', note: 'bg-gray-400', call: 'bg-sky-400',
    meeting: 'bg-indigo-500', followup: 'bg-amber-400', status_change: 'bg-blue-400',
  };
  return colors[type] || 'bg-gray-400';
}

function timelineBadge(type) {
  const badges = {
    created: 'bg-blue-50 text-blue-700',
    updated: 'bg-amber-50 text-amber-700',
    section_updated: 'bg-amber-50 text-amber-700',
    sent: 'bg-indigo-50 text-indigo-700',
    viewed: 'bg-green-50 text-green-700',
    negotiating: 'bg-indigo-50 text-indigo-700',
    accepted: 'bg-primary-soft text-text-brand',
    rejected: 'bg-red-50 text-red-700',
    finished: 'bg-primary-soft text-text-brand',
    email_sent: 'bg-indigo-50 text-indigo-700',
    note: 'bg-gray-50 text-text-muted',
    call: 'bg-sky-50 text-sky-700',
    meeting: 'bg-indigo-50 text-indigo-700',
    followup: 'bg-amber-50 text-amber-700',
    status_change: 'bg-blue-50 text-blue-700',
  };
  return badges[type] || 'bg-gray-50 text-text-default';
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
  if (!c) return 'bg-surface-raised';
  if (metric === 'ttfv') {
    const val = analytics.value?.time_to_first_view_hours;
    const avg = c.avg_time_to_first_view_hours;
    if (val == null || avg == null) return 'bg-surface-raised';
    return val < avg ? 'bg-primary-soft' : 'bg-amber-50 dark:bg-amber-900/20';
  }
  if (metric === 'ttr') {
    const val = analytics.value?.time_to_response_hours;
    const avg = c.avg_time_to_response_hours;
    if (val == null || avg == null) return 'bg-surface-raised';
    return val < avg ? 'bg-primary-soft' : 'bg-amber-50 dark:bg-amber-900/20';
  }
  if (metric === 'views') {
    const val = analytics.value?.total_views;
    const avg = c.avg_views;
    if (val == null || avg == null) return 'bg-surface-raised';
    return val > avg ? 'bg-primary-soft' : 'bg-amber-50 dark:bg-amber-900/20';
  }
  return 'bg-surface-raised';
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
