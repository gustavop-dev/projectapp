<template>
  <section ref="sectionRef" class="functional-requirements py-16 md:py-24 bg-white">
    <div class="container mx-auto px-4 max-w-5xl">
      <div class="section-header mb-12">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ data.index }}
          </span>
          <h2 class="text-esmerald font-light leading-tight text-4xl md:text-6xl">
            {{ data.title }}
          </h2>
        </div>
      </div>

      <div class="requirements-intro mb-12">
        <p class="text-xl text-gray-600 leading-relaxed">
          {{ data.intro }}
        </p>
      </div>

      <!-- Overview: group icons + titles + descriptions -->
      <div v-if="allGroups.length" data-animate="fade-up" class="overview-grid grid md:grid-cols-2 gap-6 mb-16">
        <div v-for="group in allGroups" :key="group.id || group.title"
             class="overview-card bg-gray-50 p-6 rounded-2xl border border-gray-100">
          <div class="flex items-center gap-3 mb-3">
            <span class="text-2xl">{{ group.icon || '🧩' }}</span>
            <h3 class="text-lg font-bold text-gray-900">{{ group.title }}</h3>
          </div>
          <p class="text-sm text-gray-600 leading-relaxed">{{ group.description }}</p>
        </div>
      </div>

      <!-- Sub-sections: 7.1, 7.2, etc. -->
      <div data-animate="fade-up-stagger" class="sub-sections space-y-16">
        <div v-for="(group, gIdx) in allGroups" :key="group.id || gIdx"
             class="sub-section">
          <div class="sub-section-header mb-8">
            <div class="flex items-baseline gap-3 mb-4">
              <span class="text-green-light font-light tracking-[0.25em] text-xs">
                {{ data.index }}.{{ gIdx + 1 }}
              </span>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                     :class="getGroupBgColor(group)">
                  <span class="text-xl">{{ group.icon || '🧩' }}</span>
                </div>
                <h3 class="text-2xl font-bold text-gray-900">{{ group.title }}</h3>
              </div>
            </div>
            <p class="text-gray-600 leading-relaxed pl-0 md:pl-14">{{ group.description }}</p>
          </div>

          <div v-if="group.items && group.items.length" class="requirements-grid grid md:grid-cols-2 gap-4 pl-0 md:pl-14">
            <div v-for="(item, idx) in group.items" :key="idx"
                 class="requirement-card bg-gray-50 p-5 rounded-xl hover:bg-emerald-50 transition-colors border border-gray-100 hover:border-emerald-200">
              <div class="flex items-start">
                <div class="w-9 h-9 rounded-lg bg-white border border-gray-200 flex items-center justify-center mr-3 flex-shrink-0">
                  <span class="text-lg">{{ item.icon || '✅' }}</span>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900 mb-1">{{ item.name }}</h4>
                  <p class="text-sm text-gray-600">{{ item.description }}</p>
                </div>
              </div>
            </div>
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
  if (id === 'admin_module') return 'bg-amber-100';
  return 'bg-emerald-100';
};
</script>

<style scoped>
.requirement-card {
  transition: all 0.3s ease;
}

.requirement-card:hover {
  transform: translateX(4px);
}

.overview-card {
  transition: all 0.3s ease;
}

.overview-card:hover {
  border-color: #d1d5db;
}
</style>
