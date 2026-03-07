<template>
  <section ref="sectionRef" class="greeting-section min-h-screen flex items-center relative overflow-hidden bg-white">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 relative z-10">
      <div class="greeting-content max-w-7xl">
        <h1 data-animate="fade-up" class="main-title font-light text-esmerald leading-tight mb-8">
          {{ proposalTitle }}, {{ clientName }}
        </h1>
        
        <p data-animate="fade-up" class="subtitle font-light text-green-light italic">
          "{{ inspirationalQuote }}"
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  proposalTitle: {
    type: String,
    default: 'Propuesta de Desarrollo Web'
  },
  clientName: {
    type: String,
    default: 'Juan Pablo'
  },
  inspirationalQuote: {
    type: String,
    default: 'Design is not just what it looks like and feels like. Design is how it works.'
  }
});
</script>

<style scoped>
.greeting-section {
  position: relative;
}

.main-title {
  font-size: clamp(3rem, 8vw, 8rem);
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: clamp(1.25rem, 3vw, 2.5rem);
  letter-spacing: 0.02em;
}
</style>
