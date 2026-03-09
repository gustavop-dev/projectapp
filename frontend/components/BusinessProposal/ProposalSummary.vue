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
import { ref, computed } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  content: { type: Object, default: () => ({}) },
  proposal: { type: Object, default: () => ({}) },
  timelineDuration: { type: String, default: '' },
  language: { type: String, default: 'es' },
});

function formatCurrency(value) {
  if (!value) return '';
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

const resolvedCards = computed(() => {
  const cards = props.content?.cards || [];
  return cards.map(card => {
    let value = '';
    let description = card.description;
    if (card.source === 'total_investment' && props.proposal?.total_investment) {
      value = `${formatCurrency(props.proposal.total_investment)} ${props.proposal.currency || 'COP'}`;
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
