<template>
  <section ref="sectionRef" class="proposal-summary py-16 md:py-24 bg-white">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 max-w-5xl">
      <div class="section-header mb-12">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ content.index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ content.title }}
          </h2>
        </div>
        <p v-if="content.subtitle" data-animate="fade-up" class="text-esmerald/70 font-light text-lg md:text-xl leading-relaxed">
          {{ content.subtitle }}
        </p>
      </div>

      <div data-animate="fade-up" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="(card, idx) in resolvedCards"
          :key="idx"
          class="summary-card bg-esmerald/5 border border-esmerald/10 rounded-2xl p-6 hover:border-esmerald/30 transition-all"
        >
          <div class="text-3xl mb-3">{{ card.icon }}</div>
          <h3 class="font-bold text-esmerald text-base mb-1">{{ card.title }}</h3>
          <p v-if="card.value" class="text-lg font-bold text-esmerald mb-2">{{ card.value }}</p>
          <p class="text-sm text-esmerald/60 leading-relaxed">{{ card.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  content: { type: Object, default: () => ({}) },
  proposal: { type: Object, default: () => ({}) },
  timelineDuration: { type: String, default: '' },
  language: { type: String, default: 'es' },
  proposalUuid: { type: String, default: '' },
  investmentModules: { type: Array, default: () => [] },
  rawTotalInvestment: { type: String, default: '' },
  paymentOptions: { type: Array, default: () => [] },
});

function parseInvestment(str) {
  if (!str) return 0;
  const cleaned = String(str).replace(/[^\d]/g, '');
  return parseInt(cleaned, 10) || 0;
}

function formatCurrency(value) {
  if (!value) return '';
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

const customTotal = ref(null);
const selectedModuleCount = ref(null);

onMounted(() => {
  if (props.proposalUuid && props.investmentModules?.length) {
    try {
      const raw = localStorage.getItem(`proposal-${props.proposalUuid}-modules`);
      if (raw) {
        const selectedIds = JSON.parse(raw);
        const base = parseInvestment(props.rawTotalInvestment);
        const deselectedSum = props.investmentModules
          .filter(m => m.is_required !== true && !selectedIds.includes(m.id))
          .reduce((sum, m) => sum + (m.price || 0), 0);
        if (deselectedSum > 0) {
          customTotal.value = base - deselectedSum;
        }
        selectedModuleCount.value = selectedIds.length;
      }
    } catch (_e) { /* ignore */ }
  }
});

const i18n = {
  es: {
    customized: 'Inversión personalizada según tu selección.',
    modulesTitle: 'Módulos del proyecto',
    modulesDesc: 'Componentes técnicos que conforman tu solución personalizada.',
    modulesCustomized: 'Personalizado — ajustado a tus necesidades.',
    paymentTitle: 'Formas de pago',
    paymentDesc: 'Opciones flexibles de pago para tu inversión.',
    discountTitle: 'Descuento especial',
    discountDesc: 'Precio preferencial disponible por tiempo limitado.',
    guaranteeTitle: 'Garantía post-lanzamiento',
    guaranteeDesc: 'Soporte técnico, corrección de bugs y mantenimiento incluido.',
    modules: 'módulos',
    options: 'opciones de pago',
  },
  en: {
    customized: 'Customized investment based on your selection.',
    modulesTitle: 'Project modules',
    modulesDesc: 'Technical components that make up your custom solution.',
    modulesCustomized: 'Customized — tailored to your needs.',
    paymentTitle: 'Payment options',
    paymentDesc: 'Flexible payment options for your investment.',
    discountTitle: 'Special discount',
    discountDesc: 'Preferential pricing available for a limited time.',
    guaranteeTitle: 'Post-launch guarantee',
    guaranteeDesc: 'Technical support, bug fixes, and maintenance included.',
    modules: 'modules',
    options: 'payment options',
  },
};

const t = computed(() => i18n[props.language] || i18n.es);

const resolvedCards = computed(() => {
  const cards = props.content?.cards || [];
  const existingSources = new Set(cards.map(c => c.source).filter(Boolean));

  const resolved = cards.map(card => {
    let value = '';
    let description = card.description;
    if (card.source === 'total_investment') {
      if (customTotal.value !== null) {
        value = `${formatCurrency(customTotal.value)} ${props.proposal?.currency || 'COP'}`;
        description = t.value.customized;
      } else if (props.proposal?.total_investment) {
        value = `${formatCurrency(props.proposal.total_investment)} ${props.proposal.currency || 'COP'}`;
      }
    } else if (card.source === 'timeline_duration' && props.timelineDuration) {
      value = props.timelineDuration;
    } else if (card.source === 'expires_at' && props.proposal?.expires_at) {
      const d = new Date(props.proposal.expires_at);
      value = d.toLocaleDateString(props.language === 'en' ? 'en-US' : 'es-CO', {
        day: 'numeric', month: 'long', year: 'numeric',
      });
      const now = new Date();
      const daysLeft = Math.max(Math.floor((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)), 0);
      description = props.language === 'en'
        ? `This proposal is valid for ${daysLeft} day${daysLeft !== 1 ? 's' : ''} from today.`
        : `Esta propuesta es válida por ${daysLeft} día${daysLeft !== 1 ? 's' : ''} a partir de hoy.`;
    }
    return { ...card, value, description };
  });

  // Auto-generate additional cards from available data
  if (!existingSources.has('modules_count') && props.investmentModules?.length) {
    const count = selectedModuleCount.value ?? props.investmentModules.length;
    resolved.push({
      icon: '🧩',
      title: t.value.modulesTitle,
      value: `${count} ${t.value.modules}`,
      description: selectedModuleCount.value !== null ? t.value.modulesCustomized : t.value.modulesDesc,
    });
  }

  if (!existingSources.has('payment_options') && props.paymentOptions?.length) {
    resolved.push({
      icon: '💳',
      title: t.value.paymentTitle,
      value: `${props.paymentOptions.length} ${t.value.options}`,
      description: t.value.paymentDesc,
    });
  }

  if (!existingSources.has('discount') && props.proposal?.discount_percent > 0) {
    resolved.push({
      icon: '🔥',
      title: t.value.discountTitle,
      value: `${props.proposal.discount_percent}% OFF`,
      description: t.value.discountDesc,
    });
  }

  if (!existingSources.has('guarantee')) {
    resolved.push({
      icon: '🛡️',
      title: t.value.guaranteeTitle,
      value: '',
      description: t.value.guaranteeDesc,
    });
  }

  return resolved;
});
</script>

<style scoped>
.summary-card {
  transition: all 0.3s ease;
}
.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}
</style>
