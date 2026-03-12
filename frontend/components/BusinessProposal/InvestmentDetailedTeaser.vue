<template>
  <div class="mt-6 bg-esmerald-light/60 border border-esmerald/15 rounded-2xl p-5 sm:p-6 text-center">
    <div class="mb-3">
      <span class="text-2xl">🔍</span>
    </div>
    <h4 class="text-esmerald font-bold text-sm sm:text-base mb-2">
      {{ t.title }}
    </h4>
    <p class="text-esmerald/60 font-light text-xs sm:text-sm leading-relaxed max-w-md mx-auto mb-4">
      {{ t.description }}
    </p>
    <button
      type="button"
      class="inline-flex items-center gap-2 px-5 py-2.5 bg-esmerald text-lemon rounded-xl
             font-bold text-xs sm:text-sm hover:bg-esmerald/90 transition-all shadow-md"
      @click="$emit('switchToDetailed')"
    >
      {{ t.cta }}
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  language: {
    type: String,
    default: 'es',
  },
});

defineEmits(['switchToDetailed']);

const i18n = {
  es: {
    title: 'Hay más por descubrir',
    description:
      'En la Propuesta Completa puedes explorar funcionalidades adicionales como inteligencia artificial, aplicaciones móviles, integración con Meta y Google Ads, pasarelas de pago y más.',
    cta: 'Ver Propuesta Completa',
  },
  en: {
    title: 'There\'s more to discover',
    description:
      'In the Full Proposal you can explore additional features like artificial intelligence, mobile apps, Meta & Google Ads integration, payment gateways, and more.',
    cta: 'View Full Proposal',
  },
};

const t = computed(() => i18n[props.language] || i18n.es);
</script>
