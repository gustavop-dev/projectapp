<template>
  <section v-if="resolvedCards.length > 0" ref="sectionRef" class="value-added-modules min-h-screen w-full bg-white py-16">
    <div class="w-full px-6 md:px-12 lg:px-24">
      <div class="max-w-5xl mx-auto">
        <!-- Header -->
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-8">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ content.index || '' }}
          </span>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-esmerald-light/60">
              <span class="text-2xl">🎁</span>
            </div>
            <h2 class="text-esmerald font-light leading-tight text-3xl md:text-5xl">
              {{ content.title || defaultTitle }}
            </h2>
          </div>
        </div>

        <!-- Free badge + intro -->
        <div data-animate="fade-up" class="mb-10">
          <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold uppercase tracking-wider mb-5 border border-emerald-200">
            <span>✨</span>
            <span>{{ noCostLabel }}</span>
          </span>
          <p v-if="content.intro" class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl max-w-3xl">
            {{ content.intro }}
          </p>
        </div>

        <!-- Cards grid -->
        <div data-animate="fade-up-stagger" class="grid md:grid-cols-2 gap-5 mb-8">
          <article
            v-for="card in resolvedCards"
            :key="card.id"
            class="value-card bg-esmerald/5 p-6 rounded-2xl border border-esmerald/10 hover:border-esmerald/30 transition-colors"
            :data-testid="`value-added-card-${card.id}`"
          >
            <div class="flex items-start gap-4">
              <div class="w-11 h-11 rounded-xl bg-esmerald-light/60 border border-esmerald/10 flex items-center justify-center flex-shrink-0">
                <span class="text-2xl">{{ card.icon || '🧩' }}</span>
              </div>
              <div class="flex-1">
                <div class="flex items-start justify-between gap-3 mb-2">
                  <h3 class="font-bold text-esmerald text-lg leading-snug">{{ card.title }}</h3>
                  <span class="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full whitespace-nowrap">
                    {{ freeBadge }}
                  </span>
                </div>
                <p class="text-sm text-esmerald/75 font-light leading-relaxed mb-3">
                  {{ card.justification }}
                </p>
                <p v-if="card.description" class="text-xs text-esmerald/60 italic leading-relaxed">
                  {{ card.description }}
                </p>
              </div>
            </div>
          </article>
        </div>

        <!-- Footer note -->
        <div v-if="content.footer_note" data-animate="fade-up" class="bg-emerald-50 border border-emerald-200 rounded-xl px-5 py-4 text-center">
          <p class="text-emerald-800 text-sm md:text-base font-medium">
            {{ content.footer_note }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const props = defineProps({
  section: {
    type: Object,
    default: () => ({ content_json: {} }),
  },
  proposal: {
    type: Object,
    default: () => ({ sections: [] }),
  },
});

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const content = computed(() => props.section?.content_json || {});

const language = computed(() => props.proposal?.language || 'es');

const i18n = {
  es: {
    defaultTitle: 'Incluido sin costo adicional',
    noCost: 'Sin costo adicional',
    free: 'Gratis',
  },
  en: {
    defaultTitle: 'Included at no extra cost',
    noCost: 'No extra cost',
    free: 'Free',
  },
};
const t = computed(() => i18n[language.value] || i18n.es);

const defaultTitle = computed(() => t.value.defaultTitle);
const noCostLabel = computed(() => t.value.noCost);
const freeBadge = computed(() => t.value.free);

const moduleCatalog = computed(() => {
  const sections = props.proposal?.sections || [];
  const fr = sections.find((s) => s.section_type === 'functional_requirements');
  const groups = fr?.content_json?.groups || [];
  const lookup = {};
  for (const group of groups) {
    if (group && group.id) {
      lookup[group.id] = group;
    }
  }
  return lookup;
});

const resolvedCards = computed(() => {
  const ids = Array.isArray(content.value.module_ids) ? content.value.module_ids : [];
  const justifications = content.value.justifications || {};
  const catalog = moduleCatalog.value;
  return ids
    .map((id) => {
      const group = catalog[id];
      if (!group) return null;
      return {
        id,
        icon: group.icon,
        title: group.title,
        description: group.description,
        justification: justifications[id] || '',
      };
    })
    .filter(Boolean);
});
</script>

<style scoped>
.value-card {
  transition: all 0.3s ease;
}

.value-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(7, 89, 73, 0.06);
}
</style>
