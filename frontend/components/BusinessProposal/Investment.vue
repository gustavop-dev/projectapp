<template>
  <section ref="sectionRef" class="investment py-16 md:py-24 bg-white">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 max-w-5xl">
      <div class="section-header mb-12">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ title }}
          </h2>
        </div>
      </div>

      <div data-animate="fade-up" class="investment-intro mb-12">
        <p class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl">
          {{ introText }}
        </p>
      </div>

      <div data-animate="fade-up" class="pricing-card bg-esmerald p-5 sm:p-8 md:p-12 rounded-3xl text-white mb-12 shadow-2xl">
        <div class="text-center mb-8">
          <div class="text-sm font-semibold uppercase tracking-wider mb-4 text-green-light">{{ t.totalInvestment }}</div>
          <div v-if="customTotal !== null" class="text-4xl sm:text-6xl md:text-7xl font-bold mb-2 text-lemon">{{ formatCurrency(customTotal) }}</div>
          <div v-else class="text-4xl sm:text-6xl md:text-7xl font-bold mb-2 text-lemon">{{ totalInvestment }}</div>
          <div class="text-green-light">{{ currency }}</div>
          <p v-if="customTotal !== null" class="text-xs text-green-light/70 mt-2">{{ t.customized }}</p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-6 mt-8">
          <div v-for="(item, index) in whatsIncluded" :key="index"
               class="text-center p-4 bg-white/10 backdrop-blur-sm rounded-xl">
            <div class="text-3xl mb-2">{{ item.icon }}</div>
            <div class="font-bold text-esmerald-light mb-1">{{ item.title }}</div>
            <div class="text-sm text-esmerald-light/70">{{ item.description }}</div>
          </div>
        </div>
        <!-- Customize investment button -->
        <button
          v-if="modules && modules.length"
          ref="customizeBtnRef"
          class="mt-4 mx-auto block px-6 py-3 bg-lemon text-esmerald rounded-xl font-bold text-sm hover:bg-lemon/90 transition-all shadow-lg"
          :class="{ 'btn-pulse': btnPulse }"
          @click="calculatorOpen = true"
        >
          🧮 {{ t.customizeBtn }}
        </button>
      </div>

      <!-- Discount banner -->
      <div v-if="hasActiveDiscount" data-animate="fade-up" class="discount-banner mb-12 relative overflow-hidden bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-2xl p-5 sm:p-8">
        <div class="absolute top-0 right-0 bg-amber-500 text-white text-xs font-bold px-4 py-1.5 rounded-bl-xl">
          🔥 {{ discountPercent }}% OFF
        </div>
        <div class="flex flex-col sm:flex-row items-center gap-4 sm:gap-8">
          <div class="text-center sm:text-left">
            <p class="text-sm font-semibold text-amber-800 uppercase tracking-wider mb-1">{{ t.specialPriceLabel }}</p>
            <div class="flex items-baseline gap-3">
              <span class="text-3xl sm:text-4xl font-bold text-amber-700">{{ formatCurrency(discountedInvestment) }}</span>
              <span class="text-lg text-gray-400 line-through">{{ totalInvestment }}</span>
            </div>
            <p class="text-xs text-amber-600 mt-2">
              {{ currency }} · {{ t.validFor }}
              <template v-if="daysRemaining !== null">{{ daysRemaining }} {{ daysRemaining !== 1 ? t.days : t.day }}</template>
              <template v-else>{{ t.limitedTime }}</template>
            </p>
          </div>
        </div>
      </div>

      <div v-if="paymentOptions && paymentOptions.length" data-animate="fade-up" class="payment-options mb-12">
        <h3 class="text-2xl font-bold text-esmerald mb-6">{{ t.paymentOptions }}</h3>
        <div class="space-y-4">
          <div v-for="(option, index) in paymentOptions" :key="index"
               class="payment-option-card flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4 p-4 sm:p-5 bg-esmerald/5 rounded-xl border-2 border-esmerald/10 hover:border-esmerald/30 transition-all">
            <span class="text-esmerald/80 font-medium text-sm sm:text-base">{{ option.label }}</span>
            <span class="font-bold text-esmerald text-base sm:text-lg">{{ option.description }}</span>
          </div>
        </div>
      </div>

      <div v-if="hostingPlan.title" data-animate="fade-up" class="hosting-plan mt-12 bg-white p-5 sm:p-8 md:p-10 rounded-2xl border-2 border-esmerald/10">
        <div class="flex items-center mb-4">
          <div class="w-12 h-12 bg-esmerald-light/60 rounded-xl flex items-center justify-center mr-4">
            <span class="text-2xl">☁️</span>
          </div>
          <h3 class="text-2xl font-bold text-esmerald">{{ hostingPlan.title }}</h3>
        </div>
        <p v-if="hostingPlan.description" class="text-esmerald/70 font-light leading-relaxed mb-6 pl-0 sm:pl-16">{{ hostingPlan.description }}</p>

        <div class="mb-6 pl-0 sm:pl-16">
          <div class="grid sm:grid-cols-3 gap-4">
            <div v-for="(card, cIdx) in t.coverageCards" :key="cIdx"
                 class="bg-esmerald/5 border border-esmerald/10 rounded-xl p-5 text-center">
              <div class="text-3xl mb-3">{{ card.icon }}</div>
              <div class="font-bold text-esmerald text-sm mb-1">{{ card.title }}</div>
              <p class="text-xs text-esmerald/60 leading-relaxed">{{ card.description }}</p>
            </div>
          </div>
        </div>

        <div v-if="hostingPlan.monthlyPrice || hostingPlan.annualPrice" class="mt-6 pl-0 sm:pl-16">
          <div class="grid md:grid-cols-2 gap-4">
            <div v-if="hostingPlan.monthlyPrice" class="bg-esmerald-light/60 border border-esmerald/10 rounded-xl p-5">
              <div class="text-sm text-green-light font-medium">{{ t.specialPrice }}</div>
              <div class="text-2xl font-bold text-esmerald">{{ hostingPlan.monthlyPrice }}</div>
              <div v-if="hostingPlan.monthlyLabel" class="text-sm text-esmerald/70">{{ hostingPlan.monthlyLabel }}</div>
            </div>
            <div v-if="hostingPlan.annualPrice" class="bg-esmerald/5 border border-esmerald/10 rounded-xl p-5">
              <div class="text-sm text-green-light font-medium">{{ t.annualPayment }}</div>
              <div class="text-2xl font-bold text-esmerald">{{ hostingPlan.annualPrice }}</div>
              <div v-if="hostingPlan.annualLabel" class="text-sm text-esmerald/70">{{ hostingPlan.annualLabel }}</div>
            </div>
          </div>
        </div>

        <!-- Collapsible tech specs -->
        <div v-if="filteredSpecs.length" class="mt-6 pl-0 sm:pl-16">
          <button
            class="flex items-center gap-2 text-sm font-medium text-esmerald/60 hover:text-esmerald transition-colors mb-4"
            @click="specsOpen = !specsOpen"
          >
            <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-90': specsOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            {{ t.viewTechSpecs }}
          </button>
          <Transition name="collapse">
            <div v-if="specsOpen" class="grid md:grid-cols-2 gap-4">
              <div
                v-for="(spec, idx) in filteredSpecs"
                :key="idx"
                class="bg-esmerald/5 p-5 rounded-xl border border-esmerald/10"
              >
                <div class="flex items-start">
                  <div class="w-9 h-9 rounded-lg bg-esmerald-light/60 border border-esmerald/10 flex items-center justify-center mr-3 flex-shrink-0">
                    <span class="text-lg">{{ spec.icon }}</span>
                  </div>
                  <div>
                    <div class="font-bold text-esmerald">{{ spec.label }}</div>
                    <div class="text-sm text-esmerald/70">{{ spec.value }}</div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <div v-if="valueReasons && valueReasons.length" data-animate="fade-up" class="value-proposition mt-12 bg-esmerald p-5 sm:p-8 md:p-12 rounded-2xl">
        <h3 class="text-2xl font-bold text-lemon mb-6">{{ t.whyWorthIt }}</h3>
        <div class="grid md:grid-cols-2 gap-6">
          <div v-for="(reason, index) in normalizedReasons" :key="index"
               class="value-reason flex items-start">
            <div class="flex-shrink-0 w-10 h-10 bg-lemon rounded-lg flex items-center justify-center mr-4">
              <svg class="w-6 h-6 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <div>
              <p class="text-sm text-esmerald-light leading-relaxed">{{ reason }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <InvestmentCalculatorModal
      :visible="calculatorOpen"
      :modules="modules"
      :currency="currency"
      :proposalUuid="proposalUuid"
      :language="language"
      :totalInvestment="totalInvestment"
      @close="calculatorOpen = false"
      @update:selection="onSelectionUpdate"
    />
  </section>
</template>

<script setup>
import { ref, computed, toRef, onMounted } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';
import { useExpirationTimer } from '~/composables/useExpirationTimer';
import InvestmentCalculatorModal from './InvestmentCalculatorModal.vue';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const specsOpen = ref(false);
const calculatorOpen = ref(false);
const customTotal = ref(null);
const customizeBtnRef = ref(null);
const btnPulse = ref(false);

const props = defineProps({
  language: {
    type: String,
    default: 'es',
  },
  index: {
    type: String,
    default: '9'
  },
  title: {
    type: String,
    default: 'Inversión y Formas de Pago'
  },
  introText: {
    type: String,
    default: 'Costo total del desarrollo: $1.490.000 COP'
  },
  totalInvestment: {
    type: String,
    default: '$1.490.000'
  },
  currency: {
    type: String,
    default: 'COP'
  },
  whatsIncluded: {
    type: Array,
    default: () => [
      { icon: '🎨', title: 'Diseño', description: 'UX/UI enfocado en conversión' },
      { icon: '⚙️', title: 'Desarrollo', description: 'Implementación completa del proyecto' },
      { icon: '📦', title: 'Entrega y despliegue', description: 'Despliegue en producción y puesta en marcha' }
    ]
  },
  paymentOptions: {
    type: Array,
    default: () => [
      { label: '40% al firmar el contrato ✍️', description: '$596.000 COP' },
      { label: '30% al aprobar el diseño final ✅', description: '$447.000 COP' },
      { label: '30% al desplegar el sitio web 🚀', description: '$447.000 COP' }
    ]
  },
  hostingPlan: {
    type: Object,
    default: () => ({
      title: 'Hosting, Mantenimiento y Soporte',
      description: 'Infraestructura optimizada para proyectos de alto rendimiento y disponibilidad:',
      specs: [
        { icon: '🧠', label: 'vCPU', value: '1 núcleo de vCPU' },
        { icon: '🧮', label: 'RAM', value: '1 GB de RAM dedicada' },
        { icon: '💾', label: 'Almacenamiento', value: '2 GB de almacenamiento NVMe' },
        { icon: '🌐', label: 'Ancho de banda', value: '600 GB mensual' },
        { icon: '📍', label: 'Centros de datos', value: 'EE.UU., Brasil, Francia, Lituania e India' },
        { icon: '🧬', label: 'Compatibilidad', value: 'Linux (Ubuntu)' }
      ],
      monthlyPrice: '$49.999 COP',
      monthlyLabel: 'por mes',
      annualPrice: '$680.000 COP',
      annualLabel: 'Hosting anual — Año 1',
      renewalNote: '',
      coverageNote: ''
    })
  },
  paymentMethods: {
    type: Array,
    default: () => []
  },
  valueReasons: {
    type: Array,
    default: () => [
      'Diseño hecho a medida',
      'Código optimizado',
      'Soporte post-lanzamiento',
    ]
  },
  discountPercent: {
    type: Number,
    default: 0
  },
  discountedInvestment: {
    type: String,
    default: ''
  },
  expiresAt: {
    type: String,
    default: ''
  },
  modules: {
    type: Array,
    default: () => []
  },
  proposalUuid: {
    type: String,
    default: ''
  }
});

function parseInvestment(str) {
  if (!str) return 0;
  const cleaned = String(str).replace(/[^\d]/g, '');
  return parseInt(cleaned, 10) || 0;
}

onMounted(() => {
  if (props.proposalUuid && props.modules?.length) {
    try {
      const raw = localStorage.getItem(`proposal-${props.proposalUuid}-modules`);
      if (raw) {
        const selectedIds = JSON.parse(raw);
        const base = parseInvestment(props.totalInvestment);
        const deselectedSum = props.modules
          .filter(m => {
            const locked = m.is_required !== false && !m.removable;
            return !locked && !selectedIds.includes(m.id);
          })
          .reduce((sum, m) => sum + (m.price || 0), 0);
        customTotal.value = base - deselectedSum;
      }
    } catch (_e) { /* ignore */ }
  }
  if (props.modules?.length) {
    setTimeout(() => {
      btnPulse.value = true;
      setTimeout(() => { btnPulse.value = false; }, 4000);
    }, 1500);
  }
});

function onSelectionUpdate({ total }) {
  customTotal.value = total;
}

const { daysRemaining, urgencyLevel } = useExpirationTimer(toRef(props, 'expiresAt'));

const i18n = {
  es: {
    totalInvestment: 'Inversión Total',
    specialPriceLabel: 'Precio especial por tiempo limitado',
    validFor: 'Válido por',
    days: 'días',
    day: 'día',
    limitedTime: 'tiempo limitado',
    paymentOptions: 'Formas de Pago',
    specialPrice: 'Precio especial',
    annualPayment: 'Pago anual único',
    whyWorthIt: '¿Por Qué Esta Inversión Vale la Pena?',
    viewTechSpecs: 'Ver especificaciones técnicas',
    customizeBtn: 'Personalizar tu inversión',
    customized: 'Precio personalizado según tu selección',
    coverageCards: [
      { icon: '🔧', title: 'Mantenimiento técnico', description: 'Actualizaciones de seguridad, parches y optimización de base de datos' },
      { icon: '🛟', title: 'Soporte ante incidencias', description: 'Resolución de bugs y asistencia técnica continua' },
      { icon: '☁️', title: 'Recursos computacionales', description: 'Servidor, almacenamiento, ancho de banda y certificados SSL' },
    ],
  },
  en: {
    totalInvestment: 'Total Investment',
    specialPriceLabel: 'Special price — limited time',
    validFor: 'Valid for',
    days: 'days',
    day: 'day',
    limitedTime: 'a limited time',
    paymentOptions: 'Payment Options',
    specialPrice: 'Special price',
    annualPayment: 'Annual payment',
    whyWorthIt: 'Why Is This Investment Worth It?',
    viewTechSpecs: 'View technical specs',
    customizeBtn: 'Customize your investment',
    customized: 'Custom price based on your selection',
    coverageCards: [
      { icon: '🔧', title: 'Technical Maintenance', description: 'Security updates, patches, and database optimization' },
      { icon: '🛟', title: 'Incident Support', description: 'Bug resolution and ongoing technical assistance' },
      { icon: '☁️', title: 'Computing Resources', description: 'Server, storage, bandwidth, and SSL certificates' },
    ],
  },
};

const t = computed(() => i18n[props.language] || i18n.es);

const hasActiveDiscount = computed(() => {
  return props.discountPercent > 0 && props.discountedInvestment && daysRemaining.value !== null && daysRemaining.value <= 5;
});

function formatCurrency(value) {
  if (!value) return '';
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

const filteredSpecs = computed(() => {
  return (props.hostingPlan?.specs || []).filter(s => s.label || s.value);
});

const normalizedReasons = computed(() => {
  if (!props.valueReasons?.length) return [];
  return props.valueReasons.map(r => typeof r === 'string' ? r : (r.description || r.title || ''));
});
</script>

<style scoped>
.payment-option-card {
  transition: all 0.3s ease;
}

.payment-option-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.value-reason {
  transition: transform 0.3s ease;
}

.value-reason:hover {
  transform: translateX(8px);
}

.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 600px;
}

.btn-pulse {
  animation: btnDoublePulse 3.6s ease-in-out;
}

@keyframes btnDoublePulse {
  0%   { box-shadow: 0 0 0 0 rgba(225, 255, 0, 0.4); }
  10%  { box-shadow: 0 0 16px 6px rgba(225, 255, 0, 0.35); }
  24%  { box-shadow: 0 0 0 0 rgba(225, 255, 0, 0); }
  38%  { box-shadow: 0 0 16px 6px rgba(225, 255, 0, 0.35); }
  54%  { box-shadow: 0 0 0 0 rgba(225, 255, 0, 0); }
  100% { box-shadow: none; }
}
</style>
