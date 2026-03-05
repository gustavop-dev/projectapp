<template>
  <div class="print-layout bg-white">
    <!-- Loading -->
    <div v-if="isLoading" class="min-h-screen flex items-center justify-center">
      <p class="text-gray-400 text-lg">Cargando propuesta…</p>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <h1 class="text-4xl font-light text-gray-400 mb-4">
          {{ loadError === 'expired' ? '⏰' : '404' }}
        </h1>
        <p class="text-gray-500">
          {{ loadError === 'expired' ? 'Esta propuesta ha expirado.' : 'Propuesta no encontrada.' }}
        </p>
      </div>
    </div>

    <!-- Print-ready content -->
    <div v-else-if="proposal" class="print-sections">
      <div
        v-for="(panel, idx) in displayPanels"
        :key="panel.id"
        class="print-panel"
        :data-section-type="panel.section_type"
      >
        <RawContentSection
          v-if="isPastePanel(panel)"
          :title="getPastePanelTitle(panel)"
          :index="getPastePanelIndex(panel)"
          :rawText="getPastePanelRawText(panel)"
        />
        <component
          v-else
          :is="sectionComponentMap[panel.section_type]"
          v-bind="getSectionProps(panel)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import {
  Greeting,
  ExecutiveSummary,
  ContextDiagnostic,
  ConversionStrategy,
  DesignUX,
  CreativeSupport,
  DevelopmentStages,
  FunctionalRequirements,
  FunctionalRequirementsGroup,
  Timeline,
  Investment,
  FinalNote,
  NextSteps,
} from '~/components/BusinessProposal';
import RawContentSection from '~/components/BusinessProposal/RawContentSection.vue';
import ProposalClosing from '~/components/BusinessProposal/ProposalClosing.vue';

definePageMeta({ layout: false });

const route = useRoute();
const proposalStore = useProposalStore();

const sectionComponentMap = {
  greeting: Greeting,
  executive_summary: ExecutiveSummary,
  context_diagnostic: ContextDiagnostic,
  conversion_strategy: ConversionStrategy,
  design_ux: DesignUX,
  creative_support: CreativeSupport,
  development_stages: DevelopmentStages,
  functional_requirements: FunctionalRequirements,
  functional_requirements_group: FunctionalRequirementsGroup,
  timeline: Timeline,
  investment: Investment,
  final_note: FinalNote,
  next_steps: NextSteps,
  proposal_closing: ProposalClosing,
};

const isLoading = ref(true);
const loadError = ref(null);

const proposal = computed(() => proposalStore.currentProposal);
const enabledSections = computed(() => proposalStore.enabledSections);

// Reuse the same displayPanels logic from [uuid].vue
const displayPanels = computed(() => {
  const panels = [];
  for (const section of enabledSections.value) {
    if (section.section_type === 'functional_requirements') {
      panels.push(section);
      const content = section.content_json || {};
      let groups = content.groups || [];
      if (!groups.length) {
        const legacyGroups = proposal.value?.requirement_groups || [];
        groups = legacyGroups.map((g) => ({
          id: g.group_id,
          icon: g.title?.trim().split(' ')[0] || '🧩',
          title: g.title?.trim().split(' ').slice(1).join(' ') || g.title,
          description: g.description,
          items: (g.items || []).map((item) => ({
            icon: item.icon, name: item.name, description: item.description,
          })),
        }));
      }
      const additional = content.additionalModules || [];
      const allGroups = [...groups, ...additional].filter(g => g && (g.title || g.items?.length));
      const parentIndex = content.index || '7';
      allGroups.forEach((group, gIdx) => {
        panels.push({
          id: `${section.id}_group_${gIdx}`,
          section_type: 'functional_requirements_group',
          title: `${group.icon || '🧩'} ${group.title}`,
          _group: group,
          _subIndex: `${parentIndex}.${gIdx + 1}`,
        });
      });
    } else {
      panels.push(section);
    }
  }

  const finalNote = enabledSections.value.find(s => s.section_type === 'final_note');
  const fnContent = finalNote?.content_json || {};
  panels.push({
    id: 'proposal_closing',
    section_type: 'proposal_closing',
    title: '🤝 Cierre',
    _validityMessage: fnContent.validityMessage || '',
    _thankYouMessage: fnContent.thankYouMessage || '',
  });

  return panels;
});

// --- Section props (same logic as [uuid].vue) ---
function getSectionProps(section) {
  const content = section.content_json || {};

  if (section.section_type === 'proposal_closing') {
    return {
      proposal: proposal.value,
      validityMessage: section._validityMessage || '',
      thankYouMessage: section._thankYouMessage || '',
    };
  }

  if (section.section_type === 'greeting') {
    return {
      clientName: content.clientName || proposal.value?.client_name || '',
      inspirationalQuote: content.inspirationalQuote,
    };
  }

  if ([
    'executive_summary', 'context_diagnostic', 'conversion_strategy',
    'design_ux', 'creative_support',
  ].includes(section.section_type)) {
    return { content };
  }

  if (section.section_type === 'functional_requirements_group') {
    return {
      group: section._group,
      subIndex: section._subIndex,
    };
  }

  if (section.section_type === 'functional_requirements') {
    let groups = content.groups || [];
    if (!groups.length) {
      const legacyGroups = proposal.value?.requirement_groups || [];
      groups = legacyGroups.map((g) => ({
        id: g.group_id,
        icon: g.title?.trim().split(' ')[0] || '🧩',
        title: g.title?.trim().split(' ').slice(1).join(' ') || g.title,
        description: g.description,
        items: (g.items || []).map((item) => ({
          icon: item.icon,
          name: item.name,
          description: item.description,
        })),
      }));
    }
    return {
      data: {
        ...content,
        groups,
        additionalModules: content.additionalModules || [],
      },
    };
  }

  return content;
}

function isPastePanel(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?._editMode === 'paste' && panel._group?.rawText;
  }
  return panel.content_json?._editMode === 'paste' && panel.content_json?.rawText;
}

function getPastePanelTitle(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?.title || panel.title;
  }
  return panel.content_json?.title || panel.title;
}

function getPastePanelIndex(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._subIndex || '';
  }
  return panel.content_json?.index || '';
}

function getPastePanelRawText(panel) {
  if (panel.section_type === 'functional_requirements_group') {
    return panel._group?.rawText || '';
  }
  return panel.content_json?.rawText || '';
}

// --- Fetch + auto-print ---
onMounted(async () => {
  const uuid = route.params.uuid;
  const result = await proposalStore.fetchPublicProposal(uuid);
  isLoading.value = false;

  if (!result.success) {
    loadError.value = result.error;
    return;
  }

  // Wait for DOM to render, then trigger print dialog
  await nextTick();
  await new Promise((r) => setTimeout(r, 600));
  window.print();
});
</script>

<style>
/* ===== Print-layout global overrides ===== */

/* Kill all CSS animations so elements render in their final state */
.print-layout *,
.print-layout *::before,
.print-layout *::after {
  animation-duration: 0s !important;
  animation-delay: 0s !important;
  transition-duration: 0s !important;
}

/* Force data-animate elements visible (GSAP won't run without horizontalTweenRef) */
.print-layout [data-animate] {
  opacity: 1 !important;
  transform: none !important;
}

/* Override component scoped opacity:0 (e.g. Greeting titles, Timeline items) */
.print-layout .main-title,
.print-layout .subtitle,
.print-layout .timeline-item {
  opacity: 1 !important;
  transform: none !important;
}
</style>

<style scoped>
.print-layout {
  width: 100%;
  min-height: 100vh;
}

.print-sections {
  width: 100%;
}

.print-panel {
  width: 100%;
  min-height: 100vh;
  overflow: visible;
  position: relative;
}

/* Hide interactive elements that don't belong in PDF */
.print-panel :deep(button),
.print-panel :deep([role="button"]) {
  display: none !important;
}

/* ===== Print media rules ===== */
@media print {
  @page {
    size: A4 landscape;
    margin: 10mm;
  }

  html, body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .print-layout {
    width: 100%;
  }

  .print-panel {
    page-break-after: always;
    page-break-inside: avoid;
    min-height: auto;
    height: auto;
    overflow: visible;
  }

  .print-panel:last-child {
    page-break-after: auto;
  }

  /* Preserve background colors in print */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}

/* ===== Screen preview styles (before print dialog opens) ===== */
@media screen {
  .print-panel {
    border-bottom: 1px dashed #e5e7eb;
  }

  .print-panel:last-child {
    border-bottom: none;
  }
}
</style>
