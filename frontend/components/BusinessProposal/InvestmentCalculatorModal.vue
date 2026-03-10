<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')" />
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-gray-100 bg-esmerald">
            <div>
              <h3 class="text-xl font-bold text-lemon">{{ t.title }}</h3>
              <p class="text-sm text-esmerald-light/70 mt-1">{{ t.subtitle }}</p>
            </div>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-esmerald-light/60 hover:text-white hover:bg-white/10 transition-colors"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto px-6 py-6 flex-1">
            <template v-for="(group, gKey) in groupedModules" :key="gKey">
              <div class="mb-1 mt-4 first:mt-0">
                <h4 class="text-xs font-semibold text-gray-400 uppercase tracking-wider px-1">{{ group.label }}</h4>
              </div>
              <div class="space-y-2 mb-4">
                <div
                  v-for="mod in group.items"
                  :key="mod.id"
                  class="rounded-xl border transition-all"
                  :class="[
                    mod.selected
                      ? 'bg-esmerald/5 border-esmerald/20'
                      : 'bg-gray-50 border-gray-200',
                    mod._locked ? 'opacity-80' : 'cursor-pointer hover:border-esmerald/40'
                  ]"
                  @click="toggleModule(mod)"
                >
                  <div class="flex items-center justify-between p-4">
                    <div class="flex items-center gap-3 flex-1 min-w-0">
                      <div
                        class="w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors flex-shrink-0"
                        :class="mod.selected
                          ? 'bg-esmerald border-esmerald text-white'
                          : 'border-gray-300 bg-white'"
                      >
                        <svg v-if="mod.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div class="min-w-0">
                        <span class="font-medium" :class="mod.selected ? 'text-esmerald' : 'text-gray-500'">
                          {{ mod.name }}
                        </span>
                        <span v-if="mod._locked" class="ml-2 text-[10px] text-esmerald/50 font-medium uppercase">{{ t.required }}</span>
                        <span v-if="mod._freeActive" class="ml-2 text-[10px] bg-amber-100 text-amber-700 font-bold px-1.5 py-0.5 rounded-full">🎁 {{ t.freeLabel }}</span>
                        <p v-if="!mod.selected && !mod._locked && !mod.is_ai_invite" class="text-[11px] text-amber-600 leading-snug mt-0.5">
                          ⚠ {{ impactMessage(mod) }}
                        </p>
                      </div>
                    </div>
                    <span v-if="mod.is_ai_invite" class="text-[11px] font-semibold text-purple-600 flex-shrink-0">
                      {{ t.aiScheduleCall }}
                    </span>
                    <span v-else class="font-bold text-sm flex-shrink-0" :class="mod.selected ? 'text-esmerald' : 'text-gray-400'">
                      {{ mod.price ? (mod._source === 'calculator_module' && mod.selected ? '+' : '') + formatPrice(mod.price) : t.included }}
                    </span>
                  </div>
                  <!-- AI invite creative note -->
                  <div v-if="mod.is_ai_invite" class="px-4 pb-4 -mt-1">
                    <div class="bg-purple-50 border border-purple-100 rounded-lg px-3 py-2.5">
                      <p class="text-[11px] text-purple-700 leading-relaxed">
                        {{ t.aiInviteNote }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- Informational badge -->
            <div class="mt-4 mb-2 bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
              <p class="text-[11px] text-blue-700 leading-relaxed">
                💡 {{ t.optionalItemsBadge }}
              </p>
              <button
                type="button"
                class="mt-1.5 text-[11px] text-blue-600 font-semibold hover:text-blue-800 transition-colors flex items-center gap-1"
                @click="$emit('navigateToRequirements')"
              >
                📋 {{ t.viewRequirements }}
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Footer with total -->
          <div class="px-6 py-5 border-t border-gray-100 bg-gray-50">
            <div class="flex items-center justify-between mb-4">
              <div>
                <span class="text-sm text-gray-500">{{ t.selectedModules }}</span>
                <span class="ml-1 text-sm font-medium text-esmerald">{{ selectedCount }}/{{ localModules.length }}</span>
              </div>
              <div class="text-right">
                <span class="text-sm text-gray-500 block">{{ t.estimatedTotal }}</span>
                <span class="text-2xl font-bold text-esmerald">{{ formatPrice(animatedTotal) }}</span>
                <span class="text-xs text-gray-400 ml-1">{{ currency }}</span>
              </div>
            </div>
            <!-- Dynamic timeline -->
            <div v-if="baseWeeks > 0" class="flex items-center justify-between mb-4 px-3 py-2.5 rounded-xl" :class="timelineChanged ? 'bg-blue-50 border border-blue-200' : 'bg-gray-100'">
              <div class="flex items-center gap-2">
                <span class="text-sm">⏱</span>
                <span class="text-sm text-gray-600">{{ t.estimatedDuration }}</span>
              </div>
              <div class="text-right">
                <span class="text-lg font-bold" :class="timelineChanged ? 'text-blue-600' : 'text-esmerald'">{{ dynamicWeeks }} {{ t.weeks }}</span>
                <span v-if="timelineChanged" class="block text-[11px] text-blue-500 font-medium">
                  {{ t.reducedFrom }} {{ baseWeeks }} {{ t.to }} {{ dynamicWeeks }} {{ t.weeks }}
                </span>
              </div>
            </div>
            <button
              class="w-full py-3 bg-esmerald text-lemon rounded-xl font-bold text-sm hover:bg-esmerald/90 transition-colors shadow-md"
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

const props = defineProps({
  visible: { type: Boolean, default: false },
  modules: { type: Array, default: () => [] },
  currency: { type: String, default: 'COP' },
  proposalUuid: { type: String, default: '' },
  language: { type: String, default: 'es' },
  totalInvestment: { type: String, default: '' },
  baseWeeks: { type: Number, default: 0 },
  sentAt: { type: String, default: '' },
});

function parseInvestment(str) {
  if (!str) return 0;
  const cleaned = String(str).replace(/[^\d]/g, '');
  return parseInt(cleaned, 10) || 0;
}

const emit = defineEmits(['close', 'update:selection', 'navigateToRequirements', 'updateCalculatorModules']);

const i18n = {
  es: {
    title: 'Personaliza tu inversión',
    subtitle: 'Selecciona los módulos que necesitas',
    selectedModules: 'Módulos seleccionados:',
    estimatedTotal: 'Total inversión',
    confirm: 'Confirmar selección',
    included: 'Incluido',
    required: 'obligatorio',
    viewRequirements: 'Ver detalle de requerimientos funcionales',
    estimatedDuration: 'Duración estimada',
    weeks: 'semanas',
    reducedFrom: 'Se reduce de',
    to: 'a',
    impactModule: 'Sin este módulo, tu proyecto tendrá menos cobertura en esta área.',
    impactView: 'Esta vista no estará disponible en la versión final.',
    impactFeature: 'Esta funcionalidad no se incluirá en el alcance.',
    impactIntegration: 'Esta integración no estará conectada al sistema.',
    impactGeneric: 'Este componente no se incluirá en el proyecto.',
    impactWeeks: 'Se reduce ~1 semana del cronograma.',
    freeLabel: 'Gratis',
    aiScheduleCall: 'Agendar llamada',
    aiInviteNote: '🤝 Te invitamos a una llamada personalizada donde exploraremos juntos cómo la inteligencia artificial puede transformar tu negocio. Conocerás nuestras soluciones, cómo las adaptamos a tu caso particular, y los costos asociados — sin compromiso.',
    optionalItemsBadge: 'Los elementos aquí son opcionales y pueden modificar el valor de la inversión y el tiempo de desarrollo. Para ver los requerimientos completos de tu proyecto, visítalos en la sección de Requerimientos Funcionales.',
  },
  en: {
    title: 'Customize your investment',
    subtitle: 'Select the modules you need',
    selectedModules: 'Selected modules:',
    estimatedTotal: 'Total investment',
    confirm: 'Confirm selection',
    included: 'Included',
    required: 'required',
    viewRequirements: 'View functional requirements details',
    estimatedDuration: 'Estimated duration',
    weeks: 'weeks',
    reducedFrom: 'Reduced from',
    to: 'to',
    impactModule: 'Without this module, your project will have less coverage in this area.',
    impactView: 'This view will not be available in the final version.',
    impactFeature: 'This feature will not be included in the scope.',
    impactIntegration: 'This integration will not be connected to the system.',
    impactGeneric: 'This component will not be included in the project.',
    impactWeeks: 'Reduces ~1 week from the timeline.',
    freeLabel: 'Free',
    aiScheduleCall: 'Schedule a call',
    aiInviteNote: '🤝 We invite you to a personalized call where we\'ll explore together how artificial intelligence can transform your business. You\'ll learn about our solutions, how we tailor them to your specific case, and associated costs — no commitment required.',
    optionalItemsBadge: 'The items here are optional and may change the investment amount and development timeline. To see the full requirements for your project, visit the Functional Requirements section.',
  },
};

const t = computed(() => i18n[props.language] || i18n.es);

const localModules = ref([]);

watch(() => props.visible, (val) => {
  if (val) {
    const storageKey = `proposal-${props.proposalUuid}-modules`;
    let saved = null;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) saved = JSON.parse(raw);
    } catch (_e) { /* ignore */ }

    const now = new Date();
    localModules.value = props.modules.map(m => {
      const locked = m.is_required === true;
      // Compute free promotion status
      let freeActive = false;
      if (m.is_free && m.free_days && props.sentAt) {
        const sentDate = new Date(props.sentAt);
        const expiresAt = new Date(sentDate.getTime() + m.free_days * 86400000);
        freeActive = now < expiresAt;
      }
      const defaultSel = m.default_selected !== false;
      return {
        ...m,
        selected: locked ? true : (saved ? saved.includes(m.id) : defaultSel),
        _locked: locked,
        _freeActive: freeActive,
      };
    });
  }
}, { immediate: true });

const selectedCount = computed(() => localModules.value.filter(m => m.selected).length);

const groupLabels = {
  investment: { es: 'Módulos de inversión', en: 'Investment modules' },
  views: { es: 'Vistas', en: 'Views' },
  components: { es: 'Componentes', en: 'Components' },
  features: { es: 'Funcionalidades', en: 'Features' },
  integrations_api: { es: 'Integraciones', en: 'Integrations' },
  admin_module: { es: 'Módulo administrativo', en: 'Admin module' },
  analytics_dashboard: { es: 'Analítica', en: 'Analytics' },
  pwa_module: { es: 'Progressive Web App (PWA)', en: 'Progressive Web App (PWA)' },
  ai_module: { es: '🤖 Implementación con IA', en: '🤖 AI Implementation' },
  reports_alerts_module: { es: 'Reportes y Alertas', en: 'Reports & Alerts' },
  _other: { es: 'Otros', en: 'Other' },
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
  return groups;
});

const baseTotalInvestment = computed(() => parseInvestment(props.totalInvestment));

const dynamicTotal = computed(() => {
  const deselectedSum = localModules.value
    .filter(m => !m.selected && m._source !== 'calculator_module')
    .reduce((sum, m) => sum + (m.price || 0), 0);
  const freeSum = localModules.value
    .filter(m => m.selected && m._freeActive && m.price)
    .reduce((sum, m) => sum + (m.price || 0), 0);
  const addedSum = localModules.value
    .filter(m => m.selected && m._source === 'calculator_module' && m.price)
    .reduce((sum, m) => sum + (m.price || 0), 0);
  return baseTotalInvestment.value - deselectedSum - freeSum + addedSum;
});

const { animated: animatedTotal } = useAnimatedNumber(dynamicTotal, 500);

// Dynamic timeline: week reduction based on deselected items
// Rule: 1 module/integration removed = -1 week; every 3 views or 3 features removed = -1 week
const weeksReduction = computed(() => {
  const deselected = localModules.value.filter(m => !m.selected && !m._locked);
  let reduction = 0;
  let viewsRemoved = 0;
  let featuresRemoved = 0;

  for (const mod of deselected) {
    if (mod._source === 'investment' || mod.groupId === 'integrations_api') {
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

const dynamicWeeks = computed(() => {
  if (!props.baseWeeks) return 0;
  return Math.max(1, props.baseWeeks - weeksReduction.value);
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
  } else if (groupId === 'integrations_api') {
    msg = t.value.impactIntegration;
  } else {
    msg = t.value.impactGeneric;
  }
  if (source === 'investment' || groupId === 'integrations_api') {
    msg += ' ' + t.value.impactWeeks;
  }
  return msg;
}

function toggleModule(mod) {
  if (mod._locked) return;
  mod.selected = !mod.selected;
}

function confirmSelection() {
  const selectedIds = localModules.value.filter(m => m.selected).map(m => m.id);
  const storageKey = `proposal-${props.proposalUuid}-modules`;
  try {
    localStorage.setItem(storageKey, JSON.stringify(selectedIds));
  } catch (_e) { /* ignore */ }
  emit('update:selection', { selectedIds, total: dynamicTotal.value, weeks: dynamicWeeks.value });
  emit('updateCalculatorModules', selectedIds);
  emit('close');
}
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
</style>
