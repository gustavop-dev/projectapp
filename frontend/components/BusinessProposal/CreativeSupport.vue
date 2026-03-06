<template>
  <section ref="sectionRef" class="creative-support min-h-screen w-full bg-white flex items-center">
    <div class="w-full px-6 md:px-12 lg:px-24 py-12 md:py-6">
      <div class="max-w-7xl mx-auto">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ content.index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ content.title }}
          </h2>
        </div>

        <div class="grid lg:grid-cols-12 gap-10 items-start">
          <div data-animate="fade-up" class="lg:col-span-8 space-y-6">
            <p
              v-for="(paragraph, idx) in content.paragraphs"
              :key="idx"
              class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl"
            >
              {{ paragraph }}
            </p>

            <div v-if="content.closing" class="pt-2">
              <p class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl">
                {{ content.closing }}
              </p>
            </div>
          </div>

          <aside v-if="content.includes?.length" data-animate="fade-up" class="lg:col-span-4">
            <div class="rounded-3xl bg-esmerald-light/60 p-6 md:p-8">
              <h3 class="text-esmerald font-light text-base md:text-lg tracking-wide mb-5">
                {{ content.includesTitle }}
              </h3>
              <ul class="space-y-4">
                <li v-for="(item, idx) in content.includes" :key="idx" class="flex gap-3">
                  <span class="mt-3 h-1.5 w-1.5 rounded-full bg-esmerald flex-shrink-0"></span>
                  <p class="text-esmerald/80 font-light leading-relaxed">
                    {{ item }}
                  </p>
                </li>
              </ul>
            </div>
          </aside>
        </div>
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
  content: {
    type: Object,
    default: () => ({
      index: '5',
      title: 'Acompañamiento creativo personalizado',
      paragraphs: [
        'Durante todo el proceso, el cliente contará con el acompañamiento cercano de nuestro equipo creativo y técnico �. Crearemos juntos un proyecto digital que capture la esencia de su propósito.',
        'El proceso será colaborativo, cálido y empático, cuidando tanto el detalle visual como el sentido emocional detrás de cada palabra, color o imagen.'
      ],
      includesTitle: 'Incluye',
      includes: [
        '💡 Sesiones de revisión y retroalimentación sobre diseño y estructura.',
        '🎨 Apoyo en la selección de paleta de colores, tipografía y estilo visual que transmitan calma y autenticidad.',
        '🕊 Adaptaciones según la evolución de las ideas o nuevas inspiraciones que surjan durante el proceso.',
        '🔗 Aseguramiento de coherencia entre estética, contenido y propósito del proyecto.'
      ],
      closing: 'Cada decisión será una co-creación, en la que el cliente podrá participar activamente para que el resultado final refleje fielmente su energía y su mensaje.'
    })
  }
});
</script>

<style scoped>
</style>
