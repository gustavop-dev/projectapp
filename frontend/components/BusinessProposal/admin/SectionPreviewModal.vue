<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      @click.self="$emit('close')"
    >
      <!-- Close button -->
      <button
        type="button"
        class="absolute top-4 right-4 z-[10000] w-10 h-10 flex items-center justify-center
               rounded-full bg-white/90 text-gray-600 hover:bg-white hover:text-gray-900
               shadow-lg transition-colors"
        @click="$emit('close')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- Preview panel -->
      <div class="preview-panel w-[95vw] h-[90vh] rounded-2xl overflow-hidden shadow-2xl bg-white">
        <div class="w-full h-full overflow-y-auto">
          <RawContentSection
            v-if="isPaste"
            :title="pastePanelTitle"
            :index="pastePanelIndex"
            :rawText="pastePanelRawText"
          />
          <component
            v-else-if="resolvedComponent"
            :is="resolvedComponent"
            v-bind="resolvedProps"
          />
          <div v-else class="flex items-center justify-center h-full text-gray-400 text-sm">
            No hay vista previa disponible para este tipo de sección.
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import {
  Greeting,
  ExecutiveSummary,
  ContextDiagnostic,
  ConversionStrategy,
  DesignUX,
  CreativeSupport,
  DevelopmentStages,
  FunctionalRequirements,
  Timeline,
  Investment,
  FinalNote,
  NextSteps,
} from '~/components/BusinessProposal';
import RawContentSection from '~/components/BusinessProposal/RawContentSection.vue';

const sectionComponentMap = {
  greeting: Greeting,
  executive_summary: ExecutiveSummary,
  context_diagnostic: ContextDiagnostic,
  conversion_strategy: ConversionStrategy,
  design_ux: DesignUX,
  creative_support: CreativeSupport,
  development_stages: DevelopmentStages,
  functional_requirements: FunctionalRequirements,
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
};

const props = defineProps({
  visible: { type: Boolean, default: false },
  section: { type: Object, default: () => ({}) },
  proposalData: { type: Object, default: () => ({}) },
});

defineEmits(['close']);

const isPaste = computed(() => {
  const cj = props.section?.content_json;
  return cj?._editMode === 'paste' && cj?.rawText;
});

const pastePanelTitle = computed(() => props.section?.content_json?.title || props.section?.title || '');
const pastePanelIndex = computed(() => props.section?.content_json?.index || '');
const pastePanelRawText = computed(() => props.section?.content_json?.rawText || '');

const resolvedComponent = computed(() => {
  return sectionComponentMap[props.section?.section_type] || null;
});

const resolvedProps = computed(() => {
  const section = props.section || {};
  const content = section.content_json || {};
  const sType = section.section_type;

  if (sType === 'greeting') {
    return {
      clientName: content.clientName || props.proposalData?.client_name || '',
      inspirationalQuote: content.inspirationalQuote,
    };
  }

  if ([
    'executive_summary', 'context_diagnostic', 'conversion_strategy',
    'design_ux', 'creative_support',
  ].includes(sType)) {
    return { content };
  }

  if (sType === 'functional_requirements') {
    const groups = content.groups || [];
    return {
      data: {
        ...content,
        groups,
        additionalModules: content.additionalModules || [],
      },
    };
  }

  // development_stages, timeline, investment, final_note, next_steps
  return content;
});
</script>

<style scoped>
.preview-panel {
  animation: modalIn 0.25s ease-out;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
