<template>
  <section ref="sectionRef" class="functional-requirements min-h-screen w-full bg-white flex items-center">
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

        <!-- Overview: clickable group cards that open detail modal -->
        <div v-if="allGroups.length" data-animate="fade-up-stagger" class="overview-grid grid md:grid-cols-2 gap-6">
          <div v-for="group in allGroups" :key="group.id || group.title"
               class="overview-card bg-esmerald/5 p-6 rounded-2xl border border-esmerald/10 cursor-pointer"
               @click="openModal(group)">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-esmerald-light/60">
                <span class="text-xl">{{ group.icon || '🧩' }}</span>
              </div>
              <h3 class="text-lg font-medium text-esmerald">{{ group.title }}</h3>
              <span v-if="group.items?.length" class="ml-auto text-xs font-medium text-esmerald/60 bg-esmerald/10 px-2 py-0.5 rounded-full">
                {{ group.items.length }}
              </span>
            </div>
            <p class="text-sm text-esmerald/70 font-light leading-relaxed mb-3">{{ group.description }}</p>
            <span class="text-xs font-medium text-green-light hover:text-esmerald transition-colors">
              Ver detalle →
            </span>
          </div>
        </div>
      </div>
    </div>

    <FunctionalRequirementsModal
      :visible="modalVisible"
      :group="selectedGroup"
      @close="modalVisible = false"
    />
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useSectionAnimations } from '~/composables/useSectionAnimations';
import FunctionalRequirementsModal from './FunctionalRequirementsModal.vue';

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

const modalVisible = ref(false);
const selectedGroup = ref({});

function openModal(group) {
  selectedGroup.value = group;
  modalVisible.value = true;
}
</script>

<style scoped>
.overview-card {
  transition: all 0.3s ease;
}

.overview-card:hover {
  border-color: #d1d5db;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}
</style>
