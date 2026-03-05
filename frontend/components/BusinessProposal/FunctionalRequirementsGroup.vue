<template>
  <section ref="sectionRef" class="fr-group h-full w-full bg-white flex items-start pt-16 overflow-y-auto">
    <div class="w-full px-6 md:px-12 lg:px-24 pb-16">
      <div class="max-w-5xl mx-auto">
        <!-- Sub-section number + title -->
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span class="text-green-light font-light tracking-[0.25em] text-xs md:text-sm">
            {{ subIndex }}
          </span>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center"
                 :class="groupBgColor">
              <span class="text-2xl">{{ group.icon || '🧩' }}</span>
            </div>
            <h2 class="text-esmerald font-light leading-tight text-3xl md:text-5xl">
              {{ group.title }}
            </h2>
          </div>
        </div>

        <!-- Description -->
        <div data-animate="slide-in-left" class="mb-10">
          <p class="text-esmerald/80 font-light leading-relaxed text-lg md:text-xl max-w-3xl">
            {{ group.description }}
          </p>
        </div>

        <!-- Items grid -->
        <div v-if="group.items && group.items.length" data-animate="fade-up-stagger"
             class="requirements-grid grid md:grid-cols-2 gap-4">
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
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  group: {
    type: Object,
    default: () => ({
      id: '',
      icon: '🧩',
      title: '',
      description: '',
      items: [],
    })
  },
  subIndex: {
    type: String,
    default: '7.1',
  },
});

const groupBgColor = computed(() => {
  const id = props.group?.id;
  if (id === 'views') return 'bg-blue-100';
  if (id === 'components') return 'bg-purple-100';
  if (id === 'features') return 'bg-green-100';
  if (id === 'integrations_api') return 'bg-indigo-100';
  if (id === 'admin_module') return 'bg-amber-100';
  return 'bg-emerald-100';
});
</script>

<style scoped>
.requirement-card {
  transition: all 0.3s ease;
}

.requirement-card:hover {
  transform: translateX(4px);
}
</style>
