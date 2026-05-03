<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="visible"
        class="calc-modal-root fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6"
        :data-theme="isDark ? 'dark' : 'light'"
      >
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')" />
        <div class="calc-modal-panel relative bg-surface rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col border border-border-default">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-border-default bg-primary">
            <div>
              <h3 class="text-xl font-bold text-accent">{{ t.title }}</h3>
              <p class="text-sm text-accent/70 mt-1">{{ t.subtitle }}</p>
            </div>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-accent/60 hover:text-accent hover:bg-surface/10 transition-colors"
              :aria-label="t.close"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto px-6 py-6 flex-1">
            <!-- Informational badge -->
            <div class="mb-5 flex items-start gap-3 bg-primary-soft border-l-4 border-primary rounded-2xl px-5 py-4 shadow-sm">
              <div
                class="w-9 h-9 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center text-base flex-shrink-0"
                aria-hidden="true"
              >
                💡
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-[13px] sm:text-sm text-text-brand leading-relaxed font-medium">
                  {{ t.optionalItemsBadge }}
                </p>
                <button
                  type="button"
                  class="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/25 text-[12px] font-semibold text-text-brand hover:bg-primary/20 transition-colors"
                  @click="$emit('navigateToRequirements')"
                >
                  <span aria-hidden="true">📋</span>
                  {{ t.viewRequirements }}
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            <template v-for="(group, gKey) in groupedModules" :key="gKey">
              <div class="mb-1 mt-4 first:mt-0">
                <h4 class="text-xs font-semibold text-text-subtle uppercase tracking-wider px-1">{{ group.label }}</h4>
              </div>
              <div class="space-y-2 mb-4">
                <div
                  v-for="mod in group.items"
                  :key="mod.id"
                  class="rounded-xl border transition-all"
                  :class="[
                    mod.selected
                      ? 'bg-primary-soft border-border-default'
                      : 'bg-surface-muted border-border-default',
                    mod._locked ? 'opacity-80' : 'cursor-pointer hover:border-border-muted'
                  ]"
                  @click="toggleModule(mod)"
                >
                  <div class="flex items-center justify-between p-4">
                    <div class="flex items-center gap-3 flex-1 min-w-0">
                      <div
                        class="w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all duration-200 flex-shrink-0"
                        :class="mod.selected
                          ? 'bg-primary border-primary text-accent scale-110'
                          : 'border-input-border bg-surface scale-100'"
                      >
                        <svg v-if="mod.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div class="min-w-0">
                        <span class="font-medium" :class="mod.selected ? 'text-text-brand' : 'text-text-muted'">
                          {{ mod.name }}
                        </span>
                        <span v-if="mod._locked" class="ml-2 text-[10px] text-text-subtle font-medium uppercase">{{ t.required }}</span>
                        <p v-if="!mod.selected && !mod._locked && !mod.is_invite" class="text-[11px] text-danger-strong leading-snug mt-0.5">
                          ⚠ {{ impactMessage(mod) }}
                        </p>
                      </div>
                    </div>
                    <span v-if="mod.is_invite" class="text-[11px] font-semibold text-text-brand flex-shrink-0">
                      {{ t.scheduleCall }}
                    </span>
                    <span v-else class="font-bold text-sm flex-shrink-0" :class="mod.selected ? 'text-text-brand' : 'text-text-subtle'">
                      {{ mod.price ? (mod._source === 'calculator_module' && mod.selected ? '+' : '') + formatPrice(mod.price) : t.included }}
                    </span>
                    <!-- Micro-feedback badge -->
                    <Transition name="micro-feedback">
                      <span
                        v-if="priceFeedback[mod.id]"
                        class="ml-2 text-xs font-bold flex-shrink-0 whitespace-nowrap"
                        :class="priceFeedback[mod.id].startsWith('+') ? 'text-success-strong' : 'text-danger-strong'"
                      >
                        {{ priceFeedback[mod.id] }}
                      </span>
                    </Transition>
                  </div>
                  <!-- Invite creative note -->
                  <div v-if="mod.is_invite" class="px-4 pb-4 -mt-1">
                    <div class="bg-primary-soft border border-border-default rounded-lg px-3 py-2.5">
                      <p class="text-[11px] text-text-brand leading-relaxed">
                        {{ mod.invite_note || t.inviteNote }}
                      </p>
                    </div>
                  </div>
                  <!-- Detail toggle for calculator modules -->
                  <div v-if="mod._source === 'calculator_module' && (mod.description || mod.detailItems?.length)" class="px-4 pb-3 -mt-1">
                    <button
                      type="button"
                      class="text-[11px] font-semibold text-text-muted hover:text-text-brand transition-colors flex items-center gap-1"
                      @click.stop="toggleDetail(mod.id)"
                    >
                      {{ expandedModules.has(mod.id) ? t.hideDetail : t.viewDetail }}
                      <svg class="w-3 h-3 transition-transform" :class="expandedModules.has(mod.id) ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    <Transition name="detail-slide">
                      <div v-if="expandedModules.has(mod.id)" class="mt-2 bg-surface-muted border border-border-default rounded-lg px-3 py-2.5 space-y-2">
                        <p v-if="mod.description" class="text-[11px] text-text-muted leading-relaxed">
                          {{ mod.description }}
                        </p>
                        <ul v-if="mod.detailItems?.length" class="space-y-1.5">
                          <li v-for="(item, idx) in mod.detailItems" :key="idx" class="flex items-start gap-2">
                            <span class="text-xs flex-shrink-0">{{ item.icon || '•' }}</span>
                            <div class="min-w-0">
                              <span class="text-[11px] font-medium text-text-default">{{ item.name }}</span>
                              <span v-if="item.description" class="text-[11px] text-text-subtle ml-1">— {{ item.description }}</span>
                            </div>
                          </li>
                        </ul>
                      </div>
                    </Transition>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- Footer with total -->
          <div class="px-6 py-5 border-t border-border-default bg-surface-muted">
            <!-- Discount badge -->
            <Transition appear name="discount-chip">
              <div
                v-if="hasActiveDiscount"
                class="discount-chip mb-3 flex w-fit items-center gap-2 bg-primary-soft border border-primary/30 rounded-full pl-1.5 pr-3 py-1.5"
                role="status"
                aria-live="polite"
              >
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary text-accent text-[11px] font-bold leading-none">
                  <span aria-hidden="true">🔥</span>
                  {{ props.discountPercent }}% OFF
                </span>
                <span class="text-[12px] font-semibold text-text-brand">{{ t.discountApplied }}</span>
              </div>
            </Transition>
            <div class="flex items-center justify-between mb-4">
              <div>
                <span class="text-sm text-text-subtle">{{ t.selectedModules }}</span>
                <span class="ml-1 text-sm font-medium text-text-brand">{{ selectedCount }}/{{ localModules.length }}</span>
              </div>
              <div class="text-right">
                <span class="text-sm text-text-subtle block">{{ t.estimatedTotal }}</span>
                <span class="text-2xl font-bold text-text-brand transition-transform tabular-nums" :class="{ 'total-pulse': totalPulsing }">{{ formatPrice(animatedTotal) }}</span>
                <span class="text-xs text-text-subtle ml-1">{{ currency }}</span>
              </div>
            </div>
            <!-- Dynamic timeline -->
            <div v-if="baseWeeks > 0" class="flex items-center justify-between mb-4 px-3 py-2.5 rounded-xl" :class="timelineChanged ? 'bg-primary-soft border border-border-default' : 'bg-surface-raised'">
              <div class="flex items-center gap-2">
                <span class="text-sm">⏱</span>
                <span class="text-sm text-text-muted">{{ t.estimatedDuration }}</span>
              </div>
              <div class="text-right">
                <span class="text-lg font-bold" :class="timelineChanged ? 'text-text-brand' : 'text-text-brand'">{{ dynamicWeeks }} {{ t.weeks }}</span>
                <span v-if="timelineChanged" class="block text-[11px] text-text-brand font-medium">
                  {{ dynamicWeeks > baseWeeks ? t.extendedFrom : t.reducedFrom }} {{ baseWeeks }} {{ t.to }} {{ dynamicWeeks }} {{ t.weeks }}
                </span>
              </div>
            </div>
            <button
              class="w-full py-3 bg-primary text-accent rounded-xl font-bold text-sm hover:bg-primary-strong transition-colors shadow-md"
              @click="confirmSelection"
            >
              {{ t.confirm }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useAnimatedNumber } from '~/composables/useAnimatedNumber';
import { create_request } from '~/stores/services/request_http';
import { useProposalDarkMode } from '~/composables/useProposalDarkMode';

const { isDark } = useProposalDarkMode();

function isPreviewMode() {
  return typeof window !== 'undefined'
    && new URLSearchParams(window.location.search).get('preview') === '1';
}

const props = defineProps({
  visible: { type: Boolean, default: false },
  modules: { type: Array, default: () => [] },
  currency: { type: String, default: 'COP' },
  proposalUuid: { type: String, default: '' },
  language: { type: String, default: 'es' },
  totalInvestment: { type: String, default: '' },
  baseWeeks: { type: Number, default: 0 },
  sentAt: { type: String, default: '' },
  discountPercent: { type: Number, default: 0 },
  discountedInvestment: { type: String, default: '' },
  selectedIds: { type: Array, default: () => [] },
});

const hasActiveDiscount = computed(() => {
  return props.discountPercent > 0 && props.discountedInvestment;
});

function parseInvestment(str) {
  if (!str) return 0;
  const cleaned = String(str).replace(/[^\d]/g, '');
  return parseInt(cleaned, 10) || 0;
}

const emit = defineEmits(['close', 'update:selection', 'navigateToRequirements', 'updateCalculatorModules', 'selectionConfirmed']);

const hasInteracted = ref(false);
const confirmed = ref(false);
const openedAt = ref(null);

function trackCalculatorEvent(event) {
  if (!props.proposalUuid) return;
  if (isPreviewMode()) return;
  const selectedIds = localModules.value.filter(m => m.selected).map(m => m.id);
  const deselectedIds = localModules.value.filter(m => !m.selected && !m._locked).map(m => m.id);
  const elapsedSeconds = openedAt.value ? Math.round((Date.now() - openedAt.value) / 1000) : 0;
  create_request(`proposals/${props.proposalUuid}/track-calculator/`, {
    event,
    selected: selectedIds,
    deselected: deselectedIds,
    total: dynamicTotal.value,
    elapsed_seconds: elapsedSeconds,
  }).catch(() => { /* silent */ });
}

const i18n = {
  es: {
    title: 'Personaliza tu inversión',
    subtitle: 'Selecciona los módulos que necesitas',
    close: 'Cerrar',
    selectedModules: 'Módulos seleccionados:',
    estimatedTotal: 'Total inversión',
    confirm: 'Confirmar selección',
    included: 'Incluido',
    required: 'obligatorio',
    viewRequirements: 'Ver detalle de requerimientos funcionales',
    estimatedDuration: 'Duración estimada',
    weeks: 'semanas',
    reducedFrom: 'Se reduce de',
    extendedFrom: 'Se extiende de',
    to: 'a',
    impactModule: 'Sin este módulo, tu proyecto tendrá menos cobertura en esta área.',
    impactView: 'Esta vista no estará disponible en la versión final.',
    impactFeature: 'Esta funcionalidad no se incluirá en el alcance.',
    impactIntegration: 'Esta integración no estará conectada al sistema.',
    impactGeneric: 'Este componente no se incluirá en el proyecto.',
    impactWeeksReduce: 'Se reduce ~1 semana del cronograma.',
    impactWeeksAdd: 'Aumenta ~1 semana el cronograma si se selecciona.',
    discountApplied: 'Descuento aplicado al confirmar',
    freeLabel: 'Gratis',
    viewDetail: 'Ver detalle',
    hideDetail: 'Ocultar detalle',
    scheduleCall: 'Agendar llamada',
    inviteNote: '🤝 Te invitamos a una llamada personalizada para explorar juntos cómo podemos transformar tu negocio. Conocerás nuestras soluciones, cómo las adaptamos a tu caso particular, y los costos asociados — sin compromiso.',
    optionalItemsBadge: 'Los elementos aquí son opcionales y pueden modificar el valor de la inversión y el tiempo de desarrollo. Para ver los requerimientos completos de tu proyecto, visítalos en la sección de Requerimientos Funcionales.',
  },
  en: {
    title: 'Customize your investment',
    subtitle: 'Select the modules you need',
    close: 'Close',
    selectedModules: 'Selected modules:',
    estimatedTotal: 'Total investment',
    confirm: 'Confirm selection',
    included: 'Included',
    required: 'required',
    viewRequirements: 'View functional requirements details',
    estimatedDuration: 'Estimated duration',
    weeks: 'weeks',
    reducedFrom: 'Reduced from',
    extendedFrom: 'Extended from',
    to: 'to',
    impactModule: 'Without this module, your project will have less coverage in this area.',
    impactView: 'This view will not be available in the final version.',
    impactFeature: 'This feature will not be included in the scope.',
    impactIntegration: 'This integration will not be connected to the system.',
    impactGeneric: 'This component will not be included in the project.',
    impactWeeksReduce: 'Reduces ~1 week from the timeline.',
    impactWeeksAdd: 'Adds ~1 week to the timeline if selected.',
    discountApplied: 'Discount applied on confirmation',
    freeLabel: 'Free',
    viewDetail: 'View detail',
    hideDetail: 'Hide detail',
    scheduleCall: 'Schedule a call',
    inviteNote: '🤝 We invite you to a personalized call where we\'ll explore together how we can transform your business. You\'ll learn about our solutions, how we tailor them to your specific case, and associated costs — no commitment required.',
    optionalItemsBadge: 'The items here are optional and may change the investment amount and development timeline. To see the full requirements for your project, visit the Functional Requirements section.',
  },
};

const t = computed(() => i18n[props.language] || i18n.es);

const localModules = ref([]);
const initialGroupOrder = ref([]);

watch(() => props.visible, (val) => {
  if (val) {
    // The page always passes the current selection (initialized from backend
    // or updated live on every toggle) as an array — an empty array means
    // "everything deselected", not "fall back to defaults". Only a non-array
    // prop is treated as unset.
    const saved = Array.isArray(props.selectedIds) ? props.selectedIds : null;

    localModules.value = props.modules.map(m => {
      const locked = m.is_required === true;
      const defaultSel = m.default_selected !== false;
      return {
        ...m,
        selected: locked ? true : (saved ? saved.includes(m.id) : defaultSel),
        _locked: locked,
      };
    });

    // Capture initial group order once so user interactions don't cause reordering
    const groups = {};
    for (const mod of localModules.value) {
      const key = mod._source === 'investment' ? 'investment' : (mod.groupId || '_other');
      if (!groups[key]) groups[key] = { hasSelected: false };
      if (mod.selected) groups[key].hasSelected = true;
    }
    const keys = Object.keys(groups);
    keys.sort((a, b) => {
      const aS = groups[a].hasSelected;
      const bS = groups[b].hasSelected;
      if (aS === bS) return 0;
      return aS ? -1 : 1;
    });
    initialGroupOrder.value = keys;
  }
}, { immediate: true });

const selectedCount = computed(() => localModules.value.filter(m => m.selected).length);

const expandedModules = ref(new Set());

function toggleDetail(modId) {
  if (expandedModules.value.has(modId)) {
    expandedModules.value.delete(modId);
  } else {
    expandedModules.value.add(modId);
  }
  expandedModules.value = new Set(expandedModules.value);
}

const groupLabels = {
  investment: { es: '💰 Módulos de inversión', en: '💰 Investment modules' },
  views: { es: '🖥️ Vistas', en: '🖥️ Views' },
  components: { es: '🧩 Componentes', en: '🧩 Components' },
  features: { es: '⚙️ Funcionalidades', en: '⚙️ Features' },
  integration_international_payments: { es: '🌎 Pasarela de Pago Internacional (Integración API)', en: '🌎 International Payment Gateway (API Integration)' },
  integration_regional_payments: { es: '🇨🇴 Pasarela de Pago Regional (Integración API)', en: '🇨🇴 Regional Payment Gateway (API Integration)' },
  integration_electronic_invoicing: { es: '🧾 Facturación Electrónica (Integración API)', en: '🧾 Electronic Invoicing (API Integration)' },
  integration_conversion_tracking: { es: '📡 Conversiones Inteligentes (Integración API)', en: '📡 Smart Conversions (API Integration)' },
  admin_module: { es: '🛠️ Módulo administrativo', en: '🛠️ Admin module' },
  analytics_dashboard: { es: '📊 Analítica', en: '📊 Analytics' },
  pwa_module: { es: '📱 Aplicación Móvil Instalable (PWA)', en: '📱 Installable Mobile App (PWA)' },
  corporate_branding_module: { es: '🎨 Identidad Visual e Imagen Corporativa', en: '🎨 Visual Identity & Corporate Branding' },
  ai_module: { es: '🤖 Integración con IA', en: '🤖 AI Integration' },
  reports_alerts_module: { es: '📬 Reportes y Alertas', en: '📬 Reports & Alerts' },
  kpi_dashboard_module: { es: '📊 Dashboard de KPIs', en: '📊 KPI Dashboard' },
  email_marketing_module: { es: '📧 Email Marketing', en: '📧 Email Marketing' },
  i18n_module: { es: '🌍 Multi-idioma', en: '🌍 Multi-language' },
  gift_cards_module: { es: '🎁 Gift Cards', en: '🎁 Gift Cards' },
  dark_mode_module: { es: '🌙 Dark Mode', en: '🌙 Dark Mode' },
  live_chat_module: { es: '💬 Chat en Vivo', en: '💬 Live Chat' },
  _other: { es: '🧩 Otros', en: '🧩 Other' },
};

const groupedModules = computed(() => {
  const groups = {};
  for (const mod of localModules.value) {
    const key = mod._source === 'investment' ? 'investment' : (mod.groupId || '_other');
    if (!groups[key]) {
      const labelObj = groupLabels[key] || groupLabels._other;
      groups[key] = { label: labelObj[props.language] || labelObj.es, items: [] };
    }
    groups[key].items.push(mod);
  }
  // Use frozen initial order so user interactions don't cause reordering
  const order = initialGroupOrder.value;
  const ordered = [];
  for (const key of order) {
    if (groups[key]) ordered.push([key, groups[key]]);
  }
  // Append any groups not in the initial order (safety fallback)
  for (const key of Object.keys(groups)) {
    if (!order.includes(key)) ordered.push([key, groups[key]]);
  }
  return Object.fromEntries(ordered);
});

const baseTotalInvestment = computed(() => parseInvestment(props.totalInvestment));

const dynamicTotal = computed(() => {
  const deselectedSum = localModules.value
    .filter(m => !m.selected && m._source !== 'calculator_module')
    .reduce((sum, m) => sum + (m.price || 0), 0);
  const addedSum = localModules.value
    .filter(m => m.selected && m._source === 'calculator_module' && m.price)
    .reduce((sum, m) => sum + (m.price || 0), 0);
  return baseTotalInvestment.value - deselectedSum + addedSum;
});

const { animated: animatedTotal } = useAnimatedNumber(dynamicTotal, 500);

// Dynamic timeline: week changes based on module selection
// Deselecting investment modules reduces weeks; selecting calculator modules adds weeks
const weeksReduction = computed(() => {
  const deselected = localModules.value.filter(m => !m.selected && !m._locked);
  let reduction = 0;
  let viewsRemoved = 0;
  let featuresRemoved = 0;

  for (const mod of deselected) {
    if (mod._source === 'investment') {
      reduction += 1;
    } else if (mod.groupId === 'views') {
      viewsRemoved += 1;
    } else if (mod.groupId === 'features') {
      featuresRemoved += 1;
    }
  }
  reduction += Math.floor(viewsRemoved / 3);
  reduction += Math.floor(featuresRemoved / 3);
  return reduction;
});

const weeksAddition = computed(() => {
  const selected = localModules.value.filter(m => m.selected && m._source === 'calculator_module' && !m.is_invite);
  let addition = 0;
  for (const mod of selected) {
    if (mod.groupId?.startsWith('integration_') || mod._source === 'calculator_module') {
      addition += 1;
    }
  }
  return addition;
});

const dynamicWeeks = computed(() => {
  if (!props.baseWeeks) return 0;
  return Math.max(1, props.baseWeeks - weeksReduction.value + weeksAddition.value);
});

const timelineChanged = computed(() => {
  return props.baseWeeks > 0 && dynamicWeeks.value !== props.baseWeeks;
});

function formatPrice(value) {
  if (!value && value !== 0) return '';
  return '$' + Number(value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function impactMessage(mod) {
  const groupId = mod.groupId || '';
  const source = mod._source || '';
  let msg = '';
  if (source === 'investment') {
    msg = t.value.impactModule;
  } else if (groupId === 'views') {
    msg = t.value.impactView;
  } else if (groupId === 'features') {
    msg = t.value.impactFeature;
  } else if (groupId?.startsWith('integration_')) {
    msg = t.value.impactIntegration;
  } else {
    msg = t.value.impactGeneric;
  }
  if (source === 'investment') {
    msg += ' ' + t.value.impactWeeksReduce;
  } else if (source === 'calculator_module' || groupId?.startsWith('integration_')) {
    msg += ' ' + t.value.impactWeeksAdd;
  }
  return msg;
}

const priceFeedback = ref({});
const feedbackTimers = {};

function toggleModule(mod) {
  if (mod._locked) return;
  mod.selected = !mod.selected;
  hasInteracted.value = true;

  // Live-sync selected calculator modules to functional requirements section
  const selectedIds = localModules.value.filter(m => m.selected).map(m => m.id);
  emit('updateCalculatorModules', selectedIds);

  if (mod.price && !mod.is_invite) {
    const sign = mod.selected ? '+' : '-';
    priceFeedback.value = { ...priceFeedback.value, [mod.id]: `${sign}${formatPrice(mod.price)}` };
    clearTimeout(feedbackTimers[mod.id]);
    feedbackTimers[mod.id] = setTimeout(() => {
      const copy = { ...priceFeedback.value };
      delete copy[mod.id];
      priceFeedback.value = copy;
    }, 1500);
  }
}

function confirmSelection() {
  const selectedIds = localModules.value.filter(m => m.selected).map(m => m.id);
  confirmed.value = true;
  trackCalculatorEvent('confirmed');
  emit('update:selection', { selectedIds, total: dynamicTotal.value, weeks: dynamicWeeks.value });
  emit('updateCalculatorModules', selectedIds);
  emit('selectionConfirmed', { selectedIds, total: dynamicTotal.value, weeks: dynamicWeeks.value });
  emit('close');
}

const totalPulsing = ref(false);
let pulseTimer = null;

watch(dynamicTotal, () => {
  if (!hasInteracted.value) return;
  totalPulsing.value = true;
  clearTimeout(pulseTimer);
  pulseTimer = setTimeout(() => { totalPulsing.value = false; }, 400);
});

watch(() => props.visible, (val) => {
  if (!val && hasInteracted.value && !confirmed.value) {
    trackCalculatorEvent('abandoned');
  }
  if (val) {
    hasInteracted.value = false;
    confirmed.value = false;
    openedAt.value = Date.now();
  }
});
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.detail-slide-enter-active,
.detail-slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.detail-slide-enter-from,
.detail-slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.detail-slide-enter-to,
.detail-slide-leave-from {
  opacity: 1;
  max-height: 500px;
}

@keyframes pulse-scale {
  0% { transform: scale(1); }
  50% { transform: scale(1.08); }
  100% { transform: scale(1); }
}
.total-pulse {
  animation: pulse-scale 0.35s ease-in-out;
}

.micro-feedback-enter-active { transition: all 0.2s ease; }
.micro-feedback-leave-active { transition: all 0.3s ease; }
.micro-feedback-enter-from { opacity: 0; transform: translateX(-4px); }
.micro-feedback-leave-to { opacity: 0; transform: translateX(4px); }

@keyframes discountChipIn {
  0%   { opacity: 0; transform: scale(0.85); }
  60%  { opacity: 1; transform: scale(1.04); }
  100% { opacity: 1; transform: scale(1); }
}
.discount-chip-enter-active {
  animation: discountChipIn 0.5s ease-out;
}
</style>
