<template>
  <div class="max-w-4xl">
    <PromptSubTabsPanel v-model="subTab" dark-track>
      <template #commercial>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Este prompt se usa con IA (ChatGPT, Claude) para generar el JSON comercial del
          diagnóstico (propósito, entrega, costo, cronograma, alcance) a partir de la
          plantilla de 8 secciones.
        </p>
        <PromptEditor
          :state="commercialPrompt"
          download-filename="prompt-diagnostic-commercial.md"
        />
      </template>

      <template #technical>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Prompt para generar solo el objeto <code class="text-xs bg-gray-100 dark:bg-gray-800 px-1 rounded">categories</code>
          (14 categorías con hallazgos, fortalezas y recomendaciones) a partir del
          análisis del repositorio.
        </p>
        <PromptEditor
          :state="technicalPrompt"
          download-filename="prompt-diagnostic-technical.md"
        />
      </template>
    </PromptSubTabsPanel>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PromptSubTabsPanel from '~/components/panel/PromptSubTabsPanel.vue';
import PromptEditor from './PromptEditor.vue';
import {
  useDiagnosticCommercialPrompt,
  useDiagnosticTechnicalPrompt,
} from '~/composables/useDiagnosticPrompt';

const subTab = ref('commercial');
const commercialPrompt = useDiagnosticCommercialPrompt();
const technicalPrompt = useDiagnosticTechnicalPrompt();

onMounted(() => {
  commercialPrompt.loadSaved();
  technicalPrompt.loadSaved();
});
</script>
