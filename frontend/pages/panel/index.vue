<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
      <h1 class="text-2xl font-light text-gray-900 dark:text-white">Dashboard</h1>
      <div class="flex flex-wrap items-center gap-3">
        <NuxtLink
          :to="localePath('/panel/proposals/defaults')"
          class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-colors
                 border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50
                 dark:border-gray-600 dark:bg-gray-800/80 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:bg-gray-800"
          title="Proposal defaults and email templates"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Proposal defaults
        </NuxtLink>
        <NuxtLink
          :to="localePath('/panel/proposals/create')"
          class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white shadow-sm transition-colors w-fit
                 bg-esmerald hover:bg-esmerald-dark dark:bg-lemon dark:text-esmerald-dark dark:hover:opacity-90"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          New proposal
        </NuxtLink>
      </div>
    </div>

    <!-- Quick access (matches sidebar sections) -->
    <div class="mb-8">
      <h2 class="mb-3 text-xs font-semibold uppercase tracking-widest text-green-light dark:text-green-light/80">
        Quick access
      </h2>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <NuxtLink
          v-for="card in quickAccessCards"
          :key="card.href"
          :to="card.href"
          class="group flex flex-col rounded-xl border border-gray-100 bg-white p-4 shadow-sm transition-colors
                 hover:border-esmerald/20 hover:bg-esmerald-light/30 dark:border-white/[0.06] dark:bg-white/[0.04] dark:hover:bg-white/[0.08]"
        >
          <span class="text-sm font-medium text-esmerald group-hover:text-esmerald-dark dark:text-white dark:group-hover:text-lemon">
            {{ card.label }}
          </span>
          <span class="mt-1 text-xs text-gray-500 dark:text-green-light/70">{{ card.hint }}</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="text-center py-20 text-gray-400 text-sm dark:text-green-light/50">
      Loading metrics…
    </div>

    <template v-else>
      <!-- Status overview pills -->
      <div class="flex flex-wrap gap-2 mb-6">
        <span
          v-for="(count, st) in (kpis?.by_status || {})"
          :key="st"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
          :class="pillClass(st)"
        >
          <span>{{ statusEmoji(st) }}</span>
          {{ statusLabel(st) }}: <strong>{{ count }}</strong>
        </span>
      </div>

      <!-- Pipeline Value card -->
      <div v-if="kpis?.pipeline_value != null" class="mb-4">
        <div class="bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-xl shadow-sm p-5 flex items-center justify-between">
          <div>
            <p class="text-xs text-emerald-600 dark:text-emerald-400 uppercase tracking-wider font-medium mb-1">Pipeline activo</p>
            <p class="text-3xl font-light text-emerald-700 dark:text-emerald-300">${{ Number(kpis.pipeline_value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) }}</p>
            <p class="text-xs text-emerald-500 dark:text-emerald-400/70 mt-1">{{ kpis.pipeline_count }} propuesta{{ kpis.pipeline_count !== 1 ? 's' : '' }} en curso (enviadas + vistas)</p>
          </div>
          <div class="text-5xl opacity-20">💰</div>
        </div>
      </div>

      <!-- Primary KPI cards -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <p class="text-xs text-gray-400 dark:text-green-light/60 uppercase tracking-wider leading-tight mb-1">Tasa de cierre</p>
          <p class="text-2xl font-light" :class="kpis?.conversion_rate >= 50 ? 'text-emerald-600' : 'text-gray-900 dark:text-white'">
            {{ kpis?.conversion_rate != null ? kpis.conversion_rate + '%' : '—' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">de propuestas terminales</p>
        </div>
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <p class="text-xs text-gray-400 dark:text-green-light/60 uppercase tracking-wider leading-tight mb-1">1ra apertura</p>
          <p class="text-2xl font-light text-gray-900 dark:text-white">
            {{ kpis?.avg_time_to_first_view_hours != null ? kpis.avg_time_to_first_view_hours + 'h' : '—' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">tiempo promedio</p>
        </div>
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <p class="text-xs text-gray-400 dark:text-green-light/60 uppercase tracking-wider leading-tight mb-1">A respuesta</p>
          <p class="text-2xl font-light text-gray-900 dark:text-white">
            {{ kpis?.avg_time_to_response_hours != null ? kpis.avg_time_to_response_hours + 'h' : '—' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">desde primera vista</p>
        </div>
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <p class="text-xs text-gray-400 dark:text-green-light/60 uppercase tracking-wider leading-tight mb-1">Abre en &lt;24h</p>
          <p class="text-2xl font-light" :class="kpis?.pct_viewed_within_24h >= 70 ? 'text-emerald-600' : 'text-gray-900 dark:text-white'">
            {{ kpis?.pct_viewed_within_24h != null ? kpis.pct_viewed_within_24h + '%' : '—' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">de los enviados</p>
        </div>
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <p class="text-xs text-gray-400 dark:text-green-light/60 uppercase tracking-wider leading-tight mb-1">Re-abre</p>
          <p class="text-2xl font-light" :class="kpis?.pct_revisit >= 30 ? 'text-emerald-600' : 'text-gray-900 dark:text-white'">
            {{ kpis?.pct_revisit != null ? kpis.pct_revisit + '%' : '—' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">vuelven a leer</p>
        </div>
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-4">
          <p class="text-xs text-gray-400 dark:text-green-light/60 uppercase tracking-wider leading-tight mb-1">Llega a Inversión</p>
          <p class="text-2xl font-light" :class="kpis?.pct_reaching_investment >= 60 ? 'text-emerald-600' : 'text-amber-500'">
            {{ kpis?.pct_reaching_investment != null ? kpis.pct_reaching_investment + '%' : '—' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">de los que leen</p>
        </div>
      </div>

      <!-- Discount comparison + Top drop-off row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <!-- Discount vs no-discount -->
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-5">
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-4">💸 Cierre con vs sin descuento</h3>
          <div class="flex items-end gap-6">
            <div class="flex-1 text-center">
              <div class="text-3xl font-light mb-1" :class="discountDelta > 0 ? 'text-emerald-600' : 'text-gray-900 dark:text-white'">
                {{ kpis?.discount_close_rate != null ? kpis.discount_close_rate + '%' : '—' }}
              </div>
              <p class="text-xs text-gray-500 dark:text-green-light/60">Con descuento</p>
              <p v-if="kpis?.discount_analysis" class="text-[10px] text-gray-400 dark:text-green-light/60 mt-0.5">n={{ kpis.discount_analysis.with_discount_count }}</p>
            </div>
            <div class="text-gray-200 dark:text-white/20 text-2xl font-light pb-4">vs</div>
            <div class="flex-1 text-center">
              <div class="text-3xl font-light mb-1 text-gray-900 dark:text-white">
                {{ kpis?.no_discount_close_rate != null ? kpis.no_discount_close_rate + '%' : '—' }}
              </div>
              <p class="text-xs text-gray-500 dark:text-green-light/60">Sin descuento</p>
              <p v-if="kpis?.discount_analysis" class="text-[10px] text-gray-400 dark:text-green-light/60 mt-0.5">n={{ kpis.discount_analysis.without_discount_count }}</p>
            </div>
          </div>
          <div v-if="discountDelta !== null" class="mt-3 text-center">
            <span
              class="inline-flex items-center gap-1 text-xs font-medium px-3 py-1 rounded-full"
              :class="discountDelta > 0 ? 'bg-emerald-50 text-emerald-700' : discountDelta < 0 ? 'bg-red-50 text-red-600' : 'bg-gray-100 text-gray-500'"
            >
              {{ discountDelta > 0 ? '▲' : discountDelta < 0 ? '▼' : '=' }}
              {{ Math.abs(discountDelta) }}pp {{ discountDelta > 0 ? 'más con descuento' : discountDelta < 0 ? 'menos con descuento' : 'igual' }}
            </span>
          </div>
          <div v-if="kpis?.discount_analysis?.avg_discount_percent" class="mt-3 text-center text-xs text-gray-500 dark:text-green-light/60">
            Descuento promedio: <strong>{{ kpis.discount_analysis.avg_discount_percent }}%</strong>
            <span v-if="kpis.discount_analysis.avg_discount_accepted"> · En aceptadas: <strong>{{ kpis.discount_analysis.avg_discount_accepted }}%</strong></span>
          </div>
          <div v-if="discountDelta !== null && discountDelta <= 0" class="mt-2 text-center">
            <span class="text-[10px] text-amber-600 font-medium">⚠️ El descuento no está mejorando el cierre — evalúa si estás regalando margen</span>
          </div>
        </div>

        <!-- Top drop-off section -->
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm p-5">
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-4">🚪 Sección con mayor abandono</h3>
          <div v-if="kpis?.top_dropoff_section" class="flex flex-col items-center justify-center h-20 text-center">
            <p class="text-base font-semibold text-gray-800 dark:text-white">{{ sectionLabel(kpis.top_dropoff_section.section_type) }}</p>
            <p class="text-3xl font-light text-red-500 mt-1">{{ kpis.top_dropoff_section.dropoff_percent }}%</p>
            <p class="text-xs text-gray-400 dark:text-green-light/60 mt-1">de sesiones no la visitan</p>
          </div>
          <div v-else class="flex items-center justify-center h-20 text-gray-400 dark:text-green-light/60 text-sm">
            Sin datos suficientes
          </div>
        </div>
      </div>

      <!-- Rejection reasons + Monthly trend row -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <!-- Top rejection reasons -->
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100 dark:border-white/[0.06]">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">❌ Motivos de rechazo</h3>
          </div>
          <div v-if="rejectionReasons.length" class="px-5 py-4 space-y-3">
            <div
              v-for="r in rejectionReasons"
              :key="r.rejection_reason"
              class="flex items-center gap-3"
            >
              <span class="text-xs text-gray-600 dark:text-green-light/60 w-28 flex-shrink-0 truncate">{{ rejectionLabel(r.rejection_reason) }}</span>
              <div class="flex-1 bg-gray-100 dark:bg-white/[0.06] rounded-full h-2">
                <div
                  class="h-2 bg-red-400 rounded-full transition-all"
                  :style="{ width: rejectionBarWidth(r.count) + '%' }"
                />
              </div>
              <span class="text-xs text-gray-500 dark:text-green-light/60 w-4 text-right flex-shrink-0">{{ r.count }}</span>
            </div>
          </div>
          <div v-else class="px-5 py-8 text-center text-gray-400 dark:text-green-light/60 text-sm">
            Sin rechazos registrados
          </div>
        </div>

        <!-- Monthly trend -->
        <div class="bg-white dark:bg-white/[0.04] rounded-xl border border-gray-100 dark:border-white/[0.06] shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-gray-100 dark:border-white/[0.06]">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">📈 Tendencia mensual</h3>
            <div class="flex items-center gap-3 mt-2">
              <span class="flex items-center gap-1 text-xs text-gray-400 dark:text-green-light/60"><span class="w-2.5 h-2.5 rounded-sm bg-blue-300 inline-block" /> Enviadas</span>
              <span class="flex items-center gap-1 text-xs text-gray-400 dark:text-green-light/60"><span class="w-2.5 h-2.5 rounded-sm bg-emerald-400 inline-block" /> Aceptadas</span>
              <span class="flex items-center gap-1 text-xs text-gray-400 dark:text-green-light/60"><span class="w-2.5 h-2.5 rounded-sm bg-red-300 inline-block" /> Rechazadas</span>
            </div>
          </div>
          <div v-if="monthlyTrend.length" class="px-5 py-4">
            <div class="flex items-end gap-2 h-24">
              <div
                v-for="row in monthlyTrend"
                :key="row.month"
                class="flex-1 flex flex-col items-center gap-0.5"
              >
                <div class="w-full flex flex-col justify-end gap-0.5" style="height: 72px;">
                  <div
                    class="w-full bg-emerald-400 rounded-t-sm min-h-[2px]"
                    :style="{ height: trendBarHeight(row.accepted, maxTrendValue) + 'px' }"
                    :title="`Aceptadas: ${row.accepted}`"
                  />
                  <div
                    class="w-full bg-red-300 min-h-[2px]"
                    :style="{ height: trendBarHeight(row.rejected, maxTrendValue) + 'px' }"
                    :title="`Rechazadas: ${row.rejected}`"
                  />
                  <div
                    class="w-full bg-blue-200 rounded-b-sm min-h-[2px]"
                    :style="{ height: trendBarHeight(row.sent - row.accepted - row.rejected, maxTrendValue) + 'px' }"
                    :title="`En curso: ${row.sent - row.accepted - row.rejected}`"
                  />
                </div>
                <span class="text-[10px] text-gray-400 dark:text-green-light/60">{{ formatMonth(row.month) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="px-5 py-8 text-center text-gray-400 dark:text-green-light/60 text-sm">
            Sin datos de tendencia
          </div>
        </div>
      </div>

      <!-- Recent proposals -->
      <div class="bg-white dark:bg-white/[0.04] rounded-xl shadow-sm border border-gray-100 dark:border-white/[0.06]">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-white/[0.06] flex items-center justify-between">
          <h2 class="text-sm font-medium text-gray-700 dark:text-white">Recent proposals</h2>
          <NuxtLink
            :to="localePath('/panel/proposals')"
            class="text-xs text-esmerald hover:text-esmerald-dark dark:text-lemon dark:hover:opacity-90"
          >
            View all →
          </NuxtLink>
        </div>
        <div v-if="recentProposals.length === 0" class="px-6 py-12 text-center text-gray-400 text-sm dark:text-green-light/60">
          No proposals yet. Create the first one.
        </div>
        <ul v-else class="divide-y divide-gray-50 dark:divide-white/[0.04]">
          <li
            v-for="p in recentProposals"
            :key="p.id"
          >
            <NuxtLink
              :to="localePath(`/panel/proposals/${p.id}/edit`)"
              class="block px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors cursor-pointer"
            >
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-emerald-600 transition-colors">
                  {{ p.title }}
                </span>
                <p class="text-xs text-gray-400 dark:text-green-light/60 mt-0.5">{{ p.client_name }}</p>
              </div>
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="pillClass(p.status)"
              >
                {{ statusLabel(p.status) }}
              </span>
            </NuxtLink>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getPanelNavSections } from '~/config/panelNav';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const proposalStore = useProposalStore();

/** Sidebar-aligned shortcuts for the dashboard (labels in English). */
const quickAccessCards = computed(() => {
  const sections = getPanelNavSections(localePath);
  const pick = (id, hint) => {
    const section = sections.find((s) => s.id === id);
    const first = section?.items?.[0];
    return first ? { label: section.label, href: first.href, hint } : null;
  };
  return [
    pick('overview', 'Home'),
    pick('commercial', 'Proposals and clients'),
    pick('site', 'Blog and portfolio'),
    pick('documents', 'Markdown → PDF'),
    pick('system', 'Admins and tools'),
  ].filter(Boolean);
});
const kpis = ref(null);
const loading = ref(true);

const recentProposals = computed(() => (proposalStore.proposals || []).slice(0, 5));

const rejectionReasons = computed(() => kpis.value?.top_rejection_reasons?.slice(0, 5) || []);
const monthlyTrend = computed(() => kpis.value?.monthly_trend || []);

const maxRejectionCount = computed(() => {
  if (!rejectionReasons.value.length) return 1;
  return Math.max(...rejectionReasons.value.map((r) => r.count), 1);
});

const maxTrendValue = computed(() => {
  if (!monthlyTrend.value.length) return 1;
  return Math.max(...monthlyTrend.value.map((r) => r.sent), 1);
});

const discountDelta = computed(() => {
  const d = kpis.value?.discount_close_rate;
  const n = kpis.value?.no_discount_close_rate;
  if (d == null || n == null) return null;
  return Math.round((d - n) * 10) / 10;
});

onMounted(async () => {
  await proposalStore.fetchProposals();
  const result = await proposalStore.fetchProposalDashboard();
  if (result.success) kpis.value = result.data;
  loading.value = false;
});

function rejectionBarWidth(count) {
  return Math.round((count / maxRejectionCount.value) * 100);
}

function trendBarHeight(value, max) {
  if (!value || value <= 0 || !max) return 2;
  return Math.max(2, Math.round((value / max) * 64));
}

function formatMonth(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('es-CO', { month: 'short' });
}

const STATUS_LABELS = {
  draft: 'Borrador', sent: 'Enviada', viewed: 'Vista',
  accepted: 'Aceptada', rejected: 'Rechazada', expired: 'Expirada',
};
const STATUS_EMOJIS = {
  draft: '📝', sent: '📤', viewed: '👁️',
  accepted: '✅', rejected: '❌', expired: '⏰',
};
const REJECTION_LABELS = {
  budget: 'Presupuesto', timeline: 'Plazos', competitor: 'Competidor',
  not_the_right_time: 'No es el momento', scope: 'Alcance',
  internal_decision: 'Decisión interna', other: 'Otro',
};
const SECTION_LABELS = {
  investment: 'Inversión', timeline: 'Cronograma',
  functional_requirements: 'Requerimientos', context_diagnostic: 'Diagnóstico',
  proposal_closing: 'Cierre', about_us: 'Nosotros',
  portfolio: 'Portafolio', greeting: 'Saludo',
  executive_summary: 'Resumen', next_steps: 'Próximos pasos',
};

function statusLabel(s) { return STATUS_LABELS[s] || s; }
function statusEmoji(s) { return STATUS_EMOJIS[s] || '•'; }
function rejectionLabel(r) { return REJECTION_LABELS[r] || r; }
function sectionLabel(s) { return SECTION_LABELS[s] || s; }

function pillClass(s) {
  const map = {
    draft: 'bg-gray-100 dark:bg-white/[0.06] text-gray-600 dark:text-green-light',
    sent: 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300',
    viewed: 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-300',
    accepted: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
    rejected: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-300',
    expired: 'bg-yellow-50 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-300',
  };
  return map[s] || 'bg-gray-100 dark:bg-white/[0.06] text-gray-600 dark:text-green-light';
}
</script>
