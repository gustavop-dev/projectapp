<template>
  <section ref="sectionRef" class="development-stages py-16 md:py-24 bg-white">
    <div class="container mx-auto px-6 md:px-12 lg:px-24 max-w-5xl">
      <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
        <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
          06
        </span>
        <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
          Etapas de contratación y desarrollo
        </h2>
      </div>

      <p data-animate="fade-up" class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl mb-12">
        Nuestro proceso está diseñado para ofrecer claridad, confianza y acompañamiento en cada fase 🧭:
      </p>

      <!-- Vertical timeline -->
      <div class="relative">
        <!-- Timeline line -->
        <div class="absolute left-6 top-0 bottom-0 w-px bg-emerald-200 hidden md:block"></div>

        <div data-animate="fade-up-stagger" class="space-y-4">
          <div
            v-for="(stage, idx) in stages"
            :key="stage.title"
            class="relative rounded-2xl border border-emerald-100 bg-white px-6 py-5 md:ml-14 transition-all"
            :class="stage.current ? 'border-emerald-500 bg-emerald-50/50 shadow-sm' : 'hover:border-emerald-200'"
          >
            <!-- Timeline dot -->
            <div
              class="absolute -left-[2.35rem] top-6 h-3 w-3 rounded-full border-2 border-white hidden md:block"
              :class="stage.current ? 'bg-emerald-600' : 'bg-emerald-300'"
            ></div>

            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                  <span class="text-xl md:text-2xl">{{ stage.icon }}</span>
                  <h3 class="text-esmerald font-medium text-base sm:text-lg md:text-xl leading-snug">
                    {{ stage.title }}
                  </h3>
                  <span v-if="stage.current" class="text-[10px] uppercase tracking-wider text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full font-medium">
                    Actual
                  </span>
                </div>
                <p class="text-esmerald/70 font-light leading-relaxed text-sm md:text-base">
                  {{ stage.description }}
                </p>
              </div>
              <div class="flex-shrink-0 text-green-light font-light tracking-[0.25em] text-xs pt-1">
                {{ String(idx + 1).padStart(2, '0') }}
              </div>
            </div>
          </div>
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
  stages: {
    type: Array,
    default: () => [
      { icon: '✉️', title: 'Propuesta Comercial', description: 'Presentación formal de la propuesta técnica y económica (etapa actual).', current: true },
      { icon: '🧾', title: 'Borrador de Contrato', description: 'Envío del documento que establece los términos, condiciones y compromisos de ambas partes.' },
      { icon: '✍️', title: 'Formalización del Contrato', description: 'Firma del acuerdo y confirmación del inicio oficial del proyecto.' },
      { icon: '🎨', title: 'Etapa de Diseño', description: 'Creación del prototipo visual en Figma, con reuniones de revisión para refinar la estética y estructura del sitio hasta su aprobación final.' },
      { icon: '💻', title: 'Etapa de Desarrollo', description: 'Implementación del diseño en código nativo, con una arquitectura limpia, fluida y optimizada para la mejor experiencia del usuario.' },
      { icon: '🚀', title: 'Despliegue del Proyecto', description: 'Publicación del sitio web en el entorno de producción y revisión final de funcionalidad y rendimiento.' },
      { icon: '💖', title: 'Entrega Final', description: 'Con el sitio en línea y validado, se realiza el pago final, cerrando el ciclo con una experiencia de transformación digital completa.' },
    ],
  },
});

const stages = props.stages;
</script>

<style scoped>
</style>
