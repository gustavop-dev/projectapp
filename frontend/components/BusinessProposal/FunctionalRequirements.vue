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

      <div data-animate="fade-up-stagger" class="requirements-categories space-y-8">
        <div v-for="(group, index) in data.groups" :key="group.id || index"
             class="category-section">
          <div class="category-header mb-6">
            <div class="flex items-center mb-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center mr-4"
                   :class="getGroupBgColor(group)">
                <span class="text-2xl">{{ getGroupIcon(group) }}</span>
              </div>
              <h3 class="text-2xl font-bold text-gray-900">{{ getGroupTitle(group) }}</h3>
            </div>
            <p class="text-gray-600 leading-relaxed pl-16">{{ group.description }}</p>
          </div>

          <div class="requirements-grid grid md:grid-cols-2 gap-4 pl-16">
            <div v-for="(item, idx) in group.items" :key="item.id || idx"
                 class="requirement-card bg-gray-50 p-5 rounded-xl hover:bg-emerald-50 transition-colors border border-gray-100 hover:border-emerald-200">
              <div class="flex items-start">
                <div class="w-9 h-9 rounded-lg bg-white border border-gray-200 flex items-center justify-center mr-3 flex-shrink-0">
                  <span class="text-lg">{{ item.icon || '✅' }}</span>
                </div>
                <div>
                  <h4 class="font-bold text-gray-900 mb-1">{{ item.name }}</h4>
                  <p class="text-sm text-gray-600">{{ item.description }}</p>

                  <div v-if="(item.options && item.options.length) || (item.fields && item.fields.length)" class="mt-3 space-y-2">
                    <div v-if="item.options && item.options.length" class="flex flex-wrap gap-2">
                      <span
                        v-for="(opt, oIdx) in item.options"
                        :key="opt.key || oIdx"
                        class="text-xs px-2 py-1 rounded-lg bg-emerald-100 text-emerald-800"
                      >
                        {{ opt.label }}
                      </span>
                    </div>

                    <div v-if="item.fields && item.fields.length" class="flex flex-wrap gap-2">
                      <span
                        v-for="(field, fIdx) in item.fields"
                        :key="field.key || fIdx"
                        class="text-xs px-2 py-1 rounded-lg bg-gray-200 text-gray-700"
                      >
                        {{ field.label }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="data.technicalSpecs && data.technicalSpecs.length" class="technical-specs mt-12 bg-gradient-to-br from-gray-900 to-gray-800 p-8 md:p-12 rounded-2xl text-white">
        <h3 class="text-2xl font-bold mb-8">Especificaciones Técnicas</h3>
        <div class="grid md:grid-cols-3 gap-8">
          <div v-for="(spec, index) in data.technicalSpecs" :key="index"
               class="spec-item">
            <div class="flex items-center mb-3">
              <div class="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center mr-3">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="spec.icon"></path>
                </svg>
              </div>
              <h4 class="font-bold">{{ spec.title }}</h4>
            </div>
            <ul class="space-y-2 pl-13">
              <li v-for="(item, idx) in spec.items" :key="idx"
                  class="text-sm text-gray-300 flex items-start">
                <span class="text-emerald-400 mr-2">•</span>
                <span>{{ item }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div v-if="data.integrations && data.integrations.length" class="integrations mt-8 bg-white p-8 md:p-10 rounded-2xl border-2 border-gray-100">
        <h3 class="text-2xl font-bold text-gray-900 mb-6">Integraciones Disponibles</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="(integration, index) in data.integrations" :key="index"
               class="integration-card p-4 bg-gray-50 rounded-xl text-center hover:bg-emerald-50 transition-colors">
            <div class="text-3xl mb-2">{{ integration.icon }}</div>
            <div class="text-sm font-medium text-gray-900">{{ integration.name }}</div>
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
  data: {
    type: Object,
    default: () => ({
      index: '07',
      title: 'Requerimientos funcionales',
      intro: 'A continuación se detallan los requerimientos funcionales del proyecto.',
      groups: [],
      technicalSpecs: [],
      integrations: [],
    })
  }
});

const data = props.data;

const getGroupIcon = (group) => {
  const title = group?.title || '';
  const first = title.trim().split(' ')[0];
  return first || '🧩';
};

const getGroupTitle = (group) => {
  const title = group?.title || '';
  const parts = title.trim().split(' ');
  if (parts.length <= 1) return title;
  return parts.slice(1).join(' ');
};

const getGroupBgColor = (group) => {
  const id = group?.id;
  if (id === 'views') return 'bg-blue-100';
  if (id === 'components') return 'bg-purple-100';
  if (id === 'features') return 'bg-green-100';
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

.integration-card {
  transition: all 0.3s ease;
}

.integration-card:hover {
  transform: scale(1.05);
}
</style>
