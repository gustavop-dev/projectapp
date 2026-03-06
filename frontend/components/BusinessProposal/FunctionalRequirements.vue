<template>
  <section ref="sectionRef" class="functional-requirements min-h-full w-full bg-white flex items-center">
    <div class="w-full px-6 md:px-12 lg:px-24 py-12 md:py-6">
      <div class="max-w-5xl mx-auto">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ data.index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ data.title }}
          </h2>
        </div>

        <div data-animate="fade-up" class="requirements-intro mb-12">
          <p class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl max-w-3xl">
            {{ data.intro }}
          </p>
        </div>

        <!-- Overview: group icons + titles + descriptions -->
        <div v-if="allGroups.length" data-animate="fade-up-stagger" class="overview-grid grid md:grid-cols-2 gap-6">
          <div v-for="group in allGroups" :key="group.id || group.title"
               class="overview-card bg-gray-50 p-6 rounded-2xl border border-gray-100">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                   :class="getGroupBgColor(group)">
                <span class="text-xl">{{ group.icon || '🧩' }}</span>
              </div>
              <h3 class="text-lg font-bold text-gray-900">{{ group.title }}</h3>
            </div>
            <p class="text-sm text-gray-600 leading-relaxed">{{ group.description }}</p>
          </div>
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
  data: {
    type: Object,
    default: () => ({
      index: '7',
      title: 'Requerimientos funcionales',
      intro: 'A continuación se detallan los requerimientos funcionales del proyecto.',
      groups: [],
      additionalModules: [],
    })
  }
});

const data = props.data;

const allGroups = computed(() => {
  const groups = data.groups || [];
  const additional = data.additionalModules || [];
  return [...groups, ...additional].filter(g => g && (g.title || g.items?.length));
});

const getGroupBgColor = (group) => {
  const id = group?.id;
  if (id === 'views') return 'bg-blue-100';
  if (id === 'components') return 'bg-purple-100';
  if (id === 'features') return 'bg-green-100';
  if (id === 'integrations_api') return 'bg-indigo-100';
  if (id === 'admin_module') return 'bg-amber-100';
  return 'bg-emerald-100';
};
</script>

<style scoped>
.overview-card {
  transition: all 0.3s ease;
}

.overview-card:hover {
  border-color: #d1d5db;
  transform: translateY(-2px);
}
</style>
