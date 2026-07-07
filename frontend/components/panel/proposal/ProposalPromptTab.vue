<template>
  <PromptSubTabsPanel v-model="promptSubTab">
    <template #commercial>
    <p class="text-sm text-text-muted mb-6">
      Este prompt se usa con IA (ChatGPT, Claude, etc.) para generar propuestas comerciales personalizadas a partir del JSON plantilla.
    </p>

    <!-- Action bar -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <template v-if="!promptIsEditing">
        <BaseButton variant="secondary" size="md" @click="startEditPrompt">
          <PencilIcon class="w-4 h-4" />
          Editar
        </BaseButton>
        <BaseButton variant="secondary" size="md" @click="handleCopyPrompt">
          <DocumentDuplicateIcon class="w-4 h-4" />
          {{ promptCopied ? '¡Copiado!' : 'Copiar' }}
        </BaseButton>
        <BaseButton variant="secondary" size="md" @click="promptDownload">
          <ArrowDownTrayIcon class="w-4 h-4" />
          Descargar .md
        </BaseButton>
        <BaseButton
          v-if="promptText !== promptDefault"
          variant="secondary"
          size="md"
          class="!text-danger-strong"
          @click="handleResetPrompt"
        >
          Restaurar original
        </BaseButton>
      </template>
      <template v-else>
        <BaseButton variant="primary" size="md" @click="saveEditPrompt">
          Guardar cambios
        </BaseButton>
        <BaseButton variant="ghost" size="md" @click="cancelEditPrompt">
          Cancelar
        </BaseButton>
      </template>
    </div>

    <div v-if="promptIsEditing" class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
      <textarea
        v-model="promptEditBuffer"
        rows="30"
        class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-text-default bg-transparent border-0 outline-none resize-y focus:ring-0"
      />
    </div>

    <div v-else class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
      <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
        <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ promptText }}</pre>
      </div>
    </div>

    <p v-if="promptText !== promptDefault" class="text-xs text-warning-strong mt-3">
      Este prompt ha sido personalizado. Usa "Restaurar original" para volver al valor por defecto.
    </p>
    </template>

    <template #technical>
    <p class="text-sm text-text-muted mb-6">
      Prompt para generar solo la clave <code class="text-xs bg-surface-raised px-1 rounded">technicalDocument</code> del JSON (arquitectura, módulos del producto, requerimientos, integraciones, etc.). Sin narrativa comercial ni precios.
    </p>
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <template v-if="!technicalPromptIsEditing">
        <BaseButton variant="secondary" size="md" @click="startEditTechnicalPrompt">
          <PencilIcon class="w-4 h-4" />
          Editar
        </BaseButton>
        <BaseButton variant="secondary" size="md" @click="handleCopyTechnicalPrompt">
          <DocumentDuplicateIcon class="w-4 h-4" />
          {{ technicalPromptCopied ? '¡Copiado!' : 'Copiar' }}
        </BaseButton>
        <BaseButton variant="secondary" size="md" @click="technicalPromptDownload">
          <ArrowDownTrayIcon class="w-4 h-4" />
          Descargar .md
        </BaseButton>
        <BaseButton
          v-if="technicalPromptText !== technicalPromptDefault"
          variant="secondary"
          size="md"
          class="!text-danger-strong"
          @click="handleResetTechnicalPrompt"
        >
          Restaurar original
        </BaseButton>
      </template>
      <template v-else>
        <BaseButton variant="primary" size="md" @click="saveEditTechnicalPrompt">
          Guardar cambios
        </BaseButton>
        <BaseButton variant="ghost" size="md" @click="cancelEditTechnicalPrompt">
          Cancelar
        </BaseButton>
      </template>
    </div>
    <div v-if="technicalPromptIsEditing" class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
      <textarea
        v-model="technicalPromptEditBuffer"
        rows="28"
        class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-text-default bg-transparent border-0 outline-none resize-y focus:ring-0"
      />
    </div>
    <div v-else class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
      <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
        <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ technicalPromptText }}</pre>
      </div>
    </div>
    <p v-if="technicalPromptText !== technicalPromptDefault" class="text-xs text-warning-strong mt-3">
      Prompt técnico personalizado. «Restaurar original» vuelve al texto por defecto.
    </p>
    </template>
  </PromptSubTabsPanel>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { PencilIcon, DocumentDuplicateIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline';
import PromptSubTabsPanel from '~/components/panel/PromptSubTabsPanel.vue';
import { useSellerPrompt } from '~/composables/useSellerPrompt';
import { useTechnicalPrompt } from '~/composables/useTechnicalPrompt';
import { usePanelNotify } from '~/composables/usePanelNotify';

defineProps({
  proposal: {
    type: Object,
    default: null,
  },
});

const notify = usePanelNotify();

const {
  promptText,
  isEditing: promptIsEditing,
  DEFAULT_PROMPT: promptDefault,
  loadSavedPrompt,
  savePrompt: promptSave,
  resetPrompt: promptReset,
  copyPrompt: promptCopy,
  downloadPrompt: promptDownload,
} = useSellerPrompt();

const promptEditBuffer = ref('');
const promptCopied = ref(false);

function startEditPrompt() {
  promptEditBuffer.value = promptText.value;
  promptIsEditing.value = true;
}
function cancelEditPrompt() {
  promptIsEditing.value = false;
}
function saveEditPrompt() {
  promptSave(promptEditBuffer.value);
  promptIsEditing.value = false;
  notify.success({ title: 'Prompt comercial guardado.' });
}
async function handleCopyPrompt() {
  await promptCopy();
  promptCopied.value = true;
  setTimeout(() => { promptCopied.value = false; }, 2000);
}
function handleResetPrompt() {
  promptReset();
}

const promptSubTab = ref('commercial');

const {
  promptText: technicalPromptText,
  isEditing: technicalPromptIsEditing,
  DEFAULT_PROMPT: technicalPromptDefault,
  loadSavedPrompt: loadTechnicalPrompt,
  savePrompt: technicalPromptSave,
  resetPrompt: technicalPromptReset,
  copyPrompt: technicalPromptCopy,
  downloadPrompt: technicalPromptDownload,
} = useTechnicalPrompt();

const technicalPromptEditBuffer = ref('');
const technicalPromptCopied = ref(false);

function startEditTechnicalPrompt() {
  technicalPromptEditBuffer.value = technicalPromptText.value;
  technicalPromptIsEditing.value = true;
}
function cancelEditTechnicalPrompt() {
  technicalPromptIsEditing.value = false;
}
function saveEditTechnicalPrompt() {
  technicalPromptSave(technicalPromptEditBuffer.value);
  technicalPromptIsEditing.value = false;
  notify.success({ title: 'Prompt técnico guardado.' });
}
async function handleCopyTechnicalPrompt() {
  await technicalPromptCopy();
  technicalPromptCopied.value = true;
  setTimeout(() => { technicalPromptCopied.value = false; }, 2000);
}
function handleResetTechnicalPrompt() {
  technicalPromptReset();
  technicalPromptIsEditing.value = false;
}

// The component only mounts once the proposal has loaded (the page renders
// tabs under a proposal v-else-if), matching the page's previous
// fetchProposal → loadSavedPrompt/loadTechnicalPrompt ordering.
onMounted(() => {
  loadSavedPrompt();
  loadTechnicalPrompt();
});
</script>
